# Multi-Paper Research Agent

## 项目简介

这是一个基于 RAG 和 Agent 思想实现的多论文研究助手项目。项目支持读取多篇学术论文，构建统一的向量知识库，并基于用户问题进行检索、问答和论文对比。
本项目没有直接使用 LangChain、LlamaIndex 等框架，而是手动实现核心流程，目的是理解 RAG 和 Agent 系统内部的数据流与模块协作方式。

---

## 当前支持的论文(都是组会读过的论文)
* FedAA
* ClusterGuard
* HealSplit
* BAPerturb
---

## 项目功能
### 1. 多 PDF 读取

使用 `PyPDF` 读取多篇论文内容，并统一保存为文档列表。

```text
PDF 文件
↓
PdfReader
↓
document(str)
```

---
### 2. 文档切分 Chunking
将长论文切分为多个小片段，并加入 overlap，减少上下文被切断的问题。
```python
chunk_size = 500
overlap = 100
```
---
### 3. Embedding 向量化
使用 SentenceTransformer 将每个 chunk 转换为向量。
```text
chunk文本
↓
embedding model
↓
384维向量
```
---
### 4. FAISS 向量检索
使用 FAISS 建立向量索引，实现语义检索。
```text
用户问题
↓
query embedding
↓
FAISS
↓
Top-K chunks
``

---
### 5. Query Rewriting
使用 DeepSeek 对用户问题进行改写，使问题更适合检索。
例如：

```text
what is fedaa
```
改写为：
```text
FedAA proposed method algorithm
```
这样可以提升检索质量。

---
### 6. Source Tracking 来源追踪
每个 chunk 保存来源论文信息：
```python
{
    "source": "data/FedAA.pdf",
    "chunk": "..."
}
```
这样系统可以知道检索到的内容来自哪一篇论文。

---
### 7. Citation 证据引用
回答中会附带证据来源，例如：

```text
Source:
data/FedAA.pdf | chunk_id:25
data/FedAA.pdf | chunk_id:30
```
这让回答不只是生成文本，而是有可追踪依据。

---
### 8. Metadata Filter 元数据过滤
在比较论文时，系统可以指定只在某一篇论文内部检索。
例如：

```python
retrieve("FedAA", source_filter="data/FedAA.pdf")
retrieve("ClusterGuard", source_filter="data/ClusterGuard.pdf")
```
这样可以避免在多论文知识库中检索混乱。

---
### 9. Agent Router 任务路由
系统会先判断用户问题类型：
```text
普通问答
or
论文对比
```
不同任务走不同流程。

---
### 10. 论文对比功能
例如用户输入：

```text
Compare FedAA and ClusterGuard
```
系统会执行：

```text
识别 compare 任务
↓
拆分 FedAA / ClusterGuard
↓
分别检索两篇论文
↓
构造比较 Prompt
↓
生成对比表格
```

---
## 系统架构
```text
用户问题
↓
classify_task()

├── common_qa
│   ↓
│   retrieve()
│   ↓
│   generate_answer()
│
└── compare
    ↓
    handle_compare()
    ↓
    retrieve(Paper A)
    retrieve(Paper B)
    ↓
    compare_prompt
    ↓
    DeepSeek
```

---
## 核心数据流

```text
PDF Papers
↓
Document Text
↓
Chunks
↓
Chunk Embeddings
↓
FAISS Index
↓
User Query
↓
Query Rewrite
↓
Retrieval
↓
Context
↓
Prompt
↓
LLM Answer
```

---
## 技术栈
* Python
* PyPDF
* NumPy
* Sentence Transformers
* FAISS
* OpenAI SDK
* DeepSeek API

---
## 示例问题

```text
Which paper uses reinforcement learning?

What is the main idea of FedAA?

What is ClusterGuard?

Compare FedAA and ClusterGuard

Compare HealSplit and BAPerturb
```

---
## 项目收获
通过本项目，我理解了：
* RAG 的完整流程
* 多论文知识库如何构建
* Chunk 和 Overlap 的作用
* Embedding 和 FAISS 如何配合完成语义检索
* Query Rewrite 如何提升检索质量
* Citation 如何让回答可追踪
* Metadata Filter 如何让检索更精确
* Agent Router 如何让系统根据不同任务走不同流程
* 普通 RAG 和简单 Agent 的区别

---
## 项目总结
本项目从最基础的 Paper-RAG 开始，逐步升级为一个 Multi-Paper Research Agent。
它不只是一个“Chat with PDF”小 demo，而是包含了：
```text
多文档知识库
+
语义检索
+
查询改写
+
来源追踪
+
元数据过滤
+
任务路由
+
多步检索
```
的 AI 工程项目雏形。
这个项目帮助我从“会调用模型”进一步理解了“如何搭建一个 AI 系统”。
