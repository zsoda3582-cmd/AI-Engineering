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
    api_key = "sk-91188cfc334342fea22774a09bb0233d",
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
def retrieve(query,top_k,source_filter=None):
    rewritten_query = rewritten_text(query)
    print(f"改写后的检索问题：{rewritten_query}")
    print("-"*50)

    query_embedding = model.encode(rewritten_query)
    query_vector = query_embedding.reshape(1,-1)
    query_embedding_2d = np.array([query_embedding])

    # =========================
    # Metadata Filter
    # =========================
    if source_filter is None: #不做过滤，583个chunk全部参与检索
        candidate_indics = list(range(len(all_chunks)))
    else:
        candidate_indics = []

        for idx,item in enumerate(all_chunks):
            if item["source"] == source_filter:
                candidate_indics.append(idx)

    results = []
    if source_filter is None:
        distances,indics = index.search(query_embedding_2d,top_k)
        for rank,i in enumerate(indics[0],start = 1):
            distance = distances[0][rank-1]
            results.append(i,distance)
    else:
        for idx in candidate_indics:
            chunk_vector = chunk_embeddings[idx]
            distance = np.linalg.norm(query_embedding - chunk_vector)
            results.append((idx,distance))
        results.sort(key = lambda x:x[1])
        results = results[:top_k]
    retrieved_chunks = []
    retrieved_source = []

    print("\n===== Top-K Retrieved Chunks =====")

    for rank,(i,distance) in enumerate(results,start = 1):
        source = all_chunks[i]["source"]
        chunk = all_chunks[i]["chunk"]

        print(f"\nTop-{rank} | source:{source} | chunk_id:{i} | distance:{distance:.4f}")
        print(chunk[:200])
        print("-"*50)

        retrieved_chunks.append(chunk)
        retrieved_source.append(
            f"{source} | chunk_id:{i}"
        )

    



    # distances,indices = index.search(query_embedding_2d,top_k)
    # retrieved_chunks = []
    # retrieved_source = []
    # print("\n===== Top-K Retrieved Chunks =====")
    # for rank,i in enumerate(indices[0],start=1): #遍历刚刚筛选出来的 三个范数距离最近的向量
    #     source = all_chunks[i]["source"]
    #     chunk = all_chunks[i]["chunk"]

    #     print(f"\nTop-{rank}|source:{source}|chunk_id:{i} | distance:{distances[0][rank-1]:.4f}")
    #     print(chunk[:200])
    #     print("-"*50)

    #     retrieved_chunks.append(chunk)
    #     retrieved_source.append(
    #         f"{source} | chunk_id:{i}"
    #     )
    context = "\n\n".join(retrieved_chunks)
    source_info = "\n".join(retrieved_source)
    return context,source_info

# =========================
# 构造 RAG Prompt
# =========================
def generate_answer(query,context,source_info):
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
    return response.choices[0].message.content

def classify_task(query):
    query_lower = query.lower()
    if "compare" in query_lower and "and" in query_lower:
        return "compare"
    return "common_qa"

def handle_compare(query,top_k):
    query_lower = query.lower()
    temp = query_lower.replace("compare","").strip()
    paper1,paper2 = temp.split("and")
    paper1 = paper1.strip()
    paper2 = paper2.strip()
    print("比较对象A:",paper1)
    print("比较对象B:",paper2)

    context1,source_info1 = retrieve(paper1,top_k,"data/FedAA.pdf")
    context2,source_info2 = retrieve(paper2,top_k,"data/ClusterGuard.pdf")

    compare_prompt = f"""
    You are a research assistant.
    Please compare the following two papers based on the provided contexts.
    paper A:{paper1}
    context A:
    {context1}
    Evidence A:
    {source_info1}

    paper B:{paper2}
    context B:
    {context2}
    Evidence B:
    {source_info2}

    Please compare them from:
    1. Research problem
    2. Main method
    3. Key technical idea
    4. Strengths
    5. Limitations
    Answer in a clear table if possible.
    """
    response = client.chat.completions.create(
        model = "deepseek-chat",
        messages = [
            {
                "role":"user","content":compare_prompt
            }
        ]
    )
    return response.choices[0].message.content

while True:
    query = input("请输入您的问题（输入exit退出）：")
    if query.lower() == "exit":
        break
    type_task = classify_task(query)
    print("任务类型：",type_task)
    top_k = int(input("请输入top_k（建议3或5）："))

    if type_task == "common_qa":
        context,source_info = retrieve(query,top_k)

        answer = generate_answer(query,context,source_info)
        print("===== AI Answer =====")
        print(answer)
    else:
        answer = handle_compare(query,top_k)
        print("===== AI Answer =====")
        print(answer)
    
