from pypdf import PdfReader #PDF读取器
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from openai import OpenAI

pdf_files = [
    "data/FedAA.pdf",
    "data/BAPerturb.pdf",
    "data/ClusterGuard.pdf",
    "data/HealSplit.pdf"
]
all_documents = []

for pdf_file in pdf_files:
    reader = PdfReader(pdf_file)
    document = ""
    for page in reader.pages:
        document += page.extract_text()
    all_documents.append(
        {
            "source":pdf_file,
            "text":document
        }
    ) 
print(len(all_documents))
for doc in all_documents:
    print(doc["source"])
print("-"*50)

# =========================
# 做chunk切分
# =========================
def chunk_text(text,chunk_size = 500,overlap = 100):
    chunks = []
    step = chunk_size - overlap
    for i in range(0,len(text),step):
        chunk = text[i:i+chunk_size]
        chunks.append(chunk)
    return chunks
all_chunks = []
for doc in all_documents:
    chunks = chunk_text(doc["text"])
    for chunk in chunks:
        all_chunks.append(
            {
                "source":doc["source"],
                "chunk":chunk
            }
        )
print("总chunk数量：",len(all_chunks))
print(all_chunks[0]["source"])
print(all_chunks[0]["chunk"][:200])
print("-"*50)


# =========================
# 加载Embedding模型
# =========================
model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)
#现在all_chunks是字典，但embedding模型吃不了dict结构，只吃字符列表
#所以先提取文本
chunk_texts = []
for item in all_chunks:
    chunk_texts.append(item["chunk"])

chunk_embeddings = model.encode(chunk_texts)
print("type(chunk_embeddings):",type(chunk_embeddings))
print("chunk_embeddings.shape:",chunk_embeddings.shape)
print("-"*50)

# =========================
# 建立FAISS索引
# =========================
dimension = chunk_embeddings.shape[1] #shape[1]是每条embedding的长度，faiss首先要知道每条存进了的向量维度是多少，不然没办法建立索引
index = faiss.IndexFlatL2(dimension) #创建一个以后可以用 L2 距离搜索的FAISS索引结构，这个索引用L2范数距离来做相似向量搜索
#Index:索引结构 Flat：暴力精确搜索 dimension：每个向量的维度，比如384
index.add(chunk_embeddings)
print("FAISS中向量数量:",index.ntotal) #index不是普通python list，不支持python的len()函数，它是FAISS自己实现的对象
print("-"*50)

# =========================
# 调用 DeepSeek API (通过API远程调用大模型)
# =========================
client = OpenAI( #client是DeepSeek客户端
    api_key = "sk-1c28d25e2791468ea6d416a6bc631232",
    base_url = "https://api.deepseek.com" #API服务器地址，如果没有base_url，OpenAI SDK 默认会连https://api.openai.com（OpenAI 官方服务器—）
)

# =========================
# Rewritten 模块
# =========================
def rewritten_text(text):
    rewrite_prompt = f"""
    Rewrite the user question into a better search query for retrieving information from this paper.

    Important rules:
    1.do not expand acronyms or abbreviations.
    2.keep technical terms exactly as written,such as FedAA.
    3.add useful academic searcj terms like "main idea","proposed method","algorithm","reinforcement learning","aggregation" only when appropriate.
    4.Only output the rewritten query.

    user_question:
    {text}
    """
    response = client.chat.completions.create(
        model = "deepseek-chat",
        messages = [
            {
                "role":"user","content":rewrite_prompt
            }
        ]
    )
    return response.choices[0].message.content.strip()

# =========================
# 用户提问query 
# =========================
while True:
    query = input("请输入您的问题（输入exit退出）：")
    if query.lower() == "exit":
        break
    rewritten_query = rewritten_text(query)
    print(f"改写后的检索问题：{rewritten_query}")
    print("-"*50)

    query_embedding = model.encode(rewritten_query)
    query_embedding_2d = np.array([query_embedding])

    top_k = int(input("请输入top_k（建议3或5）:"))
    distances,indices = index.search(query_embedding_2d,top_k)

    # print(f"检索到的chunk编号：{indices}距离：{distances}")
    # print("-"*50)

    # =========================
    # 构造 context
    # =========================
    retrieved_chunks = []
    retrieved_source = []
    print("\n===== Top-K Retrieved Chunks =====")
    for rank,i in enumerate(indices[0],start=1): #遍历刚刚筛选出来的 三个范数距离最近的向量
        source = all_chunks[i]["source"]
        chunk = all_chunks[i]["chunk"]
        
        print(f"\nTop-{rank}|source:{source}|chunk_id:{i} | distance:{distances[0][rank-1]:.4f}")
        print(chunk[:200])
        print("-"*50)

        retrieved_chunks.append(chunk)
        retrieved_source.append(
            f"{source} | chunk_id:{i}"
        )
    context = "\n\n".join(retrieved_chunks)
    source_info = "\n".join(retrieved_source)

    # =========================
    # 构造 RAG Prompt
    # =========================
    prompt = f"""
    You are a paaper reading assitant.
    Please answer the question based on the paper context below.
    paper context:{context}
    Question:{query}
    Please answer the question.
    At the end,cite the evidence sources provided.
    Evidence Sources:
    {source_info}
    Answer:
    """

    response = client.chat.completions.create( #给大模型发请求：client是DeepSeek客户端，chat表示聊天模型，completions表示文本补全，create()表示发起一次请求，总结：向聊天大模型发起一次文本生成请求
        model = "deepseek-chat",
        messages = [
            {"role":"user","content":prompt} #OpenAI/DeepSeek API 的字段名固定是这两个：role和content
        ]
    )
    answer = response.choices[0].message.content

    print("===== AI Answer =====")
    print(answer)
