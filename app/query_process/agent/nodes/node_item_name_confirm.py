import sys
import os
import json
import logging
from typing import List, Dict, Any, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from mpmath import limit

from app.conf.milvus_config import milvus_config
from app.core.load_prompt import load_prompt
from app.query_process.agent.state import QueryGraphState
from app.utils.task_utils import add_running_task, add_done_task
from app.clients.mongo_history_utils import get_recent_messages, save_chat_message, update_message_item_names
from app.lm.lm_utils import get_llm_client
from app.lm.embedding_utils import generate_embeddings
from app.clients.milvus_utils import get_milvus_client, create_hybrid_search_requests, hybrid_search
from dotenv import load_dotenv,find_dotenv
from app.core.logger import logger, step_log, node_log


@step_log("step_3_extract_info")
def step_3_extract_info(original_query, history_list):
    #遍历history_list,将每个历史对话拼接，role(user/ai):text
    history_text = ""
    for history in history_list:
        history_text += f"{history['role']}:{history['text']}\n"
    #读取rewritten_query_and_itemnames.prompt文件获取提示词
    prompt = load_prompt("rewritten_query_and_itemnames",history_text=history_text,query=original_query)
    #构造调用大模型提示词
    messages = [{
        SystemMessage(content="你是一个专业的客服助手，擅长理解用户意图和提取关键信息。"),
        HumanMessage(content=prompt)
    }]
    try:
        #获取大模型对象
        llm = get_llm_client(json_mode=True)#返回格式为json格式
        #调用大模型
        response = llm.invoke(messages)
        # 获取大模型输出内容
        result = response.content
        #判断result是否是json代码块，'''json{key:value}'''
        if result.startswith("```json"):
            result = result.replace("```json", "").replace("```", "")
        #将字符串格式的json转换为python对象
        extract_result = json.loads(result)
        #判断结果中是否包含"item_names"
        if "item_names" not in extract_result:
            extract_result["item_names"] = []
        # 判断结果中是否包含"rewritten_query"
        if "rewritten_query" not in extract_result:
            extract_result["rewritten_query"] = original_query
        return extract_result
    except Exception as e:
        logger.error(f"提取产品主体并重写用户问题时出现了异常：",{e})
        return {"item_names": [], "rewritten_query": original_query}

@step_log("step_4_vectorize_and_query")
def step_4_vectorize_and_query(item_names):
    """
         results=[
             {
                 "extracted_name":从用户的问题中提取的产品主体,
                 "matches":[
                     {
                         "item_name":从向量数据库中检索到的产品主体,
                         "score":分数
                     },
                     ...
                 ]
             },
             ...
         ]
    """
    #创建存储最终结果的列表
    results = []
    #获取milvus_client的客户端
    try:
        milvus_client = get_milvus_client()
        #判断milvus_client是否为空
        if not milvus_client:
            logger.erro("获取milvus客户端失败")
            return results
        #获取要检索的集合
        collection_name = milvus_config.item_name_collection
        #判断collection_name是否为空
        if not collection_name:
            logger.error("获取产品主题名称失败")
            return results
        #获取item_names所对应的向量
        embeddings = generate_embeddings(item_names)
        #分别获取每个item_name所对应的稠密向量和稀疏向量
        for i in range(len(item_names)):
            dense_vector = embeddings["dense"][i]
            sparse_vector = embeddings["sparse"][i]
            #设置稠密向量和稀疏向量的检索方式
            reqs = create_hybrid_search_requests(dense_vector=dense_vector, sparse_vector=sparse_vector,limit=5)
            # 进行混合检索
            """
                混合检索的结果的结构：
                [
                    [
                        {
                            'pk': 468868229533272140, 
                            'distance': 0.9151462912559509, 
                            'entity': {'item_name': 'HAK 180 烫金机'}
                        }
                    ]
                ]
            """
            #进行混合检索
            hybrid_search_results = hybrid_search(
                client=milvus_client,
                collection_name=collection_name,
                reqs=reqs,
                ranker_weights=(0.8,0.2),
                norm_score=True,#归1化 把分数控制在0~1之间
                output_fields=["item_name"],
            )
            #创建存储检索结果的列表
            matches = []
            #判断检索的结果是否为空
            if hybrid_search_results and len(hybrid_search_results) > 0:
                for result in hybrid_search_results:
                    matches.append({
                        "item_name" : result["entity"]["item_name"],
                        "score": result['distance']
                    })
            #存储最终结果
            results.append({
                "extracted_name":item_names[i],
                "matches": matches
            })
        return results
    except Exception as e:
        logger.error(f"混合检索item_name失败：{e}")



