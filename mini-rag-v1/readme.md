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

