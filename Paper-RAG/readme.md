# Paper-RAG

## 项目简介

Paper-RAG 是一个从零实现的论文问答系统（Research Assistant）。

项目支持读取多篇学术论文，自动构建向量知识库，并结合大语言模型实现论文内容检索与问答。

本项目没有使用 LangChain、LlamaIndex 等 RAG 框架，而是手动实现完整流程，以理解 RAG 系统内部的数据流与工作原理。

当前知识库包含：

* FedAA
* ClusterGuard
* HealSplit
* BAPerturb

用户可以直接提问：

* Which paper uses reinforcement learning?
* Which paper focuses on backdoor attacks?
* Compare FedAA and ClusterGuard

系统会自动检索相关论文内容并生成回答。

---

## 项目 Pipeline

```text
PDF Papers
↓
PDF Parsing (PyPDF)
↓
Document Text
↓
Chunking
↓
Chunks
↓
Embedding
↓
Vector Embeddings
↓
FAISS Vector Database
↓
Query Rewriting
↓
Semantic Retrieval
↓
Top-K Chunks
↓
Context Construction
↓
DeepSeek LLM
↓
Answer + Citation
```

---

## 实现功能

### 1. Multi-PDF Knowledge Base

支持同时加载多篇论文：

```python
pdf_files = [
    "FedAA.pdf",
    "ClusterGuard.pdf",
    "HealSplit.pdf",
    "BAPerturb.pdf"
]
```

所有论文统一构建知识库。

---

### 2. Chunking

长论文自动切分：

```python
chunk_size = 500
overlap = 100
```

采用 Overlap 机制减少信息断裂问题。

---

### 3. Embedding

使用模型：

```python
sentence-transformers/all-MiniLM-L6-v2
```

将文本转换为 384 维向量：

```text
Text
↓
Embedding
↓
384-d Vector
```

---

### 4. FAISS Vector Search

使用：

```python
faiss.IndexFlatL2()
```

建立向量索引。

支持：

```text
Query
↓
Embedding
↓
Top-K Similar Chunks
```

语义检索。

---

### 5. Query Rewriting

引入 DeepSeek 对用户问题进行改写：

例如：

```text
what is fedaa
```

改写为：

```text
FedAA proposed method main idea algorithm
```

提高检索准确率。

---

### 6. Source Tracking

每个 Chunk 保存来源信息：

```python
{
    "source": "FedAA.pdf",
    "chunk": "..."
}
```

检索后能够追踪答案来源。

---

### 7. Citation

回答同时给出证据来源：

```text
Source:
FedAA.pdf | chunk_id:25
FedAA.pdf | chunk_id:26
FedAA.pdf | chunk_id:28
```

提高回答可解释性。

---

## 学到的核心概念

### RAG

RAG 本质：

```text
Retrieval
+
Generation
```

而不是重新训练大模型。

---

### Embedding

文本可以转换为高维向量。

语义相近的文本：

```text
距离更近
```

---

### FAISS

FAISS 用于高效向量检索：

```text
Query Vector
↓
Similarity Search
↓
Top-K Results
```

---

### Query Rewriting

用户问题不一定适合检索。

通过 LLM 先改写 Query，可以提高召回质量。

---

### Citation

完整 RAG 应包含：

```text
Question
↓
Retrieval
↓
Evidence
↓
Answer
```

而不仅仅是生成答案。

---

## 项目技术栈

* Python
* PyPDF
* NumPy
* Sentence Transformers
* FAISS
* OpenAI SDK
* DeepSeek API

---

## 当前项目完成内容

✅ Multi-PDF Parsing

✅ Chunking + Overlap

✅ Embedding

✅ FAISS Retrieval

✅ Query Rewriting

✅ Top-K Search

✅ Source Tracking

✅ Citation

✅ Multi-Paper Question Answering

---

## 项目收获

通过本项目理解了完整 RAG 系统的数据流：

```text
PDF
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
LLM
↓
Answer
```

并进一步掌握：

* 多论文知识库构建
* Query Rewrite
* Retrieval Optimization
* Citation Mechanism
* Research Assistant 基础实现

```
```
