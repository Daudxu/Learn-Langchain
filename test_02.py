import os
from typing import List, Annotated, TypedDict
# from operator import itemgetter # itemgetter 在这个版本中不再需要，可以删除此行
from operator import add # <-- 【最终修正】导入 Python 内置的 operator.add

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

# 引入 LangGraph 核心组件
from langgraph.graph import StateGraph, END

# 引入 dotenv 来加载 .env 文件中的环境变量
from dotenv import load_dotenv

# --- 1. 加载环境变量 ---
load_dotenv()

# --- 2. 配置你的大模型 (LLM) ---
# 从环境变量中获取模型配置
API_BASE = os.getenv("API_BASE")
API_KEY = os.getenv("API_KEY") # 确保这个变量名和 .env 文件一致
BASE_MODEL = os.getenv("BASE_MODEL")

print(f"模型 API 基础 URL: {API_BASE}")
print(f"模型 API 密钥: {API_KEY}") # 注意：在生产环境中不要打印敏感信息
print(f"模型名称: {BASE_MODEL}")

llm = ChatOpenAI(
    base_url=API_BASE,
    api_key=API_KEY,
    model=BASE_MODEL,
    temperature=0.1, # 保持较低温度，让回复更稳定
    max_tokens=512,  # 限制最大 token 数
    streaming=True   # 启用流式输出，尽管在这个简单 demo 中没有直接体现在控制台
)

# --- 3. 定义 LangGraph 的“共享记忆区” (State) ---
# TypedDict 帮助我们定义这个共享记忆区里会有哪些东西
class AgentState(TypedDict):
    # 使用 Python 内置的 operator.add 作为 reducer，它会简单地将列表相加（追加）
    messages: Annotated[List[BaseMessage], add] # 聊天记录，每次都会追加新消息
    user_name: str # 记住用户的名字

# --- 4. 定义 LangGraph 的“AI 专家” (Node) ---
# 这个函数就是一个节点，它接收当前“共享记忆区”的状态，并返回更新后的状态
def chatbot_node(state: AgentState):
    print("\n--- 机器人节点开始处理 ---")
    messages = state["messages"]
    user_name = state.get("user_name", "朋友") # 如果还没有名字，就用“朋友”

    # 找到最新的用户消息，用于 prompt 中的 {input}
    latest_user_message = ""
    # 确保 messages 列表非空，并且最新消息是 HumanMessage 类型
    if messages and isinstance(messages[-1], HumanMessage):
        latest_user_message = messages[-1].content
    
    # 4.1 准备 Prompt 模板
    # MessagesPlaceholder(variable_name="messages") 会自动放入所有聊天记录
    # {input} 会放入最新的用户消息
    # 我们在 system prompt 中加入 user_name，让模型知道并记住它
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"你是一个友好的AI助手"),
        MessagesPlaceholder(variable_name="messages"), # 聊天历史的占位符
        ("human", "{input}") # 最新用户输入的占位符
    ])

    # 4.2 构建 LCEL Chain (作为节点内部逻辑)
    # 这个链会处理完整的聊天记录和最新的用户输入
    full_chain = (
        prompt
        | llm # 使用我们自定义配置的 llm
        | StrOutputParser()
    )

    # 调用链，获取 AI 的回复
    ai_response_content = full_chain.invoke({"messages": messages, "input": latest_user_message})

    # 尝试从 AI 回复中提取名字，如果用户说了“我叫X”
    extracted_name = None
    # 简单的名字提取逻辑：查找“我叫”
    if "我叫" in latest_user_message:
        parts = latest_user_message.split("我叫", 1)
        if len(parts) > 1:
            name_candidate = parts[1].strip()
            # 进一步清理，去除可能的名字后的一些标点或多余词语
            if name_candidate:
                # 假设名字通常不会包含句号、逗号、问号、感叹号
                extracted_name = name_candidate.split('。')[0].split(',')[0].split('？')[0].split('！')[0].strip()
                # 避免提取到空字符串或太短的非名字词
                if len(extracted_name) < 2: # 名字通常不止一个字
                    extracted_name = None # 排除太短的名字，防止误判
    
    # 返回新的状态更新
    # 只需要返回需要更新的部分。LangGraph 会自动合并
    updates = {"messages": [AIMessage(content=ai_response_content)]}
    if extracted_name:
        updates["user_name"] = extracted_name # 如果提取到名字，更新 user_name
        print(f"--- 机器人记住了新名字: {extracted_name} ---")
    
    print("--- 机器人节点处理完毕 ---")
    return updates

# --- 5. 构建 LangGraph 图 (Graph) ---
# 定义一个图，并指定它的“共享记忆区”类型
workflow = StateGraph(AgentState)

# 添加一个节点，命名为 "chatbot_node_id"，对应的处理函数是 chatbot_node
workflow.add_node("chatbot_node_id", chatbot_node)

# 设置图的起点 (所有请求都从这里开始)
workflow.set_entry_point("chatbot_node_id")

# 设置图的终点 (这里是简单示例，直接结束)
workflow.add_edge("chatbot_node_id", END)

# 编译图，得到一个可运行的 LangGraph 应用
# 注意：这里我们没有使用 RedisSaver，因为是简单的内存持久化，所以 checkpointer 默认为 None
app = workflow.compile()

# --- 6. 运行和测试你的机器人 ---

print("欢迎来到简单的LangGraph聊天机器人！输入 'exit' 退出。")
# 我们可以用一个固定的ID来模拟一个会话
# 在这个内存版本的demo中，不同的 session_id 会创建不同的内存会话，
# 但是程序重启后所有内存会话都会丢失。
session_id = "my_first_langgraph_session_1" 

while True:
    user_input = input("你: ")
    if user_input.lower() == 'exit':
        break

    # 准备输入给 LangGraph 的状态。只包含最新的用户消息。
    # LangGraph 会自动从（内存中）加载历史，并与新的消息合并
    input_messages = [HumanMessage(content=user_input)]

    # 运行 LangGraph 应用
    # config 用于传递 LangGraph 内部的配置，这里是 thread_id 来标识会话
    try:
        # stream 方法会逐个yield状态更新
        for s in app.stream(
            {"messages": input_messages}, # 传入最新的用户消息
            config={"configurable": {"thread_id": session_id}} # 告诉 LangGraph 这是哪个会话
        ):
            # 只有当流程结束时（即到达 END 节点），才提取并打印最终回复
            if "__end__" in s:
                final_state = s["__end__"]
                # 找到最新的 AI 消息
                ai_message = next((msg for msg in reversed(final_state["messages"]) if isinstance(msg, AIMessage)), None)
                if ai_message:
                    print(f"AI: {ai_message.content}")
                    # 打印当前记忆中的名字，验证是否记住了
                    print(f"(AI 记住了名字: {final_state.get('user_name', '无')})")
                else:
                    print("AI: (没有回复)")
    except Exception as e:
        print(f"发生错误: {e}")

print("再见！")