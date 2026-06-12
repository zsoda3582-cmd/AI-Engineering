# Mini Code Agent

一个基于 LLM + Tool Calling + Agent Loop 的最小代码分析 Agent，用于理解 AI Agent 的核心工作流程，并能够对真实 Python 项目进行代码检索与分析。

## 项目目标

本项目参考 Claude Code、Cursor 等 Code Agent 的基本思想，从零实现一个最小版本的代码智能体（Mini Code Agent），重点理解：

* LLM Planner（规划）
* Tool Calling（工具调用）
* Observation（工具观察结果）
* History（历史记忆）
* Agent Loop（多轮决策循环）

而不是单纯调用现成框架。

---

## 项目架构

```text
User Question
        │
        ▼
   LLM Planner
        │
        ▼
   Tool Calling
   ┌──────────────┐
   │  grep_code   │
   │  read_file   │
   │  list_files  │
   └──────────────┘
        │
        ▼
   Observation
        │
        ▼
     History
        │
        ▼
   LLM Planner
        │
        ▼
   Final Answer
```

---

## 已实现功能

* ✅ 根据自然语言问题自动规划下一步操作（Planner）
* ✅ 使用 `grep_code` 搜索相关代码位置
* ✅ 自动选择并读取相关文件（`read_file`）
* ✅ 支持查看项目文件列表（`list_files`）
* ✅ 支持多轮 Agent Loop（Plan → Tool → Observation → Re-plan）
* ✅ 支持 History 记录与上下文传递
* ✅ 支持简单的关键词改写（Fallback Search）
* ✅ 支持多文件读取与代码总结

---

## 支持的工具（Tools）

| 工具                | 功能          |
| ----------------- | ----------- |
| `grep_code`       | 根据关键词搜索代码   |
| `read_file`       | 读取指定文件内容    |
| `list_files`      | 列出项目文件      |
| `generate_answer` | 根据上下文生成最终回答 |

---

## 项目测试

### Demo 项目测试

* `login 功能在哪里？`
* `login 有什么功能？`
* `项目里有哪些文件？`
* `auth.py 里面写了什么？`

### 真实项目测试（Paper-RAG）

* `DeepSeek API 是在哪里调用的？`
* `Embedding 是在哪里生成的？`
* `FAISS 是怎么建立的？`
* `Query 是如何在 FAISS 中搜索的？`

Agent 可以自动完成：

> 搜索代码 → 读取相关文件 → 总结实现逻辑 → 返回答案。

---

## 技术栈

* Python 3
* OpenAI SDK（兼容 DeepSeek API）
* DeepSeek Chat
* JSON
* Agent Loop / Tool Calling

---

## 后续可扩展方向

* 更智能的关键词改写（Query Rewrite）
* Search Ranking 优化
* 更多代码工具（Find File / Glob）
* 多项目代码仓库分析
* 支持更复杂的 Agent Workflow

---

> 本项目主要用于学习和实践 AI Agent 的核心架构，通过实现最小 Code Agent 来理解现代 AI 应用工程中的 Planner、Tool Calling 和 Agent Loop 机制。
