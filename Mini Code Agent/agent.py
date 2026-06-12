#=====================
#Agent是项目的大脑，它拿到main.py交给它的问题之后，决定调用tools.py中的哪个工具，拿到返回的结果后，再继续思考，重复此过程，最后回答
from tools import grep_code,read_file,list_files,find_file
import openai
from openai import OpenAI
import json #一种统一的数据包装格式。严格来说这是 Python 的 dict，但长得和 JSON 一样
PROJECT_ROOT = "data/paper_rag_project"

client = OpenAI(
    api_key = "sk-decd220c2a684e8bb413a91b4f5df856",
    base_url = "https://api.deepseek.com"
)

def choose_tool(question):
    question = question.lower()
    if "where" in question or "在哪" in question:
        return "grep"
    if "how" in question or "怎么" in question:
        return "read"
    return "grep"

def plan_action(question):
    prompt = f"""
    You aer a code agent planner.
    Given a user question,decide which tool to user and what keyword to search.

    Avaliable tools:
    1.list_files:list all files in the project.
    2.grep_code:search code files by keyword

    For now,you should usually choose gred_code first.
    
    Return ONLY valid JSON,no explanation.

    Format:
    {{
        "tool":"grep_code",
        "keyword":"login
    }}

    User question:
    {question}
    """

    response = client.chat.completions.create( #调用 DeepSeek
        model = "deepseek-chat",
        messages = [
            {
                "role":"user",
                "content":prompt
            }
        ]
    )
    plan_text = response.choices[0].message.content.strip() #取模型返回值
    try:
        plan = json.loads(plan_text)
    except:
        plan = {
            "tool":"grep_code",
            "keyword":question
        }
    return plan

def plan_read_file(question,observation):
    prompt = f"""
    You are a code agent.
    The user asked:
    {question}
    You searched the code and got this observation:
    {observation}
    Now decide which single file should be read to answer the question beat.
    Return ONLY valid JSON,no explanation.
    Format:
    {{
        "file_path":"data/sample_project/auth.py"
    }}
    """
    response = client.chat.completions.create(
            model = "deepseek-chat",
            messages = [
                {
                    "role":"user",
                    "content":prompt
                }
            ]
    )
    plan_text = response.choices[0].message.content.strip()
    try:
        return json.loads(plan_text)
    except:
        return{
            "file_path":""
        }

def build_file_context(file_paths):
    all_file_content = ""
    for file_path in file_paths:
        content = read_file(file_path)
        all_file_content += f"""
        ====================
        File:{file_path}
        ====================
        {content}
        """
    return all_file_content

def build_search_observation(results):
    if len(results) == 0:
        return "没有找到相关代码"
    observation = "搜索结果：\n"
    for item in results:
        observation += f"-{item['file']} | line{item['line']}:{item['content']}\n"
    return observation

def get_related_files(results,max_files = 3):
    related_files = []
    for item in results:
        file_path = item['file']
        if file_path not in related_files:
            related_files.append(file_path)
    return related_files[:max_files]

def plan_fallback_keyword(question,old_keyword):
    prompt = f"""
    You are a code search assistant.
    The user's question is:
    {question}
    The previous waerch keyword was:
    {old_keyword}
    But it found no code.
    Please suggest a better short code keyword for searching.
    Return ONLY valid JSON,no explanation.
    
    Format:
    {{
        "keyword":"user"
    }}
    """
    response = client.chat.completions.create(
        model = "deepseek-chat",
        messages = [
            {
                "role":"user",
                "content":prompt
            }
        ]
    )
    #response 是一个很大的对象,response.choices[0]就是取第一个回答,.message取回答对象,.content取该对象回答真正的文本，该文本是字符串，.strip()用于把首尾空格、换行去掉
    #最后得到：plan_text = '{"keyword":"user_info"}'
    plan_text = response.choices[0].message.content.strip()
    try:
        return json.loads(plan_text) #把长得像 JSON 的字符串，变成 Python 字典（dict），并返回
    except:
        return {"keyword":old_keyword}

def format_history(history):
    if len(history) == 0:
        return "No previous step"
    text = ""

    for i,item in enumerate(history,start=1):
        text += f"\nStep{i}:\n"
        text += f"Tool:{item.get('tool','')}\n"

        if "keyword" in item:
            text += f"Keyword:{item['keyword']}\n"
        if "file_path" in item:
            text += f"File:{item['file_path']}\n"
        text += f"Observation:\n{item.get('observation','')}\n"
    return text


