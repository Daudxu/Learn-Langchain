import os
from typing import List, Annotated, TypedDict
from operator import add # 用于合并列表

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

# 引入 LangGraph 核心组件
from langgraph.graph import StateGraph, END

# 引入 dotenv 用于加载 .env 文件中的环境变量
from dotenv import load_dotenv

# --- 1. 加载环境变量 ---
load_dotenv()

# --- 2. 配置你的大模型 (LLM) ---
# 从 .env 文件中获取配置。请确保你的 .env 文件中有 API_BASE, API_KEY, BASE_MODEL
API_BASE = os.getenv("API_BASE")
API_KEY = os.getenv("API_KEY")
BASE_MODEL = os.getenv("BASE_MODEL")

# 检查 API_KEY 是否设置，如果没有则抛出错误
if not API_KEY:
    raise ValueError("请在 .env 文件中设置 API_KEY！")

# 初始化 LangChain 的 ChatOpenAI 模型
llm = ChatOpenAI(
    base_url=API_BASE,
    api_key=API_KEY,
    model=BASE_MODEL,
    temperature=0.7, # 控制模型回复的创造性，0.7 比较自然
    max_tokens=256,  # 限制模型回复的最大 token 数
    streaming=True   # 启用流式输出，虽然在这个简单 demo 的控制台不会逐字显示，但这是个好习惯
)

print(f"✅ 模型配置成功: {BASE_MODEL} ({API_BASE})")

# ---

# ### 3. 定义 LangGraph 的“共享记忆区” (State)

# 这个 `AgentState` 就是你的 LangGraph 应用的**“大脑”或“记忆”**。它是一个 `TypedDict`，定义了在整个 LangGraph 流程中需要共享和更新的数据结构。

# ```python
class AgentState(TypedDict):
    # messages: 存储所有聊天消息的历史记录 (包括用户和AI的消息)。
    # Annotated[List[BaseMessage], add] 告诉 LangGraph：
    # 当有新的 BaseMessage 列表返回时，使用 `operator.add` 函数将其追加（concatenate）到现有的消息列表末尾。
    messages: Annotated[List[BaseMessage], add]
    
    # first_utterance: 存储用户对机器人说的第一句话。
    # 这个字段的默认值是 None，这样我们就可以判断它是否已经被设置过。
    first_utterance: str


def chatbot_node(state: AgentState):
    print("\n--- 机器人节点开始处理 ---")
    
    # 从机器人的“记忆”中获取当前的消息历史列表
    messages = state["messages"]
    # 获取 'first_utterance' 字段。如果状态中还没有这个字段，它的值会是 None。
    first_utterance = state.get("first_utterance") 

    # 尝试从最新的消息中提取用户输入
    latest_user_message = ""
    # 确保 messages 列表非空，并且最新消息是 HumanMessage 类型
    if messages and isinstance(messages[-1], HumanMessage):
        latest_user_message = messages[-1].content
    else:
        # 这种情况通常发生在程序的第一次运行，或者消息历史为空时。
        # 如果 'first_utterance' 还没有被设置过 (即为 None)，我们发送一个欢迎语。
        if first_utterance is None:
            ai_response_content = "你好！很高兴和你聊天。请问你想说什么？"
            # 返回欢迎语，并同时将这个欢迎语作为 'first_utterance' 记住，确保它只在首次设置。
            return {"messages": [AIMessage(content=ai_response_content)], "first_utterance": ai_response_content}
        else:
            # 如果不是真正的第一次对话（first_utterance 已有值），但当前收到的不是有效用户消息，
            # 则不做任何状态更新，等待下一次有效用户输入。
            return {}

    # 关键逻辑：只有当 'first_utterance' 还没有被设置过 (即它当前是 None) 时，才将其设置为当前用户输入。
    # 这样确保 'first_utterance' 只会记住第一句有效对话。
    if first_utterance is None:
        first_utterance = latest_user_message
        print(f"--- 机器人记住了你的第一句话: '{first_utterance}' ---")

    # 准备给大模型的 Prompt 模板。
    # SystemMessage 设置机器人的角色，并告诉它记住的第一句话。
    prompt_messages = [
        SystemMessage(content=f"你是一个友好的AI助手。我们之前的对话中，你记住的第一句话是 '{first_utterance}'。在回复时，可以偶尔（但不要每次）提及这句话。"),
        # MessagesPlaceholder 会自动将 LangGraph 传递过来的完整 'messages' 历史列表填充到这里。
        # 这样大模型就能看到完整的对话上下文，包括用户最新的消息。
        MessagesPlaceholder(variable_name="messages"), 
    ]
    
    # 从消息列表构建 ChatPromptTemplate
    prompt = ChatPromptTemplate.from_messages(prompt_messages)

    # 构建 LangChain 表达式语言 (LCEL) 链。
    # 这个链的步骤是：Prompt -> 大模型 (LLM) -> 字符串解析器 (StrOutputParser)。
    full_chain = (
        prompt
        | llm
        | StrOutputParser()
    )

    # 调用链，让大模型根据当前的 messages 历史生成回复。
    # 传入的字典中只包含 'messages' 键，因为 MessagesPlaceholder 已经包含了最新用户消息。
    ai_response_content = full_chain.invoke({"messages": messages}) 

    # 返回需要更新到“记忆”中的内容。
    # updates 字典中的键会对应 AgentState 的字段，值会根据该字段的 reducer 进行合并。
    updates = {"messages": [AIMessage(content=ai_response_content)]}
    
    # 只有当 'first_utterance' 确实从 None 变为一个具体值时，才将其更新到状态中。
    if state.get("first_utterance") is None and first_utterance is not None:
        updates["first_utterance"] = first_utterance
    
    print("--- 机器人节点处理完毕 ---")
    return updates

