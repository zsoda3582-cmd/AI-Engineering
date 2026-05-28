from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import faiss

# 加载embedding 模型
model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

# # =========================
# # 小型知识库
# # =========================
# documents = [
#     "FedAA uses reinforcement learning for aggregation",
#     "BAPerturb is a boundary attack in federated learning",
#     "LSTM is good at sequence modeling",
#     "Transformers use attention mechanism",
#     "ClusterGuard defends against malicious clients"
# ]

# =========================
# 长文档
# =========================
document = """
Machine learning is a field of artificial intelligence.

Deep learning is a subset of machine learning.

Transformers use attention mechanism.

RAG combines retrieval and generation.

FAISS is used for vector search.
"""
# =========================
# Chunk 切分
# =========================
chunks = document.split("\n\n")
print("chunks:",chunks)


# =========================
# 知识库转 embedding
# =========================
# doc_embeddings = model.encode(documents)
chunk_embeddings = model.encode(chunks)

# =========================
# 建立 FAISS 向量索引
# =========================
dimension = chunk_embeddings.shape[1] #chunk_embeddings的shape 大概是(5, 384)，取shape[1]，即可得到384，即每条embedding的向量维度。FAISS需要知道存进来的向量每个长度是多少，否则它不知道怎么建索引
index =faiss.IndexFlatL2(dimension)   #创建一个向量数据库 index，用来存 embedding。IndexFlatL2是一种用距离找相似向量的方式
index.add(chunk_embeddings)           #把 embedding 存进 FAISS
print("FAISS中存入的向量数量:",index.ntotal)



# =========================
# 用户问题
# =========================
query = "What model uses attention"
query_embedding = model.encode(query)

# =========================
# 用 FAISS 检索 Top-K
# =========================
top_k = 3
query_embedding_2d = np.array([query_embedding])
distances,indices = index.search(query_embedding_2d,top_k)
print("query_embedding:",query_embedding.shape)
print("query_embedding_2d:",query_embedding_2d.shape)
print("FAISS检索结果:")
print("distances:",distances)
print("indics:",indices)

# =========================
# 取回检索到的 chunks
# =========================
retrieved_chunks = []
for i in indices[0]:
    retrieved_chunks.append(chunks[i])
print("检索出来的chunks：")
print(retrieved_chunks)

# =========================
# 拼接 context
# =========================
context = "\n".join(retrieved_chunks)
print("context:",context)

# =========================
# 查看所有数据形态
# =========================

print("\n===== 数据流查看 =====\n")

print("1.document:")
print(type(document))

print("\n2.chunks:")
print(type(chunks))
print(chunks)

print("\n3.chunk_embeddings:")
print(type(chunk_embeddings))
print(chunk_embeddings.shape)

print("\n4.query_embedding:")
print(type(query_embedding))
print(query_embedding.shape)

print("\n5.query_embedding_2d:")
print(type(query_embedding_2d))
print(query_embedding_2d.shape)

print("\n6.indices:")
print(type(indices))
print(indices.shape)
print(indices)

print("\n7.retrieved_chunks:")
print(type(retrieved_chunks))
print(retrieved_chunks)

print("\n8.context:")
print(type(context))
print(context)

# =========================
# 构造 RAG Prompt
# =========================
prompt = f"""
You are an AI assistant.
Known information:
{context}
QuestionL
{query}
Answer:
"""
print("\n======RAG Prompt=====\n",prompt)








# =========================
# 用 cosine-similarity 检索 Top-K
# =========================
# similarities = cosine_similarity(
#     [query_embedding],
#     chunk_embeddings
# )
# print(similarities)

# # =========================
# # Top-K 检索
# # =========================
# top_k = 3

# # 排序
# sorted_indices = np.argsort(similarities[0])[::-1] #[::-1]反转，argsort默认从小到大，我们希望从大到小
# #cosine_similarity(）后的结构默认是二维矩阵，矩阵中第一行表示 A的第1条语句和 B的所有语句之间的相似度，此处的问题query只有一条，所以A只有1条，故此矩阵是1*5的结构

# #取前3个
# top_indices = sorted_indices[:top_k]

# print("top_k个检索结果：")
# for i in top_indices:
#     print(f"相似度：{similarities[0][i]:.4f}")
#     print(chunks[i])
#     print()