@step_log("step_5_align_item_names")
def step_5_align_item_names(query_results):
    #创建存储已确认的item_name的列表
    confirmed_item_names : List[str] = []
    #创建存储待确认的item_name的列表
    options: List[str] = []
    #遍历query_results
    for result in query_results:
        #获取用户问题中的extract_name
        extracted_name = result["extracted_name"]
        #获取extract_name所检索出来的数据
        matches = result["matches"]
        #将检索出来的数据根据分数进行倒序排序
        # #lambda match :match["score"] 第一个match相当于传的参数，match["score"]为return的，match是字典
        matches.sort(key= lambda match :match["score"],reverse=True)
        #判断matches是否为空
        if not matches:
            logger.warning(f"{extracted_name}没有检测书任何数据")
            continue
        #分别获取最高分数(>=0.85)和中间分数（>=0.6 and < 0.85）的数据
        high = [match for match in matches if match["score"]>=0.85]
        middle = [match for match in matches if match["score"]>=0.6]
        #判断high中数据的数量，若只有一条，则直接作为已确认的item_name
        if len(high)==1:
            confirmed_item_names.append(high[0]["item_name"])#match是个列表
        #判断high中数据的数量，若有多条，优先检索到item_name与extract_name一致的数据
        #创建存储已确认item_name的变量
        picked = None
        if len(high)>1:
            for item in high:
                if item["item_name"] == extracted_name:
                    picked = item
                    continue
                #判断picked为None，若为None，表示0.85以上没有数据与item_name和extract_name一致
                # 直接将0.85以上的数据中分数最高的作为已确认的item_name
                if not picked:
                    picked = high[0]
                #保存已确认的item_name
                confirmed_item_names.append(picked["item_name"])
                continue
        #表示没有已确认的item_name,即检索数据的score在[0.6,0.85]之间
        #将0.6-0.85之间的数据中前3个作为待确认的item_name
        if len(middle)>0:
            for item in middle[:3]:
                options.append(item["item_name"])
    return {
        "confirmed_item_names": list(set(confirmed_item_names)),
        "options": list(set(options))
    }

@step_log("step_6_check_confirmation")
def step_6_check_confirmation(state,align_result, session_id, history_list, rewritten_query):
    #分别获取已确认和待确认的item_name的列表
    confirmed = align_result.get("confirmed_item_names",[])
    options = align_result.get("options",[])
    #分支1：已有确认的item_name
    if confirmed:
        #更新历史记录中的item_name
        #先获取要修改的id
        ids = []
        #遍历历史记录
        for history in history_list:
            #若历史记录的item_names为空，进行更新，就需要记录历史纪录的id
            if not history.get("item_names"):
                ids.append(history["_id"])
        #判断ids是否为空，若不为空则修改历史记录的item_names
        if ids: #ids接收的是列表
            update_message_item_names(ids,confirmed)
        #更新状态
        state["item_names"] = confirmed
        state["rewritten_query"] = rewritten_query
        #判断state中answer是否有值，若有则删除
        if state.get("answer"):
            del state["answer"]
        return state
    #分支2：有待确认的item_name
    if options:
        #获取拼接待确认的item_names
        options_str = "、".join(options)
        #拼接待确认信息
        answer = f"您是想问以下哪个产品：{options_str}?请明确一下型号。"
        #更新状态
        state["item_names"] = []
        state["answer"] = answer
        return state
    #分支3：既没有确认也没有待确认
    #拼接待确认信息
    answer = "抱歉，未找到相关产品，请提供准确型号以便我为您查询。"
    #更新状态
    state["item_names"] = []
    state["answer"] = answer
    return state

@step_log("step_7_write_history")
def step_7_write_history(state, history_list, session_id, rewritten_query, message_id):
    #判断状态answer，若有值则保存历史纪录，若没有值更新历史记录
    if state.get("answer"):
        save_chat_message(session_id,"assistant",state["answer"],"",[])
    #更新历史记录
    save_chat_message(
        session_id = session_id,#会话id，关联所属会话
        role="user",#消息角色：用户
        text = state["original_query"],#消息内容：用户原始查询
        rewritten_query=rewritten_query,#补充step3改写后的完整问题
        item_names=state.get("item_names",[]),#补充关联的商品名列表
        message_id=message_id #消息ID，指定更新已存在的用户消息(并非新增)
    )
    return state


@node_log("node_item_name_confirm")
def node_item_name_confirm(state: QueryGraphState):
    # 记录当前任务的状态为进行中
    add_running_task(state["session_id"], "node_item_name_confirm", state["is_stream"])
    #获取状态中：session_id,original_query,is_stream
    session_id = state["session_id"]
    original_query = state["original_query"]
    is_stream = state["is_stream"]
    #步骤1：获取历史记录
    history_list = get_recent_messages(session_id)
    #步骤2：将当前用户的问题保存到Mongo,返回的message_id是添加数据的唯一标识
    message_id = save_chat_message(session_id, "user", state["original_query"], "", [])
    #步骤3：从用户的问题中提取item_names并重写用户问题
    extract_result = step_3_extract_info(original_query, history_list)
    #分别获取提取的item_names和重写之后的问题rewritten_query
    item_names = extract_result.get("item_names")
    rewritten_query = extract_result.get("rewritten_query")
    #更新状态中的rewritten_query
    state["rewritten_query"] = rewritten_query
    #创建存储对齐之后结果的字典
    align_result = {}
    #如果有提取到商品名，进行搜索和对齐
    if len(item_names) > 0:
        #步骤4：通过item_names在向量数据库中进行检索
        query_results = step_4_vectorize_and_query(item_names)
        #步骤5：获取对齐的结果
        align_result = step_5_align_item_names(query_results)
    else:
        logger.info("Node:未提取到商品名，跳过向量检索")
    #步骤6：检查确认状态
    state =step_6_check_confirmation(align_result,session_id,history_list,rewritten_query)
    #步骤7：写入最终历史(第六步是修改之前的历史记录第七步是更新当前的用户的问题记录)
    final_state = step_7_write_history(state,history_list,session_id,rewritten_query,message_id)
    state["history"] = history_list
    # 记录当前任务的状态为已完成
    add_done_task(state["session_id"], "node_item_name_confirm", state["is_stream"])
    return final_state

