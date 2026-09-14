<div align="center">

# 掌柜智库 · 企业级 RAG 知识库系统

**基于 LangGraph 编排的双流水线 RAG 工程 —— 让产品手册"会说话"**

从 PDF / Markdown 到可检索向量：一条流水线完成解析、多模态理解、语义切片、向量化与入库

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-工作流编排-1C3C3C?style=flat-square&logo=langchain&logoColor=white)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Web%20服务-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/zh/)
[![Milvus](https://img.shields.io/badge/Milvus-向量数据库-149ECA?style=flat-square&logo=milvus&logoColor=white)](https://milvus.io/docs)
[![BGE-M3](https://img.shields.io/badge/Embedding-BGE--M3-FF6F00?style=flat-square&logo=huggingface&logoColor=white)](https://github.com/FlagOpen/FlagEmbedding)
[![uv](https://img.shields.io/badge/包管理-uv-DE5FE9?style=flat-square&logo=astral&logoColor=white)](https://docs.astral.sh/uv/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](./LICENSE)

</div>

---

## 目录

- [项目简介](#项目简介)
- [当前进度](#当前进度)
- [技术栈](#技术栈)
- [系统架构](#系统架构)
- [导入流水线：7 个节点](#导入流水线7-个节点)
- [双层索引设计](#双层索引设计)
- [检索流水线：7 个节点](#检索流水线7-个节点)
- [问答链路的关键设计](#问答链路的关键设计)
- [状态定义](#状态定义)
- [导入 Web 服务与前端对接](#导入-web-服务与前端对接)
- [问答 Web 服务与 SSE 流式](#问答-web-服务与-sse-流式)
- [快速开始](#快速开始)
- [目录结构](#目录结构)
- [关键设计决策](#关键设计决策)
- [踩坑记录](#踩坑记录)
- [后续计划](#后续计划)

---

## 项目简介

**掌柜智库** 是一个面向企业私有产品文档的 RAG（Retrieval-Augmented Generation，检索增强生成）知识库系统。

企业积累了大量产品手册（PDF / Markdown），传统方式靠人工检索、关键词搜索，效率低且看不懂图片内容。本项目把文档加工成**可语义检索的向量知识库**，并支持多模态（图片也能被检索到）。

系统由两条独立的 LangGraph 流水线组成：**导入流水线**负责把文档加工入库，**检索流水线**负责把用户提问变成带出处、可追问的答案。

### 核心价值

| 能力 | 说明 |
|------|------|
| **文档结构化** | PDF 经 MinerU 高精度解析为 Markdown，保留标题层级与图片 |
| **多模态理解** | 用视觉大模型（VLM）给图片生成中文语义描述 + 上传对象存储，图片从此"可被检索" |
| **语义切片** | 标题层级初切 + 递归二次切分，每个切片自带"页眉"，切碎了也不丢上下文 |
| **双层索引** | 商品级粗筛（`kb_item_names`）+ 切片级精搜（`kb_chunks`） |
| **混合检索** | 稠密向量（语义泛化）+ 稀疏向量（关键词精准），加权融合召回 |
| **多路召回 + RRF** | 向量检索 + HyDE + 联网搜索三路互补，按「名次」融合而非分数相加 |
| **交叉编码器精排** | `bge-reranker-large` 逐对重打分 + 动态 TopK（断崖检测） |
| **多轮对话** | 指代消解把「它」补全成具体商品，历史存在 MongoDB |
| **流式问答** | SSE 打字机效果，答案附出处与图片；一个 `session_id` 一条独立通道 |
| **异步导入** | FastAPI `BackgroundTasks` + 任务状态机，长任务不阻塞、进度实时可见 |

---

## 当前进度

| 模块 | 状态 | 说明 |
|------|------|------|
| **导入流水线（知识库构建）** | 已完成 | 7 个节点端到端跑通 |
| **导入 Web 服务 + 前端页面** | 已完成 | `/upload` `/status/{task_id}` `/import.html`（轮询进度） |
| **检索流水线（智能问答）** | 已完成 | 7 个节点：指代消解 → 三路召回 → RRF 融合 → 动态 TopK 重排序 → 生成 |
| **问答 Web 服务 + SSE 流式** | 已完成 | `/query` `/stream/{session_id}` `/chat.html`（打字机效果） |
| **双层索引** | 已完成 | 商品级粗筛 `kb_item_names` + 切片级精搜 `kb_chunks` |

---

## 技术栈

> 点击名称跳转官方文档 / 仓库

### 编排与框架

| 技术 | 用途 | 文档 |
|------|------|------|
| [LangGraph](https://langchain-ai.github.io/langgraph/) | 状态图编排，把节点串成流水线，支持条件边、流式执行 | [Docs](https://langchain-ai.github.io/langgraph/concepts/low_level/) · [GitHub](https://github.com/langchain-ai/langgraph) |
| [LangChain](https://python.langchain.com/docs/introduction/) | LLM 调用封装（`ChatOpenAI`）、消息类型、输出解析器 | [Docs](https://python.langchain.com/docs/introduction/) |
| [FastAPI](https://fastapi.tiangolo.com/zh/) | Web 服务：上传接口、状态查询、后台任务 | [Docs](https://fastapi.tiangolo.com/zh/) |
| [Uvicorn](https://www.uvicorn.org/) | ASGI 服务器，`--reload` 热重载 | [Docs](https://www.uvicorn.org/) |
| [Pydantic](https://docs.pydantic.dev/) | 配置数据类校验 | [Docs](https://docs.pydantic.dev/) |

### 存储与检索

| 技术 | 用途 | 文档 |
|------|------|------|
| [Milvus](https://milvus.io/docs) | 向量数据库，存稠密 + 稀疏双向量，混合检索 | [Docs](https://milvus.io/docs) · [PyMilvus](https://milvus.io/docs/install-pymilvus.md) |
| [Attu](https://github.com/zilliztech/attu) | Milvus 可视化管理界面（推荐装） | [GitHub](https://github.com/zilliztech/attu) |
| [MinIO](https://min.io/docs/minio/linux/index.html) | 对象存储，存放文档图片并生成公网 URL | [Docs](https://min.io/docs/minio/linux/index.html) · [Python SDK](https://min.io/docs/minio/linux/developers/python/minio-py.html) |
| [MongoDB](https://www.mongodb.com/docs/) | 会话历史存储 | [Docs](https://www.mongodb.com/docs/) |

### 模型与 AI

| 技术 | 用途 | 文档 |
|------|------|------|
| [BGE-M3](https://github.com/FlagOpen/FlagEmbedding) | 向量化模型，同时输出稠密 + 稀疏向量 | [GitHub](https://github.com/FlagOpen/FlagEmbedding) · [Model](https://huggingface.co/BAAI/bge-m3) |
| [BGE-Reranker-Large](https://huggingface.co/BAAI/bge-reranker-large) | 交叉编码器，对召回候选逐对精排 | [Model](https://huggingface.co/BAAI/bge-reranker-large) |
| [MinerU](https://github.com/opendatalab/MinerU) | PDF 高精度解析（云端 API） | [Docs](https://mineru.readthedocs.io/) |
| [阿里云百炼](https://bailian.console.aliyun.com/) | 大模型服务（Qwen 系列，OpenAI 兼容模式） | [兼容 API 文档](https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope) |
| [Qwen3-VL-Flash](https://help.aliyun.com/zh/model-studio/models) | 视觉大模型，生成图片中文描述 | [Docs](https://help.aliyun.com/zh/model-studio/models) |
| [MCP](https://modelcontextprotocol.io/) | 模型上下文协议，接入百炼联网搜索工具 | [Docs](https://modelcontextprotocol.io/) |

### 工程化

| 技术 | 用途 | 文档 |
|------|------|------|
| [uv](https://docs.astral.sh/uv/) | 极速 Python 包管理 + 虚拟环境 | [Docs](https://docs.astral.sh/uv/) |
| [loguru](https://loguru.readthedocs.io/) | 日志（含位置修正、节点/步骤耗时装饰器） | [Docs](https://loguru.readthedocs.io/) |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | `.env` 配置加载 | [PyPI](https://pypi.org/project/python-dotenv/) |

---

## 系统架构

```
┌──────────────────────────────────────────────────────────────┐
│                        浏览器 import.html                      │
│             选文件 → 上传 → 轮询进度条 → 查看结果               │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTP (CORS 已开启)
┌───────────────────────────▼──────────────────────────────────┐
│                    FastAPI 导入服务 (:8000)                    │
│   GET  /import.html      上传页面                             │
│   POST /upload           保存文件 + 生成 task_id              │
│   GET  /status/{task_id} 查询任务进度（前端轮询）              │
└───────────────────────────┬──────────────────────────────────┘
                            │ BackgroundTasks（响应后执行，不阻塞）
┌───────────────────────────▼──────────────────────────────────┐
│              LangGraph 导入流水线（kb_import_app）             │
│                                                               │
│  node_entry ──┬─(PDF)─→ node_pdf_to_md ──┐                    │
│               ├─(MD)─────────────────────┤                    │
│               └─(其它)─→ END             │                    │
│                                  node_md_img                  │
│                                       ↓                       │
│                              node_document_split              │
│                                       ↓                       │
│                          node_item_name_recognition           │
│                                       ↓                       │
│                             node_bge_embedding                │
│                                       ↓                       │
│                             node_import_milvus                │
│                                       ↓                      END                                       │
└───────────────────────────┬──────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
   ┌─────────┐        ┌──────────┐       ┌──────────┐
   │ Milvus  │        │  MinIO   │       │ 百炼 LLM │
   │ 向量库  │        │  图床    │       │ / VLM    │
   └─────────┘        └──────────┘       └──────────┘
```

> 上图是**导入侧**（建库）的架构。**问答侧**（检索 + 生成）是另一条独立的 LangGraph 流水线，详见 [检索流水线：7 个节点](#检索流水线7-个节点)。

---

## 导入流水线：7 个节点

> 源码位置：`app/import_process/agent/nodes/`

| # | 节点 | 作用 | 关键产出 |
|---|------|------|---------|
| 1 | `node_entry` | 入口分流：按文件后缀设置 `is_pdf_read_enabled` / `is_md_read_enabled`，提取 `file_title` | 路由标记 + 文件标题 |
| 2 | `node_pdf_to_md` | MinerU 云端解析 PDF → Markdown | `xxx.md` + `images/` 图片目录 |
| 3 | `node_md_img` | VLM 给图片生成中文描述 → 上传 MinIO → 替换 MD 中的图片路径与 alt | `xxx_new.md`（图片已是云端 URL） |
| 4 | `node_document_split` | 标题层级初切（跳过代码块）+ 递归二次切分（200 字 / 重叠 20） | `chunks[]` |
| 5 | `node_item_name_recognition` | LLM 读前 5 个切片识别商品名（失败用文件名兜底），广播到每个 chunk，向量化后写入 `kb_item_names` | `item_name` + 商品向量 |
| 6 | `node_bge_embedding` | 对 `商品：{item_name}\n{content}` 分批生成稠密 + 稀疏向量 | `dense_vector` / `sparse_vector` |
| 7 | `node_import_milvus` | 幂等入库（先删同名旧数据再插入） | `kb_chunks` 切片行 |

### 条件路由（node_entry 的三岔口）

```python
def condition_fun(state: ImportGraphState):
    if state["is_md_read_enabled"]:
        return "node_md_img"      # MD 直接处理图片
    elif state["is_pdf_read_enabled"]:
        return "node_pdf_to_md"   # PDF 先解析
    else:
        return END                # 不支持的格式，直接结束
```

---

## 双层索引设计

Milvus 里建两个 Collection，形成"先粗筛、再精搜"的两级检索：

```
┌─────────────────────────────────────────────────┐
│ kb_item_names（文档级 / 商品名片）                │
│ 每个文档 1 行                                     │
│   pk · file_title · item_name · dense_vector     │
│                               · sparse_vector    │
│ 作用：用户模糊提问 → 语义匹配定位到「哪个商品」   │
└─────────────────────────────────────────────────┘
                    ↕ 靠 item_name 字符串值关联
┌─────────────────────────────────────────────────┐
│ kb_chunks（切片级 / 书页正文）                    │
│ 每个切片 1 行                                     │
│   chunk_id · content · title · parent_name       │
│   · part · file_title · item_name · 双向量       │
│ 作用：filter 出该商品切片 → 内容向量精搜          │
└─────────────────────────────────────────────────┘
```

| 维度 | `kb_item_names` | `kb_chunks` |
|------|-----------------|-------------|
| 层级 | 文档级 | 切片级 |
| 行数 | 每文档 1 行 | 每切片 1 行 |
| `item_name` | 带向量（用于识别商品） | 仅字符串标签（用于过滤） |
| 索引 | HNSW（COSINE）+ SPARSE_INVERTED（IP） | 同左 |

> 两个集合**写入时互不知道对方**，靠共享同一个 `item_name` 字符串值隐式关联；
> 真正的"接力"发生在**检索侧**：先在 `kb_item_names` 识别商品 → 拿字符串去 `kb_chunks` 过滤 → 内容向量精搜。

---

## 状态定义

> 源码：`app/import_process/agent/state.py`

节点之间**不通过文件、不通过全局变量**传递数据，而是靠 `ImportGraphState`（`TypedDict`）在内存中流转：

```python
class ImportGraphState(TypedDict):
    task_id: str                 # 任务唯一 ID
    # --- 流程控制 ---
    is_md_read_enabled: bool     # 是否走 Markdown 路径
    is_pdf_read_enabled: bool    # 是否走 PDF 路径
    # --- 路径 ---
    local_dir: str               # 任务工作目录
    local_file_path: str         # 原始输入文件
    file_title: str              # 文件名去后缀
    pdf_path: str / md_path: str
    # --- 内容 ---
    md_content: str              # Markdown 全文
    chunks: list                 # 切片列表（list[dict]）
    item_name: str               # 识别出的商品名
    # --- 向量 ---
    embeddings_content: list     # 待入库的向量数据
```

`create_default_state(**overrides)` 会**深拷贝默认模板再覆盖**，避免多任务间互相污染。

**节点产出的关键字段变化：**

| 节点 | 写入 state 的字段 |
|------|------------------|
| 1 `node_entry` | `file_title`、`is_*_read_enabled`、`pdf_path` / `md_path` |
| 2 `node_pdf_to_md` | `md_path`（解析后的 md） |
| 3 `node_md_img` | `md_path`（切到 `_new.md`）、`md_content`（图片已替换） |
| 4 `node_document_split` | `chunks` |
| 5 `node_item_name_recognition` | `item_name`、每个 chunk 的 `item_name` |
| 6 `node_bge_embedding` | 每个 chunk 的 `dense_vector` / `sparse_vector` |
| 7 `node_import_milvus` | 写入 Milvus（state 不再变化） |

### 检索流程：`QueryGraphState`

> 源码：`app/query_process/agent/state.py`

```python
class QueryGraphState(TypedDict):
    session_id: str                  # 会话唯一标识
    original_query: str              # 用户原始问题（保留原话，供落库与兜底）
    # --- 三路召回 ---
    embedding_chunks: list           # Embedding 路召回结果
    hyde_embedding_chunks: list      # HyDE 路召回结果
    web_search_docs: list            # 联网搜索结果
    # --- 排序 ---
    rrf_chunks: list                 # RRF 融合后的切片
    reranked_docs: list              # 重排序后的最终 Top-K
    # --- 生成 ---
    prompt: str                      # 组装好的 Prompt
    answer: str                      # 最终答案（也承载「反问 / 拒答」话术）
    # --- 辅助 ---
    item_names: List[str]            # 提取 / 确认的商品名
    rewritten_query: str             # 改写后的问题
    history: list                    # 历史对话快照
    is_stream: bool                  # 是否流式输出
```

同样提供 `create_query_default_state(**overrides)`（深拷贝 + 覆盖）与 `copy_query_state`，保证多任务之间互不污染。

`answer` 有「双重身份」：既承载最终生成的答案，也是**条件边的判据**——非空即表示流程已在澄清阶段结束，无需再检索。

---

## 导入 Web 服务与前端对接

> 源码：`app/import_process/api/file_import_service.py` · 页面：`app/import_process/page/import.html`

### 接口一览

| 方法 | 路径 | 作用 | 返回值 |
|------|------|------|--------|
| `GET` | `/import.html` | 返回上传页面（`FileResponse`） | HTML |
| `POST` | `/upload` | 接收多文件，逐个保存并生成 `task_id`，挂后台任务 | `{"code":200,"task_ids":[...]}` |
| `GET` | `/status/{task_id}` | 查询任务状态与节点进度 | `{"status":..., "running_list":[...], "done_list":[...]}` |

### 一次上传的完整时序

```
① 用户选文件 → POST /upload
        ↓
② task_id = str(uuid.uuid4())          ← 生成全局唯一号
        ↓
③ 建目录 output/20260906/{task_id}/    ← 日期 + 任务号双层隔离
        ↓
④ shutil.copyfileobj 流式写盘          ← 大文件不撑爆内存
        ↓
⑤ add_running_task / add_done_task("upload_file")
        ↓
⑥ background_tasks.add_task(run_graph_task, task_id, ...)
        ↓
⑦ 【立即返回 task_ids】                ← 用户不用干等
        ↓
⑧ 响应发出后，FastAPI 在线程池执行 run_graph_task：
     update_task_status(processing)
     init_state = create_default_state(...)
     for event in kb_import_app.stream(init_state):
         add_done_task(task_id, node_name)   ← 每完成一个节点打勾
     update_task_status(completed)
```

### 任务状态机

```
pending（已创建）
    ↓ 后台任务启动
processing（处理中）
    ↓ 图跑完            ↓ 任一节点异常
completed（完成）      failed（失败 + 完整堆栈日志）
```

### 进度是怎么被前端看到的

前端用**轮询**（polling）而非后端推送：

```javascript
// 上传后拿到 taskId
const data = await (await fetch("/upload", { method: "POST", body: fd })).json();
const taskId = data.task_ids[0];

// 每 2 秒问一次「好了没」
const timer = setInterval(async () => {
  const res = await fetch(`/status/${taskId}`);   // ← 模板字符串拼 URL
  const s = await res.json();
  render(s.done_list);                            // 渲染进度条
  if (s.status === "completed" || s.status === "failed") clearInterval(timer);
}, 2000);
```

后端 `/status/{task_id}` 的 `{task_id}` 是**路径参数占位符**，与函数参数 `task_id: str` 按名字对应，FastAPI 自动把 URL 槽位里的值注入进来。

<details>
<summary><b>三个任务函数的分工（易混淆）</b></summary>

| 函数 | 操作的数据 | 语义 |
|------|-----------|------|
| `update_task_status(id, "processing")` | `status` 标量 | 任务**整体**生命周期：pending → processing → completed/failed |
| `add_running_task(id, "node_entry")` | `running_list` 列表 | 某道**工序**开始 |
| `add_done_task(id, "node_entry")` | `done_list` 列表 | 某道**工序**完成 |

`upload_file` 与 `node_entry` 等节点是**同层级的工序**，所以都用 `add_*_task`；`update_task_status` 只在图真正开始/结束/失败时调用。

</details>

---

## 检索流水线：7 个节点

> 源码：`app/query_process/agent/nodes/` · 图组装：`app/query_process/agent/main_graph.py`

用户提问进入后，先做「意图澄清」，再并行三路召回，最后融合、精排、生成：

```
                          用户问题
                             │
                             ▼
        ┌────────────────────────────────────────┐
        │ node_item_name_confirm                 │  ① 指代消解 + 主体对齐
        │   历史 → LLM 抽取 item_names / 改写问题  │
        │   向量检索 kb_item_names → 阈值判定      │
        └───────────────────┬────────────────────┘
                            │ 条件边 condition_fun
              ┌─────────────┴─────────────┐
              │ state["answer"] 有值？     │
              │  有 → 直接输出反问/拒答     │
              │  无 → 三路并行召回          │
              └─────────────┬─────────────┘
        ┌──────────────┬────┴──────────────┐
        ▼              ▼                   ▼
  node_search_    node_search_       node_web_search_mcp
  embedding       embedding_hyde       （百炼 MCP 联网）
  改写问题检索      假设性文档检索
        └──────────────┴────┬──────────────┘
                            ▼
                   ┌─────────────────┐
                   │ node_rrf        │  ② RRF 融合（仅同源两路）
                   └────────┬────────┘
                            ▼
                   ┌─────────────────┐
                   │ node_rerank     │  ③ 交叉编码器精排 + 动态 TopK
                   └────────┬────────┘
                            ▼
                   ┌─────────────────┐
                   │ node_answer_    │  ④ 拼 Prompt → LLM → 答案 + 出处/图片
                   │ output          │
                   └─────────────────┘
```

| # | 节点 | 作用 | 关键产出 |
|---|------|------|---------|
| 1 | `node_item_name_confirm` | 指代消解 + 商品名对齐：读历史 → LLM 抽取/改写 → `kb_item_names` 检索 → 阈值判定，三选一：确认 / 反问 / 未找到 | `item_names`、`rewritten_query`、`history`；或 `answer`（反问/拒答） |
| 2 | `node_search_embedding` | 用 `rewritten_query` 向量 + `item_name` 过滤，检索 `kb_chunks` | `embedding_chunks` |
| 3 | `node_search_embedding_hyde` | HyDE：先让 LLM 编一段「假设答案」，再拿它 + 原问题去检索 | `hyde_embedding_chunks` |
| 4 | `node_web_search_mcp` | 经百炼 MCP 调用联网搜索，补充库外信息 | `web_search_docs` |
| 5 | `node_rrf` | 对**同源的两路**（Embedding + HyDE）做 RRF 倒数排名融合，去重后截断 | `rrf_chunks` |
| 6 | `node_rerank` | 合并 `rrf_chunks` + `web_search_docs`，用 `bge-reranker-large` 逐对打分，动态 TopK 截断 | `reranked_docs` |
| 7 | `node_answer_output` | 组装 Prompt（参考内容 + 历史 + 主体 + 问题）→ LLM 生成（支持流式）→ 提取图片 | `prompt`、`answer`；SSE 事件 |

### 条件路由：先判断「要不要往下检索」

`node_item_name_confirm` 之后是一条条件边，由 `state["answer"]` 决定去向：

```python
def condition_fun(state: QueryGraphState):
    if state["answer"]:
        return "node_answer_output"       # 澄清阶段已生成反问/拒答 → 直接输出
    else:
        return "node_search_embedding", "node_search_embedding_hyde", "node_web_search_mcp"
        #                                     ↑ 返回多个目标 = 三路并行
```

- **`answer` 非空** → `node_item_name_confirm` 走了「反问用户」或「未找到」，此时没有商品名可检索，直接把这句话交给输出节点。
- **`answer` 为空** → 主体已确认，三路检索并行开跑。

> 三条边汇入 `node_rrf`：LangGraph 会**等三个上游全部完成**再把 `node_rrf` 执行一次——这保证 web 结果在进入 `node_rerank` 之前已写入 state。

### 节点 1 内部：`node_item_name_confirm` 的 7 个 step

| step | 做了什么 |
|------|---------|
| 1 `get_recent_messages` | 读该会话最近历史（**快照，不含本轮问题**） |
| 2 `save_chat_message(user)` | 先落库占位，拿到 `message_id`（供 step 7 回填） |
| 3 `step_3_extract_info` | LLM（`json_mode`）产出 `item_names` + `rewritten_query` |
| 4 `step_4_vectorize_and_query` | 对每个 `item_name` 向量化 → `kb_item_names` 混合检索 Top5 |
| 5 `step_5_align_item_names` | 阈值对齐：`≥0.85` 确认 / `0.6~0.85` 候选 |
| 6 `step_6_check_confirmation` | 三分支：确认 → 回填历史 `item_names`；候选 → 反问；都没有 → 未找到 |
| 7 `step_7_write_history` | 有 `answer` 则存一条 assistant；再用 `message_id` 回填当前 user 消息 |

**双层索引正是在这里「接力」**：先拿 `item_name` 去 `kb_item_names` 定位主体，确认后才用 `rewritten_query` 去 `kb_chunks` 检索内容。

---

## 问答链路的关键设计

### 1. 指代消解（Query Rewriting）

多轮对话里用户会说「**它**怎么用」，这句话单独拿去做向量检索必然失焦——向量里没有任何商品信息。所以 `node_item_name_confirm` 先用 LLM 结合历史把句子补全：

```
原始："它的电池怎么样"             ← 语义残缺，检索必挂
改写："华为Mate60的电池续航怎么样"   ← 独立完整，可直接向量化
```

同一个 LLM 调用顺带产出两个字段，各管一段：

- **`item_names`** 回答「问的是哪个商品」→ 拿去查商品名表 (`kb_item_names`)
- **`rewritten_query`** 回答「问的是什么事」→ 拿去查切片表 (`kb_chunks`)

### 2. 三路召回，各司其职

| 路 | 查询方式 | 定位 | 是否进 RRF |
|---|---------|------|-----------|
| Embedding | `rewritten_query` 向量 | 语义最贴近的切片 | ✅ |
| HyDE | `rewritten_query + 假设性文档` 向量 | 换个角度再召一遍，弥补措辞差异 | ✅ |
| Web 搜索 | 百炼 MCP 联网 | 补充知识库外的最新信息 | ❌ 旁路给 rerank |

HyDE 的思路是：**先让 LLM 编一个「看起来像标准答案」的段落，再用它去检索**——因为「问题」和「答案」在向量空间里的分布并不一致，用假答案去搜，往往更容易命中真答案。

### 3. RRF 融合：为什么只能融同源两路

```python
score_map[chunk_id] = score_map.get(chunk_id, 0) + weight * (1.0 / (rank + k))
chunk_map.setdefault(chunk_id, chunk)      # 同一 chunk 只保留第一次出现的文档
```

RRF 的「融合」依赖 `chunk_id` 对齐——**同一个切片在多路里都出现，分数才累加**：

- Embedding 路与 HyDE 路查的都是 `kb_chunks`，共享同一套 `chunk_id` → **可以对齐**
- Web 搜索返回的是 `{title, url, snippet}`，**没有 chunk_id** → 无法参与融合，硬塞进去只会被 `continue` 跳过、留下一屏警告日志

所以 `node_rrf` 只读两路**是正确的设计**；web 结果走旁路，在 `node_rerank` 里与 RRF 结果一起参与精排。

`k=60` 的作用是**平滑名次差异**：`1/rank` 时第 1 名是第 2 名的 2 倍，而 `1/(60+rank)` 两者只差约 1.6%。分母加上 `k` 后，前几名不再是压倒性优势——**「多路都排前面」比「单路第一」更重要**，这正是融合的意义。

### 4. 重排序：双塔 vs 交叉编码器

向量检索用的是**双塔模型**：query 和 doc 各走各的编码器，最后比向量距离——两者从未「见面」，精度有限。`bge-reranker-large` 是**交叉编码器**，把 `[query, doc]` 拼成一个序列送进模型，注意力能在两者之间直接流转，判断精细得多。

代价是慢（每对候选都要跑一次完整前向），所以只能放在召回之后做精排：

```
稠密 + 稀疏混合检索（粗筛）
        ↓
RRF 融合去重（≤10 条）
        ↓
bge-reranker-large 逐对打分（精排）
        ↓
动态 TopK → 交给 LLM
```

### 5. 动态 TopK：用「断崖」代替拍脑袋定数字

`node_rerank` 不机械取前 5 条，而是检测**相邻分数的落差**：

```python
RERANK_MAX_TOPK  = 10      # 硬上限
RERANK_MIN_TOPK  = 1       # 保底（至少留 1 条）
RERANK_GAP_ABS   = 0.5     # 绝对落差阈值
RERANK_GAP_RATIO = 0.25    # 相对落差阈值
```

逐个比较相邻两条的分数差，**一旦出现断崖（绝对差 > 0.5，或相对差 > 25%）就截断**：

```
[0.90, 0.88, 0.85, 0.30, 0.28]   → 0.85 → 0.30 断崖 → 只取前 3 条
[0.90, 0.88, 0.85, 0.83, 0.80]   → 平滑下降      → 取满
```

分数分布陡峭就少取（后面的明显不相关），分布平缓就多取——**用数据的自然分界决定留几条**。

### 6. Prompt 组装与出处标注

`node_answer_output` 把检索结果渲染成带元信息的块交给 LLM：

```
[1][local] chunk_id=[4688...] [score=0.9521] title=[设备]
·	请勿拆解本设备，内部没有用户可维修的部件。

[2][web] [score=0.8732] title=[烫金机日常维护]
日常维护时需先断电……
```

- `[source]` 区分 `local`（库内切片）/ `web`（联网结果）
- `chunk_id` / `score` / `title` 供模型引用与人工核查
- 整个上下文受 `MAX_CONTEXT_CHARS = 12000` 约束，超长自动截断

Prompt（`prompts/answer_out.prompt`）明确要求**只根据参考内容作答、不要编造**，并在需要时按固定格式追加 `【图片】` 区块。答案中的图片 URL 由 `_extract_images_from_docs` 用正则从切片正文中提取。

---

## 问答 Web 服务与 SSE 流式

> 源码：`app/query_process/api/query_service.py` · 页面：`app/query_process/page/chat.html` · SSE 工具：`app/utils/sse_utils.py`

### 接口一览

| 方法 | 路径 | 作用 | 返回值 |
|------|------|------|--------|
| `GET` | `/chat.html` | 返回对话页面 | HTML |
| `POST` | `/query` | 提交问题：**流式立即回 `session_id`**，非流式同步返回答案 | `{"message", "session_id"[, "answer"]}` |
| `GET` | `/stream/{session_id}` | 建立 SSE 长连接，推送事件 | `text/event-stream` |
| `GET` | `/status/{task_id}` | 查询节点进度（轮询兜底） | `{status, running_list, done_list}` |
| `GET` | `/history/{session_id}` | 拉取最近历史 | `{"session_id", "items"}` |
| `DELETE` | `/delete/{session_id}` | 清空该会话历史 | `{"message", "deleted_count"}` |
| `GET` | `/health` | 健康检查 | `{"ok": true}` |

> `/query` 用 **POST 而非 GET**：提问内容与 `session_id` 不该出现在 URL 里（会被写进浏览器历史、服务器 access log）。

### 流式 vs 非流式：两条交付路径

| | 流式（`is_stream=true`） | 非流式（`is_stream=false`） |
|---|---|---|
| 执行方式 | `BackgroundTasks` 丢后台，接口**立即返回** | 同步阻塞，跑完才返回 |
| 答案怎么给 | 走 SSE 长连接逐字推送 | 直接塞进响应 JSON 的 `answer` |
| `return` 里有答案吗 | ❌ 只有 `session_id` | ✅ 有（等完了） |

非流式必须**原地等**：答案要装在这次 HTTP 响应里带回去。若改成后台任务，`return` 那一刻答案还没生成，只能返回空。

### SSE 事件表

| event | 谁发的 | data | 前端处理 |
|-------|--------|------|---------|
| `ready` | `sse_generator` | `{}` | 确认连接已建立 |
| `progress` | `task_utils.task_push_queue` | `{status, done_list, running_list}` | 更新进度条与节点日志 |
| `delta` | `node_answer_output`（生成中） | `{"delta": "一个字"}` | **追加**到气泡（打字机效果） |
| `delta`（收尾帧） | `node_answer_output`（结束后） | `{"answer": "完整答案", "image_urls": [...]}` | **赋值**完整答案 + 渲染图片 |
| `error` | 后台任务异常 / 生成异常 | `{"error": "异常文本"}` | 显示失败原因 |

> ⚠️ 收尾帧与增量帧共用 `delta` 事件名：前端 `delta` 回调只读 `d.delta`，因此这条收尾帧不会被渲染；而 `chat.html` 里注册的 `final` / `final_answer` 监听器后端尚未发出。把收尾帧改用 `SSEEvent.FINAL` 即可打通最后一帧。

### 断连检测：`request.is_disconnected()`

SSE 是长连接，服务端生成器会一直循环推消息。如果用户关了页面而服务端不知道，这个循环会**永远空转**，占着连接和队列不放。`sse_generator` 每轮先探测一次：

```python
while True:
    if await request.is_disconnected():   # 前端还在吗
        break                             # 断了就退出
    ...
```

`finally` 中再 `remove_sse_queue(session_id)` 清理队列。这也是 `/stream` 路径函数必须声明 `request: Request` 的原因。

### 前端会话与事件订阅

```javascript
// ① session_id 存在 localStorage —— 关浏览器也保留，下次打开仍是同一会话
let sessionId = localStorage.getItem('kb_session_id');
if (!sessionId) {
  sessionId = 'sess-' + Math.random().toString(36).slice(2) + Date.now().toString(36);
  localStorage.setItem('kb_session_id', sessionId);
}

// ② 提问 → 拿 session_id → 开 SSE 专线
const res = await fetch(`${API_BASE}/query`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: text, session_id: sessionId, is_stream: true })
});
const { session_id } = await res.json();

const es = new EventSource(`${API_BASE}/stream/${session_id}`);
es.addEventListener('delta', e => { /* 逐字追加到气泡 */ });
es.addEventListener('final', e => { /* 收尾：完整答案 + 图片 + es.close() */ });
es.addEventListener('error', e => { /* 展示错误信息 */ });
```

一个 `session_id` 对应一个队列（`_session_stream: Dict[str, Queue]`），保证「谁的问题答案进谁的气泡」——多人同时提问不会串台。

---

## 快速开始

### 1. 环境要求

- Python **3.11**
- [uv](https://docs.astral.sh/uv/)（包管理）
- Docker（跑 Milvus / MinIO）
- 显卡（可选，BGE-M3 支持 GPU / CPU）

### 2. 安装依赖

```bash
uv sync
```

<details>
<summary><b>GPU 用户请注意（重要）</b></summary>

`FlagEmbedding` 会把 `torch` 拉成 CPU 版，覆盖已装的 GPU 版。解决办法：在 `pyproject.toml` 里锁定 PyTorch 走 NVIDIA 源：

```toml
[tool.uv.sources]
torch       = { index = "pytorch_cuda" }
torchvision = { index = "pytorch_cuda" }
torchaudio  = { index = "pytorch_cuda" }

[[tool.uv.index]]
name = "pytorch_cuda"
url  = "https://download.pytorch.org/whl/cu124"   # 按你的 CUDA 版本改
explicit = true
```

> 注意：uv 的 index name **不支持连字符**，`pytorch-cuda` 会报错，必须写成 `pytorch_cuda`。

然后：

```bash
rm uv.lock
uv lock
uv sync --reinstall
uv run python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

</details>

### 3. 启动依赖服务

```bash
# Milvus（standalone 单机版）
bash standalone_embed.sh start        # 首次部署
sudo docker start milvus-standalone   # 日常启动

# MinIO（图片图床）
docker run -d --name minio \
  -p 9000:9000 -p 9001:9001 \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  -v $(pwd)/minio-data:/data \
  quay.io/minio/minio server /data --console-address ":9001"
```

### 4. 配置 `.env`

```ini
# ===== 大模型（阿里云百炼，OpenAI 兼容模式）=====
LLM_DEFAULT_MODEL=qwen-flash
VL_MODEL=qwen3-vl-flash
OPENAI_API_KEY=sk-你的百炼Key
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_DEFAULT_TEMPERATURE=0.1

# ===== Embedding（BGE-M3）=====
BGE_M3_PATH=D:/ai_models/bge-m3
BGE_DEVICE=cpu          # GPU 改成 cuda:0
BGE_FP16=0              # GPU 改成 1

# ===== Reranker（BGE-Reranker-Large，问答链路精排）=====
BGE_RERANKER_LARGE=D:/ai_models/BAAI/bge-reranker-large
BGE_RERANKER_DEVICE=cpu      # GPU 改成 cuda:0
BGE_RERANKER_FP16=0          # GPU 改成 1

# ===== Milvus =====
MILVUS_URL=http://127.0.0.1:19530
CHUNKS_COLLECTION=kb_chunks
ITEM_NAME_COLLECTION=kb_item_names
EMBEDDING_DIM=1024

# ===== MinIO（图片图床）=====
MINIO_ENDPOINT=127.0.0.1:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=knowledge-base-files
MINIO_IMG_DIR=/upload-images
MINIO_SECURE=False

# ===== MinerU（PDF 解析）=====
MINERU_API_TOKEN=你的MinerU Token
MINERU_BASE_URL=https://mineru.net/api/v4

# ===== MCP（百炼联网搜索，问答链路第三路召回）=====
MCP_DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/mcp
```

> `.env` 已在 `.gitignore` 中，**请勿提交真实密钥**。

### 5. 启动服务

```bash
# 终端 1：导入服务（上传文档建库）
uv run uvicorn app.import_process.api.file_import_service:app --host 127.0.0.1 --port 8000 --reload

# 终端 2：问答服务（检索 + 生成 + SSE 流式）
uv run uvicorn app.query_process.api.query_service:app --host 127.0.0.1 --port 8001 --reload
```

| 服务 | 端口 | 页面 |
|------|------|------|
| 导入服务 | 8000 | <http://127.0.0.1:8000/import.html> |
| 问答服务 | 8001 | <http://127.0.0.1:8001/chat.html> |

> 问答服务依赖 MongoDB（会话历史）与 Milvus（向量检索），启动前确认两者都已运行。

### 6. 单节点调试

每个节点文件底部都有 `if __name__ == "__main__":` 测试入口，可直接运行：

```bash
# 导入链
uv run python -m app.import_process.agent.nodes.node_item_name_recognition
uv run python -m app.import_process.agent.nodes.node_document_split

# 检索链
uv run python -m app.query_process.agent.nodes.node_rrf
uv run python -m app.query_process.agent.nodes.node_web_search_mcp
```

---

## 目录结构

```
knowledge_base/
├── app/
│   ├── clients/                    # 外部客户端封装（单例）
│   │   ├── milvus_utils.py         #   Milvus 连接 + 混合检索
│   │   ├── minio_utils.py          #   MinIO 连接 + 自动建桶
│   │   └── mongo_history_utils.py  #   MongoDB 会话历史
│   ├── conf/                       # 配置数据类（读 .env）
│   ├── core/
│   │   ├── logger.py               #   loguru 日志 + node/step 装饰器
│   │   └── load_prompt.py          #   提示词外置加载
│   ├── import_process/             # 【导入模块】
│   │   ├── agent/
│   │   │   ├── main_graph.py       #     LangGraph 图组装 + compile
│   │   │   ├── state.py            #     ImportGraphState 定义
│   │   │   └── nodes/              #     7 个节点
│   │   ├── api/file_import_service.py  # FastAPI 服务
│   │   └── page/import.html        #     上传页面
│   ├── query_process/              # 【检索模块】
│   │   ├── agent/
│   │   │   ├── main_graph.py       #     LangGraph 图组装 + 条件边
│   │   │   ├── state.py            #     QueryGraphState 定义
│   │   │   └── nodes/              #     7 个节点（对齐/三路召回/RRF/重排/生成）
│   │   ├── api/query_service.py    #     FastAPI 服务（含 SSE 流式）
│   │   └── page/chat.html          #     问答页面
│   ├── lm/
│   │   ├── lm_utils.py             #   LLM 客户端（带缓存）
│   │   ├── embedding_utils.py      #   BGE-M3 向量化
│   │   └── reranker_utils.py       #   Rerank 精排
│   ├── utils/
│   │   ├── task_utils.py           #   任务状态与进度
│   │   ├── rate_limit_utils.py     #   API 限流（令牌桶）
│   │   └── sse_utils.py            #   SSE 流式输出
│   └── tool/                       # 模型下载脚本
├── prompts/                        # 提示词模板（.prompt，外置可热改）
├── doc/                            # 测试用产品手册
├── output/                         # 上传与解析产物（按日期/task_id 分目录）
└── pyproject.toml
```

---

## 关键设计决策

<details>
<summary><b>1. 反规范化：标题与商品名都"冗余"进每条数据</b></summary>

- **标题进 `content` 第一行**：切片会被二次切碎，碎块没有独立 `title` 字段；标题作为"页眉"跟着 content 走，切碎了也知道属于哪一章。
- **`item_name` 广播到每个 chunk**：Milvus 是向量库，检索核心操作是"带过滤条件的向量搜索"，每行自带商品名才能直接 `filter`。

代价是多存几个字符串，收益是检索时**不需要回头查别的表**。

</details>

<details>
<summary><b>2. 向量化文本："核心词前置"</b></summary>

```python
text = f"商品：{item_name}\n{content}"
```

BGE-M3 对文本**前 ~128 个 token 注意力最集中**，把商品名放在开头，等于给向量"印上"商品特征，显著提升召回率。

</details>

<details>
<summary><b>3. 图片可检索：VLM 摘要 + 对象存储双保险</b></summary>

RAG 只能检索文本，图片是"哑巴证人"。用 VLM 把图片翻译成中文描述：

```
![img](images/a.png)
        ↓ VLM + MinIO
![产品外观展示图，白色机身，正面有指示灯](http://minio/.../a.png)
```

**描述负责被检索，URL 负责被展示**——两者缺一不可。

</details>

<details>
<summary><b>4. 异步导入：不阻塞 + 进度可见</b></summary>

`BackgroundTasks` 让接口立即返回 `task_id`，后台跑几十秒~几分钟的流水线；配合 `done_list` + 前端轮询，用户能看到"进行到哪个节点"。

局限：任务状态存内存，服务重启会丢——生产环境应换 Celery / RQ + Redis。

</details>

<details>
<summary><b>5. 幂等入库：先删后插</b></summary>

同一文档重复导入时，先按 `item_name` 删除旧记录再插入新的，避免库里残留重复脏数据。

</details>

<details>
<summary><b>6. 提示词外置</b></summary>

`prompts/*.prompt` 文件存放模板，用 `load_prompt(name, **kwargs)` 渲染占位符——改提示词不用改代码。

</details>

<details>
<summary><b>7. 先定位主体，再检索内容</b></summary>

如果直接拿用户问题去检索，问题里既有「商品」又有「意图」，向量语义会被两者平均，容易失焦。

所以拆成两步：**先用 `item_name` 去 `kb_item_names` 确认「问的是哪个商品」，再用 `rewritten_query` 去 `kb_chunks` 找「哪几段内容」**。前者是短文本精确对齐，后者是长文本语义匹配——各用各的长处。

</details>

<details>
<summary><b>8. RRF 只融「同源」数据</b></summary>

RRF 靠 `chunk_id` 判断「是不是同一条」，同一 chunk 在多路出现才累加分数。Embedding 与 HyDE 两路查的都是 `kb_chunks`，天然同源；Web 搜索返回网页、没有 chunk_id，**强行塞进 RRF 只会被静默跳过**。

这也是为什么图里三条边汇入 `node_rrf`，但 `node_rrf` 只读两路——第三条边的作用是「等 web 写完 state」，让它赶上后面的 rerank。

</details>

<details>
<summary><b>9. 动态 TopK：让数据决定留几条</b></summary>

固定 Top-5 有两个问题：分数都很高时会漏掉本该留下的，分数断崖式下跌时又会混进明显不相关的。改成**检测相邻分数的落差**后，由数据本身决定截断点，同时用 `MIN_TOPK=1` 保底、`MAX_TOPK=10` 封顶。

</details>

<details>
<summary><b>10. 一个图，两种交付：`is_stream` 贯穿全链路</b></summary>

`is_stream` 不是 HTTP 层的开关，而是**从接口一路传到节点**的标记：

| 位置 | 它决定什么 |
|------|-----------|
| `/query` | 走后台任务（流式）还是同步阻塞（非流式） |
| `task_utils.add_*_task` | 是否顺手推一条 `progress` SSE 事件 |
| `node_answer_output` | 用 `llm.stream()` 逐字推，还是 `llm.invoke()` 一次拿 |

**同一个图、同一套节点，只靠这个标记切换交付方式**，逻辑不用重写两份。

</details>

---

## 踩坑记录

> 记录真实排查过的坑，避免重复踩

<details>
<summary><b>坑 1：改了 .env 却不生效（最隐蔽）</b></summary>

**现象**：`.env` 改了模型名/地址，重启后报错依旧。

**根因**：`load_dotenv()` 默认 `override=False`——遇到**系统环境变量里已存在的同名变量就跳过、不覆盖**。如果之前在 Windows 系统环境变量里配过 `OPENAI_API_KEY`，`.env` 的值会被无视。

**解决**：

```python
load_dotenv(override=True)   # 让 .env 强制覆盖
```

并清理系统残留变量（Windows：高级系统设置 → 环境变量）。

</details>

<details>
<summary><b>坑 2：torchvision::nms does not exist</b></summary>

**现象**：BGE-M3 加载时报 `RuntimeError: operator torchvision::nms does not exist`，伴随 `PreTrainedModel` / `transformers.integrations` 导入失败。

**根因**：`torch` 与 `torchvision` **版本不同代**——torchvision 是为另一个 torch 版本编译的，算子对不上。典型情况：手动用 NVIDIA 源装了 torch（2.6.0+cu124），但 torchvision/torchaudio 还是 PyPI 的 CPU 版（0.25.0）。

**解决**：三件套**一起**从同一源重装：

```bash
uv pip install --force-reinstall torch torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/cu124
```

验证三者版本号同代、且都带 `+cu124`。

</details>

<details>
<summary><b>坑 3：装 FlagEmbedding 后 GPU 不可用</b></summary>

**现象**：`torch.cuda.is_available()` 变成 `False`。

**根因**：`FlagEmbedding` 依赖 `torch`，uv 按默认源（PyPI）拉 CPU 版覆盖了 GPU 版。

**解决**：见上方「快速开始 → GPU 用户请注意」，用 `[tool.uv.sources]` 锁 NVIDIA 源。

</details>

<details>
<summary><b>坑 4：uv index name 不支持连字符</b></summary>

`name = "pytorch-cuda"` 会解析报错，必须写成 `pytorch_cuda`（下划线）。

</details>

<details>
<summary><b>坑 5：MinerU 上传报 403 SignatureDoesNotMatch</b></summary>

**根因**：系统代理污染了预签名 URL 的请求头。

**解决**：上传时关掉环境代理：

```python
session = requests.Session()
session.trust_env = False
session.put(signed_url, data=...)
```

</details>

<details>
<summary><b>坑 6：Markdown 入口报 FileNotFoundError</b></summary>

**根因**：`node_md_img` 硬编码扫描 `md 文件同级目录/images/`。走 PDF 入口时 MinerU 会自动生成该目录；**直接上传 MD 则没有**，且 Web 上传接口是"一文件一任务一目录"，图片不会与 md 同目录。

**规避**：走 PDF 入口，或提前把 `md + images/` 整理在同一目录。

</details>

<details>
<summary><b>坑 7：模型名 not support</b></summary>

**排查顺序**：

1. `OPENAI_BASE_URL` 是不是百炼的 `/compatible-mode/v1`（非百炼端点永远不认 qwen 系列）
2. 模型名是否带对版本（`qwen-flash` vs `qwen3-flash`）
3. 老型号不支持 `enable_thinking` 参数 → 把 `extra_body` 改成 `{}`

</details>

<details>
<summary><b>坑 8：稀疏向量报 numpy 类型不可哈希</b></summary>

BGE-M3 稀疏向量是 CSR 矩阵，索引是 `numpy.int64`，直接做字典 key 不可哈希。需用 `.tolist()` 转成 Python 原生类型。

</details>

---

## 后续计划

- [ ] **检索参数调参实验**：RRF 的 `k`、各路口召回条数、断崖阈值的对比数据
- [ ] **评测集**：问答准确率 / 召回率的量化报告（有数据才叫工程）
- [ ] 统一 SSE 收尾事件名（收尾帧由 `delta` 改为 `final`），打通最后一条完整答案与图片
- [ ] 多路召回的第三路 BM25，与 BGE-M3 稀疏向量做效果对比
- [ ] 会话管理：前端「新建对话」入口（当前 `session_id` 固定存在 `localStorage`）
- [ ] 导入接口支持 ZIP 批量上传（自动解压 `md + images/`）
- [ ] 任务状态持久化（Redis / Celery），摆脱单进程内存态

---

## 致谢

- [LangChain / LangGraph](https://github.com/langchain-ai/langgraph)
- [Milvus](https://github.com/milvus-io/milvus)
- [FlagEmbedding / BGE-M3](https://github.com/FlagOpen/FlagEmbedding)
- [MinerU](https://github.com/opendatalab/MinerU)
- [MinIO](https://github.com/minio/minio)
- 阿里云百炼大模型服务

---

<div align="center">

如果这个项目对你有帮助，欢迎 Star

</div>
