# mini-rag-v1

## 项目简介

这是一个从零手写的 Mini RAG（Retrieval-Augmented Generation）项目。

项目没有使用 LangChain 等框架，而是手动实现：

* 文档切分（chunking）
* embedding
* 语义检索（semantic search）
* 向量数据库（FAISS）
* retrieval
* prompt 构造

目标是理解：RAG 的数据到底是怎么流动的，而不是只会调用框架。

---
# 项目 Pipeline

```text
document
↓
chunking
↓
chunks
↓
embedding
↓
FAISS vector database
↓
retrieval
↓
retrieved chunks
↓
context
↓
RAG prompt
↓
LLM API (DeepSeek)
↓
AI Answer
```
# 最终效果展示
```
Question:
What model uses attention?

Retrieved Context:
Transformers use attention mechanism.

AI Answer:
Based on the known information provided,the model that uses the attention mechanismis the Transformer.
```
---

# 学到的核心概念

## 1. Embedding
文本可以通过 embedding model 转换成向量。
例如：

```text
"What model uses attention"
↓
[0.12, -0.55, ...]
```

embedding 后：语义相近的文本，在向量空间中也会更接近。

---
## 2. Semantic Search（语义检索）
项目不是通过关键词匹配，而是通过向量相似度进行检索。

例如：
query：

```text
What model uses attention
```

仍然可以检索到：

```text
Transformers use attention mechanism.
```

即使两个句子不是完全相同的关键词。

---
## 3. Chunking
真实 RAG 不会直接对整篇长文档做 embedding。

而是：

```text
长文档
↓
切分成多个 chunks
↓
每个 chunk 单独 embedding
```

本项目中：
```python
chunks = document.split("\n\n")
```
实现了最简单版本的 chunking。

---
## 4. FAISS 向量数据库
项目使用：
```python
faiss.IndexFlatL2()
```
建立向量索引。

作用是快速搜索最相似的 embedding，而不是手动遍历所有向量。

---
## 5. RAG Prompt
检索出的 chunks 会被拼接成：
```python
context
```
然后构造成：
```python
prompt
```
最终：
```text
retrieval + generation
```
形成完整 RAG 流程。

## 6. Retrieval 和 Generation 是两个阶段
RAG 并不是大模型本身，而是：retrieval + generation两个阶段共同完成问答。

其中：
Retrieval 负责查找相关知识
Generation 负责组织语言生成回答

## 7. Embedding Model 和 LLM 是不同模型
项目中：
Embedding Model：all-MiniLM-L6-v2

负责：文本 → 向量

用于：
* semantic search
* retrieval
* vector database
* LLM

DeepSeek Chat

负责：

文本 → 回答

用于：

* reasoning
* generation
* QA

---
# 重要数据形态（shape）

query_embedding.shape : (384,)
表示：

```text
一个384维向量
```

---
query_embedding_2d.shape :(1,384)
表示：

```text
1个query
每个query 384维
```
FAISS search 需要二维输入。

---
chunk_embeddings.shape:(5,384)
```
表示：

```text
5个chunk
每个chunk一个384维向量
```
# RAG 的本质是：

给大模型外挂知识库，而不是重新训练大模型。

流程：

外部知识
↓
retrieval
↓
context
↓
prompt
↓
LLM
↓
answer

# 技术栈
- Python
- NumPy
- sentence-transformers
- FAISS
- OpenAI SDK
- DeepSeek API

---
# 学到的数据流意识
项目中重点学习：

```text
当前数据是什么类型
shape 怎么变化
数据下一步流向哪里
```

例如：

```text
list[str]
↓
embedding
↓
ndarray
↓
FAISS
↓
indices
↓
retrieved chunks
↓
context string
```

---
# 当前项目完成内容

* [x] document chunking
* [x] embedding
* [x] cosine similarity retrieval
* [x] FAISS retrieval
* [x] top-k search
* [x] retrieved chunks
* [x] context construction
* [x] RAG prompt construction

## v2 更新内容

在 v1 基础上，进一步实现：

- knowledge.txt 外部知识库加载
- 固定长度 Chunk 切分
- Overlap Chunk（重叠切分）
- 用户动态提问
- while True 多轮问答
- DeepSeek API 接入
- 完整 RAG 闭环

流程：

Document
↓
Chunk
↓
Embedding
↓
FAISS
↓
Retrieval
↓
Context
↓
Prompt
↓
DeepSeek
↓
Answer

## 项目收获

进一步理解：

- Chunk 为什么存在
- Overlap 的作用
- Embedding Model 和 LLM 的区别
- Retrieval 和 Generation 的区别
- RAG 不等于大模型
- 知识库负责提供事实
- LLM 负责组织语言生成答案

RAG 的本质：

外部知识
↓
Retrieval
↓
Context
↓
Prompt
↓
LLM
↓
Answer
