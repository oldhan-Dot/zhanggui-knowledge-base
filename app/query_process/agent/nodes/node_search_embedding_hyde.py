
from app.clients.milvus_utils import hybrid_search, get_milvus_client, create_hybrid_search_requests
from app.conf.milvus_config import milvus_config
from app.core.load_prompt import load_prompt
from app.core.logger import node_log, logger, step_log
from app.lm.embedding_utils import generate_embeddings
from app.lm.lm_utils import get_llm_client
from app.query_process.agent.state import QueryGraphState
from app.utils.task_utils import add_running_task, add_done_task

@step_log("step_1_create_hyde_doc")
def step_1_create_hyde_doc(rewritten_query):
    #加载假设性提示词
    prompt = load_prompt("hyde_prompt",rewritten_query = rewritten_query)
    #调用大模型
    llm = get_llm_client()
    response = llm.invoke(prompt)
    #获取大模型的返回结果 即假设性文档
    hyde_doc = response.content
    return hyde_doc

@step_log("step_2_search_embedding_hyde")
def step_2_search_embedding_hyde(
        rewritten_query:str,
        hyde_doc : str,
        item_names=None,
        req_limit : int = 10,#稠密向量与稀疏向量检索的数据量
        limit : int = 5,#混合检索的数据量
        rank_weights = (0.8,0.2),#调整默认的权重 偏向于稠密向量(0.8，0.2)
        nor_score :bool = True,#默认开启归一化
        output_fields = ["chunk_id","content","item_name"]
):
    #拼接rewritten_query和hyde_doc
    text = rewritten_query + " " + hyde_doc
    # 获取text所对应的稠密向量和稀疏向量
    embeddings = generate_embeddings([text])
    dense_vector = embeddings["dense_vector"][0]
    sparse_vector = embeddings["sparse_vector"][0]
    # 获取milvus客户端
    milvus_client = get_milvus_client()
    # 拼接item_name作为检索条件
    expr_data = ",".join(f"'{item_name}'"for item_name in item_names)
    expr = f"item_name in [{expr_data}]"
    #创建稠密向量和稀疏变量的检索方式
    reqs  = create_hybrid_search_requests(
        dense_vector = dense_vector,
        sparse_vector = sparse_vector,
        expr = expr,
        limit = req_limit,
    )
    #混合检索
    result = hybrid_search(
        client=milvus_client,
        collection_name=milvus_config.chunks_collection,
        reqs = reqs,
        ranker_weights=rank_weights,
        norm_score=nor_score,
        limit=limit,
        output_fields=output_fields,
    )
    return result



@node_log("node_search_embedding_hyde")
def node_search_embedding_hyde(state: QueryGraphState):
    # 记录当前任务的状态为进行中
    add_running_task(state["session_id"], "node_search_embedding_hyde", state["is_stream"])
    # 分别获取rewritten_query和item_names
    rewritten_query = state.get("rewritten_query")
    item_names = state.get("item_names")
    #如果rewritten_query为空，用origin_query兜底
    if not rewritten_query:
        rewritten_query = state.get("original_query")
    if not rewritten_query:
        logger.warning("假设性文档检索缺失用户的问题")
        return {"hyde_embedding_chunks":[]}
    if not item_names:
        logger.warning("假设性文档检索缺失item_names")
        return {"hyde_embedding_chunks":[]}
    #步骤1：通过rewritten_query获取假设性文档
    hyde_doc = ""
    try:
        hyde_doc = step_1_create_hyde_doc(rewritten_query)
    except Exception as e:
        logger.error(f"获取假设性文档失败",{e})
        return {"hyde_embedding_chunks":[]}
    #步骤2：将hyde_doc和rewritten_query转化为向量检索数据

    try:
        result = step_2_search_embedding_hyde(
                rewritten_query=rewritten_query,
                hyde_doc=hyde_doc,
                item_names=item_names,
                limit=5,)
        return {
            "hyde_embedding_chunks":result[0] if result else [],
            "hyde_doc":hyde_doc,
        }
    except Exception as e:
        logger.error("获取假设性文档检索结果失败，{e}")
        return {"hyde_embedding_chunks":[]}
    finally:
        # 记录当前任务的状态为已完成
        add_done_task(state["session_id"], "node_search_embedding_hyde", state["is_stream"])

    #注意#result:pk distance entity(chunk_id、content、item_name) item_name的作用时缩小检索范围在当前的这个item_name中去检索