def plan_next_action(question,history):
    prompt = f"""
    You are a code agent.
    You need to answer the user's question by using tools.
    Avalibale tools:
    1.grep_code:search code by keyword.
    2.read_file:read a  specific file.
    3.final_answer:use this when you have enough information to answer.
    Keyword rules:
    - Use short code keywords, not full natural language phrases.
    - For API call questions, prefer keywords like: client, chat, completions, create, api_key, base_url, OpenAI.
    - For embedding questions, prefer keywords like: embedding, encode, model.
    - For FAISS questions, prefer keywords like: faiss, IndexFlatL2, index.add, index.search.

    User question:
    {question}

    History:
    {format_history(history)}

    Return ONLY valid JSON,no explanaton.
    Exanples:
    Search code:
    {{
        "tool":"grep_code",
        "keyword":"login"
    }}

    Read file:
    {{
        "tool":"read_file,
        "file_path":"data/sample_project/auth.py"
    }}

    Final:
    {{
        "tool":"final_answer
    }}
    """
    response = client.chat.completions.create(
        model = "deepseek-chat",
        messages = [
            {
                "role":"user","content":prompt
            }
        ]
    )
    plan_text = response.choices[0].message.content.strip()
    try:
        return json.loads(plan_text)
    except:
        return {
            "tool":"grep_code",
            "keyword":question
        }


#初始化Deepseek客户端
def generate_answer(file_content,question): #负责思考怎么利用这些信息回答用户，是大脑，非工具，所以不放在tools.py里，而在agent大脑中
    """
    给定文件内容和用户问题，调用Deepseek API生成回答
    """
    prompt = f"""
    You are a helpful programming assistant.
    Based on the following code snippet,answer the user's question.

    Code:
    {file_content}

    Question:
    {question}

    Answer:
    """
    response = client.chat.completions.create(
        model = "deepseek-chat",
        messages = [
                {"role":"system","content":"You aer a healpfuo code assistant."},
                {"role" : "user","content":f"Question:{question}\n{file_content}"}
        ]
    )
    return response.choices[0].message.content.strip()

def extract_keyword(question):
    question = question.lower()
    keywords = [
        "login",
        "logout",
        "user",
        "auth",
        "read",
        "file"
    ]
    for keyword in keywords:
        if keyword in question:
            return keyword
    return question


#最新版run_agent_loop
def run_agent_loop(question):
    history = []
    max_step = 3

    for step in range(max_step):
        print(f"\n ========Step {step + 1} =========")

        action = plan_next_action(question,history)
        tool = action.get("tool","grep_code")
        print("Agent决定：",action)

        if tool == "grep_code":
            keyword = action.get("keyword",question)
            results = grep_code(PROJECT_ROOT,keyword)
            observation = build_search_observation(results)

            print("\n ====Observation:grep_code ====\n",observation)

            history.append({
                "tool":"grep_code",
                "keyword":keyword,
                "observation":observation
            })

        elif tool == "read_file":
            file_path = action.get("file_path","")
            content = read_file(file_path)
            observation = f"""
            读取文件：
            {file_path}
            文件内容：
            {content}
            """

            print("\n ====Observation:read_file ====\n",observation)

            history.append({
                "tool":"read_file",
                "file_path":file_path,
                "observation":observation
            })

        elif tool == "final_answer":
            context = f"""
            User question:
            {question}
            History:
            {history}
            """
            return generate_answer(context,question)

        else:
            history.append({
                "tool":"unknown",
                "observation":f"未知工具：{tool}"
            })

    context = f"""
    User question:
    {question}
    History:
    {format_history(history)}
    """
    return generate_answer(context,question)

#第二版run_agent
# def run_agent(question):
#     #1.Planner:让LLM决定先搜什么
#     plan = plan_action(question) "data"list_files

#     tool = plan.get("tool","grep_code") 
#     #去找 tool的值，因为正常格式是"tool":"grep_code"，那么此时plan["tool"]得到”grep_code“；如果找不到，默认给我 grep_code
#     #等价于：
#     # if "tool" in plan:
#     #     tool = plan["tool"]
#     # else:
#     #     tool = "grep_code"
    
#     keyword = plan.get("keyword",question)

#     #如果用户输入的是文件名，直接定位并读取
#     if ".py" in keyword:
#         file_path = find_file("data",keyword)

#         if file_path is not None:
#             print("\nAgent发现这是一个文件名，直接定位文件：\n",file_path)

#             content = read_file(file_path)
#             #Observation 是 Agent 每次工具调用后看到的新信息
#             observation = f""" 
#             文件路径：\n{file_path}
#             文件内容：\n{content}
#             """
#             answer = generate_answer(observation,question)
#             return answer

#     print(f"Agent选择工具:{tool}")
#     print(f"Agent选择关键词:{keyword}")