# ---

# ### 5. 构建 LangGraph 图 (Graph)

# 这里我们定义 LangGraph 的流程图结构。对于这个简单的 Demo，只有一个节点和一条边。

# ```python
# 定义一个图，并指定它使用哪个“共享记忆区” (AgentState)
workflow = StateGraph(AgentState)

# 添加一个节点。第一个参数是节点ID (你可以自定义，但必须唯一)，第二个是对应的处理函数。
workflow.add_node("chat_node", chatbot_node)

# 设置图的起点。所有进入这个 LangGraph 应用的请求，都会从 "chat_node" 开始执行。
workflow.set_entry_point("chat_node")

# 设置图的终点。这里表示 "chat_node" 执行完毕后，整个流程就结束了。
# 在持续对话的应用中，通常会把边引回某个节点形成循环，或者引到决策节点。
workflow.add_edge("chat_node", END)

# 编译图。这将把图的定义转化为一个可运行的 LangGraph 应用实例。
# 这个简单的 demo 不使用持久化 (checkpointer 默认为 None)，所以每次运行程序，对话历史都会重置。
app = workflow.compile()


print("\n--- 欢迎来到最简单的 LangGraph 聊天机器人！---")
print("输入 'exit' 退出对话。")

# 在这个简单的内存版本 demo 中，每次运行程序都是一个新的会话。
# `session_id` 用于 LangGraph 内部识别不同的会话，但这里每次都用相同的 ID，
# 且因为没有持久化，程序重启后记忆会丢失。
session_id = "single_session_for_demo" 

# 循环以实现持续对话
while True:
    user_input = input("你: ")
    if user_input.lower() == 'exit': # 用户输入 'exit' 则退出循环
        break

    # 准备输入给 LangGraph 的最新用户消息。
    # LangGraph 会自动根据 session_id 加载之前的状态并合并这条新消息。
    input_messages = [HumanMessage(content=user_input)]

    try:
        # 使用 .invoke() 方法运行 LangGraph 图一次。
        # 它会等待整个流程（即 chatbot_node 的执行）完成，并返回最终的状态。
        final_state = app.invoke(
            {"messages": input_messages}, # 传入最新的用户消息
            config={"configurable": {"thread_id": session_id}} # 告诉 LangGraph 这是哪个会话
        )
        
        # 从最终状态中找到最新的 AI 回复，并打印出来。
        # `reversed` 确保我们从列表末尾开始找，`next` 找到第一个符合条件的就停止。
        ai_message = next((msg for msg in reversed(final_state["messages"]) if isinstance(msg, AIMessage)), None)
        if ai_message:
            print(f"AI: {ai_message.content}")
            # 打印机器人当前记住的第一句话，用于验证功能。
            print(f"(机器人记住的第一句话: '{final_state.get('first_utterance', '无')}')")
        else:
            print("AI: (没有回复)")

    except Exception as e:
        print(f"发生错误: {e}")
        # 如果是 API Key 错误，打印更详细的提示，方便用户调试。
        if "AuthenticationError" in str(e):
            print("❗ 错误提示：你的 API Key 可能不正确或过期。请检查 .env 文件中的 API_KEY。")

print("再见！")