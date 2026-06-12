# 程序入口
#=====================
#main.py 是 大傻子，它只会把用户输入的问题交给Agent处理，再把 Agent返回的答案打印出来
#=====================
from tools import list_files,grep_code,read_file,find_file
from agent import run_agent_loop


while True:
    question = input("请输入您的问题（输入exit退出）：")
    if question.lower() == "exit":
        break
    answer = run_agent_loop(question)
    print("\n======= AI answer =======")
    print(answer)
    print("=" *50)

