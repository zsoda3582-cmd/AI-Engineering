#=====================
#tools.py 是 Agent 的工具箱，Agent 自己不会干活，它只会调用自己拥有的模块功能
#=====================
import os

IGNORE_DIRS = ["__pycache__",".git","venv",".venv","node_modules"]
ALLOWED_EXTENSIONS = [".py",".txt",".md",".json",".yaml",".yml"]

def should_ignore(file_path):
    # 如果在垃圾文件夹里 → 忽略
    # 如果后缀不是我们关心的 → 忽略
    # 否则 → 保留
    for ignore_dir in IGNORE_DIRS:
        if ignore_dir in file_path:
            return True
    _,ext = os.path.splitext(file_path)
    if ext not in ALLOWED_EXTENSIONS:
        return True
    return False

def list_files(root_path):
    results = []
    for root,dirs,files in os.walk(root_path): #os.walk:去文件夹里挨个查看所有文件
        for file in files:
            file_path = os.path.join(root,file)
            if should_ignore(file_path):
                continue
            results.append(file_path)
    return results

def find_file(root_path,target_name):
    for root,dirs,files in os.walk(root_path):
        for file in files:
            file_path = os.path.join(root,file)

            if should_ignore(file_path):
                continue
                
            if file.lower() == target_name.lower():
                return file_path
    return None

def grep_code(root_path,keyword): #搜索某个关键词在哪些文件出现
    results = []

    for root,dir,files in os.walk(root_path):
        for file in files:
            file_path = os.path.join(root,file)
            if should_ignore (file_path):
                continue

            try:
                with open(file_path,"r",encoding = "utf-8") as f:
                    lines = f.readlines()

                for line_num,line in enumerate(lines,start = 1):
                    if keyword.lower() in line.lower():
                        score = 1

                        #函数定义优先
                        if f"def {keyword}" in line:
                            score = 3
                        #import次之
                        elif keyword in line and "import" in line:
                            score = 2

                        results.append({
                            "file":file_path,
                            "line":line_num,
                            "content":line.strip(),
                            "score":score
                        })
            except:
                pass
    results.sort(
        key = lambda item:item["score"],
        reverse = True
    )
    return results

def read_file(file_path):
    try:
        with open(file_path , "r" , encoding = "utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        print("读取文件失败:",e)
        return ""