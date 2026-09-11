from langchain_classic.chains.hyde.prompts import web_search

from app.core.logger import node_log, step_log, logger
from app.lm.reranker_utils import get_reranker_model
from app.query_process.agent.state import QueryGraphState
from app.utils.task_utils import add_running_task, add_done_task



# 动态 TopK 硬上限：最多取前 N 条（<=10）
RERANK_MAX_TOPK: int = 10
# 最小 TopK：至少保留前 N 条（>=1，且 <= RERANK_MAX_TOPK）
RERANK_MIN_TOPK: int = 1
# 断崖阈值（相对）
RERANK_GAP_RATIO: float = 0.25
# 断崖阈值（绝对）
RERANK_GAP_ABS: float = 0.5
@step_log("step_1_merge_docs")
def step_1_merge_docs(state):
    #分别获取状态中的web_search_docs和rrf_chunks
    web_search_docs = state["web_search_docs"]
    rrf_chunks = state["rrf_chunks"]
    #创建存储最终合并数据的列表
    doc_items = []
    #变量rrf_chunks,将其中的数据转换为固定的格式
    for chunk in rrf_chunks:
        #获取chunk中存储的entity
        entity = chunk.get("entity") if isinstance(chunk,dict) else chunk
        #判断entity是否为字典
        if not isinstance(entity, dict):
            continue
        #获取content
        content = entity.get("content")
        # 判断content是否为空
        if not content:
            continue
        #分别获取chunk_id和title(item_name)
        chunk_id = entity.get("chunk_id") or entity.get("id")
        title = entity.get("item_name") or entity.get("title")
        #将数据转为固定格式存到doc_items中
        doc_items.append(
            {
                "text": content,
                "title": title,
                "doc_id": chunk_id,
                "chunk_id": chunk_id,
                "url":"",
                "source":"local"
            }
        )
    #遍历web_search_docs : title,snippet,url
    for doc in web_search_docs:
        # 分别获取网络搜索结果中的snippet摘要，title标题，url网址
        snippet = (doc.get("snippet") or doc.get("content")).strip()
        title = (doc.get("title") or "").strip()
        url = (doc.get("url") or "").strip()
        # 使用固定的格式存储数据
        doc_items.append(
            {
                "text": snippet,
                "title": title,
                "doc_id": "",
                "chunk_id": "",
                "url": url,
                "source":"web"
            }
        )

    return doc_items

@step_log("step_2_rerank_docs")
def step_2_rerank_docs(state, doc_items):
    # 获取状态中的rewritten_query或者original_query
    rewritten_query = state.get("rewritten_query") or state.get("original_query")
    # 判断rewritten_query或doc_items是否为空
    if not rewritten_query or not doc_items:
        return []
    #获取需要融合排序的文本
    texts = [item["text"] for item in doc_items]
    try:
        #获取reranker模型对象
        reranker_model = get_reranker_model()
        #将要进行重排的数据转换为[[query,text],....]
        sentence_pairs = [[rewritten_query,text] for text in texts]
        #对数据进行重排序，返回的是每条数据分分数组成的列表
        scores = reranker_model.compute_score(sentence_pairs)
        #创建存储最后结果的列表
        scored_docs = []
        #将scores,texts,doc_items进行压缩且遍历(reranker只打分不排序)
        for score,text,item in zip(scores, texts,doc_items):
            scored_docs.append({
                "text":text,
                "score":float(score),
                "doc_id":item["doc_id"],
                "chunk_id":item["chunk_id"],
                "url":item["url"],
                "title":item["title"],
                "source":item["source"],
            }
        )
        #将最终结果进行排序
        scored_docs.sort(key = lambda doc:doc["score"],reverse=True)
        return scored_docs
    except Exception as e:
        logger.error(f"使用reranker模型重排序失败，{e}")
        for item in doc_items:
            item["score"] = 0.0
        return doc_items


@node_log("node_rerank")
def node_rerank(state: QueryGraphState):
    # 记录当前任务的状态为进行中
    add_running_task(state["session_id"], "node_rerank", state["is_stream"])
    #阶段一：合并文档,[{text,title,doc_id,url,source}]
        #合并文档：把rrf融合和hyde按相同的格式转换存到一个列表，
        # 然后调用重排模型拿着列表中的text也就是内容，和query用户的问题进行比较，留下最相似的
    doc_items = step_1_merge_docs(state)
    #阶段二：对文档进行重排序，[{text,title,doc_id,chunk_id,url,source}]
    scored_docs = step_2_rerank_docs(state, doc_items)
    # 记录当前任务的状态为已完成
    add_done_task(state["session_id"], "node_rerank", state["is_stream"])
    return state