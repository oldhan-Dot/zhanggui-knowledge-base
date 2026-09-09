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
- [状态定义](#状态定义)
- [Web 服务与前端对接](#web-服务与前端对接)
- [快速开始](#快速开始)
- [目录结构](#目录结构)
- [关键设计决策](#关键设计决策)
- [踩坑记录](#踩坑记录)
- [后续计划](#后续计划)

---

## 项目简介

**掌柜智库** 是一个面向企业私有产品文档的 RAG（Retrieval-Augmented Generation，检索增强生成）知识库系统。

企业积累了大量产品手册（PDF / Markdown），传统方式靠人工检索、关键词搜索，效率低且看不懂图片内容。本项目把文档加工成**可语义检索的向量知识库**，并支持多模态（图片也能被检索到）。

### 核心价值

| 能力 | 说明 |
|------|------|
| **文档结构化** | PDF 经 MinerU 高精度解析为 Markdown，保留标题层级与图片 |
| **多模态理解** | 用视觉大模型（VLM）给图片生成中文语义描述 + 上传对象存储，图片从此"可被检索" |
| **语义切片** | 标题层级初切 + 递归二次切分，每个切片自带"页眉"，切碎了也不丢上下文 |
| **双层索引** | 商品级粗筛（`kb_item_names`）+ 切片级精搜（`kb_chunks`） |
| **混合检索** | 稠密向量（语义泛化）+ 稀疏向量（关键词精准），加权融合召回 |
| **异步导入** | FastAPI `BackgroundTasks` + 任务状态机，长任务不阻塞、进度实时可见 |

---

## 当前进度

| 模块 | 状态 | 说明 |
|------|------|------|
| **导入流水线（知识库构建）** | 已完成 | 7 个节点端到端跑通，本 README 重点覆盖 |
| **Web 上传服务 + 前端页面** | 已完成 | `/upload` `/status/{task_id}` `/import.html` |
| **检索流水线（智能问答）** | 待补充 | 节点代码已就位，README 文档后续补充 |

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
| [MinerU](https://github.com/opendatalab/MinerU) | PDF 高精度解析（云端 API） | [Docs](https://mineru.readthedocs.io/) |
| [阿里云百炼](https://bailian.console.aliyun.com/) | 大模型服务（Qwen 系列，OpenAI 兼容模式） | [兼容 API 文档](https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope) |
| [Qwen3-VL-Flash](https://help.aliyun.com/zh/model-studio/models) | 视觉大模型，生成图片中文描述 | [Docs](https://help.aliyun.com/zh/model-studio/models) |

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

---

## Web 服务与前端对接

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
```

> `.env` 已在 `.gitignore` 中，**请勿提交真实密钥**。

### 5. 启动服务

```bash
uv run uvicorn app.import_process.api.file_import_service:app --host 127.0.0.1 --port 8000 --reload
```

浏览器打开：<http://127.0.0.1:8000/import.html>

### 6. 单节点调试

每个节点文件底部都有 `if __name__ == "__main__":` 测试入口，可直接运行：

```bash
uv run python -m app.import_process.agent.nodes.node_item_name_recognition
uv run python -m app.import_process.agent.nodes.node_document_split
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
│   ├── query_process/              # 【检索模块】节点已就位
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

- [ ] **检索模块文档**：`node_item_name_confirm` → `search_embedding` → `hyde` → `web_search_mcp` → `rrf` → `rerank` → `answer_output`
- [ ] RRF 融合与 Rerank 精排的调参说明
- [ ] SSE 流式输出的前端接入
- [ ] 导入接口支持 ZIP 批量上传（自动解压 `md + images/`）
- [ ] 任务状态持久化（Redis / Celery）

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