#     if tool == "list_files":
#         files = list_files("data")
#         observation_1 = "项目文件列表：\n"

#         for file_path in files:
#             observation_1 += f"-{file_path}\n"
#         print("\n === Observation_1:list_files ===\n",observation_1)

#         answer = generate_answer(observation_1,question)
#         return answer


#     #2.mini版Agent Loop：目前只允许grep_code
#     results = grep_code("data",keyword)

#     if len(results) == 0:
#         print("\n第一次搜索没有结果，Agent尝试换一个关键词...")

#         fallback_plan = plan_fallback_keyword(question,keyword)
#         fallback_keyword = fallback_plan.get("keyword",keyword)
#         #去找 "keyword" 这个键，如果没有，就返回后面的默认值 keyword
        
#         print("fallback关键词:",fallback_keyword)
#         results = grep_code("data",fallback_keyword)

#     #3.把工具整理成Observation_1
#     observation_1 = build_search_observation(results)
#     print("\n=== Observation_1:grep_code ===")
#     print(observation_1)

#     #4.根据搜索结果，决定读哪个文件
#     #最多读取前3个文件
#     max_files = 3
#     related_files = get_related_files(results,max_files)

#     print(f"\nAgent决定读前{len(related_files)}个文件:")
#     for file_path in related_files:
#         print("-",file_path)

#     #5.读取所有相关文件
#     all_file_content = build_file_context(related_files)
#     observation_2 = f"""
#     读取到的相关文件内容：
#     {all_file_content}
#     """
#     print("\n === Observation_2:Multi_file_read ===")
#     print(observation_2)

#     context = f"""
#     User question:
#     {question}
#     observation_1:
#     {observation_1}
#     observation_2:
#     {observation_2}
#     """
#     answer = generate_answer(context,question)
#     return answer
#=======================================================================================
     #初始版决定读哪个文件（只读一个文件）
    # read_plan = plan_read_file(question,observation_1)
    # file_path = read_plan.get("file_path","")
    # print("\nAgent决定读取文件：",file_path)
    # file_content = read_file(file_path)
    
    # observation_2 = f"""
    # 读取文件:
    # {file_path}
    # 文件内容：
    # {file_content}
    # """
    # print("\n===Observation_2:read_file ===")
    # print(observation_2)


    #6.Final Context = 把所有 Observation 汇总起来,是 Agent 最终交给 LLM 的所有信息打包
    #它其实就是：Question + Observation_1 + Observation_2

    # evidence = ""
    # all_content = ""

    # for item in results:
    #     file_path = item["file"]
    #     line = item["line"]
    #     match_line = item["content"]

    #     evidence += f"-{file_path} line{line} |{match_line}\n"

    #     content = read_file(file_path)
    #     all_content += f"\n\n==== File:{file_path} ====\n"
    #     all_content += content
    
    # print("\n====Evidence====",evidence)
    # #context = f"""...""" 是多行字符串，三引号意思是我要写很多行， f"""...""" 意思是我要写很多行，而且里面还能自动替换变量
    # context = f""" 
    # Evidence:
    # {evidence}

    # Code Context:
    # {all_content}
    # """
    # answer = generate_answer(context,question)
    # return answer



#================================
#初始版run_agent
#=================================
# def run_agent(question):
#     # 先用grep找相关文件
#     # results = grep_code("data",question)

#     keyword = extract_keyword(question)
#     tool = choose_tool(question)
#     print(f"Agent选择工具:{tool}")
#     print(f"Agent选择关键词:{keyword}")

#     if tool =="grep":
#         results = grep_code("data",keyword)
#     else:
#         results = grep_code("data",keyword)

#     if len(results) == 0:
#         return "没有找到相关代码"
    
#     #读取所有相关文件内容
#     all_content = ""
#     for item in results:
#         file_path = item["file"] #grep_code()原来输出str,升级后输出[{file,line,content}],所以run_agent()必须同步修改item["file"]
#         content = read_file(file_path)
#         all_content += f"\n\n==== File:{file_path}====\n"
#         all_content += content
    
#     #调用generate_answer，让Agent根据所有文件生成回答
#     answer = generate_answer(all_content,question)
#     return answer




#=================================
#初始版：只读取第一个文件
#=================================
    # print("找到相关文件:")
    # for file_path in results:
    #     print("-",file_path)
    
    # print("\n读取第一个文件：")
    # file_path = results[0]
    # content = read_file(file_path)
    # print("-"*50)

    # print(content[:500]) #打印第一个文件的前500个字符
    # print("-"*50)

    # # 调用AI生成初步回答
    # answer = generate_answer(content,question)
    # return answer