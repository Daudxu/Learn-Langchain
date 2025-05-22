import uuid
import sys
import os
from typing import List, Annotated, TypedDict
from operator import itemgetter

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# LangGraph 相关导入
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.redis import RedisSaver
import redis # 仍然需要导入 redis 库来处理连接参数，尽管不再直接传入客户端实例

# 1. 加载环境变量
load_dotenv()

# --- 配置 Redis ---
# 请根据你的 Redis 配置修改以下参数
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# 构建 Redis 连接 URL 字符串
# RedisSaver 期望接收一个 URL 字符串，而不是直接的 Redis 客户端实例
redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
if REDIS_PASSWORD:
    # 如果有密码，将密码嵌入 URL
    redis_url = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# 【重要修复】初始化 RedisSaver，直接传入 URL 字符串
# LangGraph 的 RedisSaver 内部会使用这个 URL 来创建和管理 Redis 连接
try:
    memory_checkpointer = RedisSaver(redis_url)
    # 尝试ping一下，确保URL能被RedisSaver内部正确解析和连接
    # 注意：RedisSaver内部连接可能发生在第一次checkpoint时，这里只是一个额外检查
    _temp_client = redis.StrictRedis.from_url(redis_url, decode_responses=True)
    _temp_client.ping()
    print(f"成功连接到 Redis 服务器：{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB} (通过URL)")
except redis.exceptions.ConnectionError as e:
    print(f"无法连接到 Redis 服务器：{e}")
    print("请确保 Redis 服务器正在运行并配置正确，或者在 .env 文件中设置正确的 Redis 环境变量。")
    sys.exit(1) # 如果无法连接 Redis，则退出


# 2. 创建 FastAPI 应用
app = FastAPI()

base_url = os.getenv("BASE_URL")
model_api_key = os.getenv("MODEL_API_KEY")
model_name = os.getenv("MODEL_NAME")

llm = ChatOpenAI(
    base_url=base_url,
    api_key=model_api_key,
    model=model_name,
    temperature=0.1,
    max_tokens=512,
    streaming=True
)

# --- LangGraph 相关定义 ---

# 3. 定义 LangGraph 的状态
# 'messages' 将存储对话历史，'word' 用于传递额外信息，例如初始欢迎语的 'word'
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], itemgetter("messages")]
    word: str # 用于存储初始欢迎语的单词，确保其在状态中持久化

# 4. 定义 LangGraph 的节点
def call_llm_node(state: AgentState):
    """
    LangGraph 节点：调用语言模型生成回复。
    它接收当前状态，并返回需要更新的状态。
    """
    messages = state["messages"]
    current_word = state.get("word", "apple") # 从状态中获取 'word'

    # 4.1. Prompt 模板
    # MessagesPlaceholder 现在直接使用 'messages'，因为它会接收整个历史
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"你是一个助手，你的关键词是：{current_word}"), # 动态关键词
        MessagesPlaceholder(variable_name="messages"),
        ("user", "{input}"), # 这里 {input} 是最新的用户消息，不是全部历史
    ])

    # 4.2. 构建 LCEL Chain (作为节点内部逻辑)
    # 确保只传递最新用户消息给 {input} 占位符
    latest_human_message = ""
    # 注意：LangGraph 传递给节点的是当前状态的完整 messages 列表
    # 如果列表为空（首次调用），或者只有 AIMessage 等，需要小心处理
    if messages and isinstance(messages[-1], HumanMessage):
        latest_human_message = messages[-1].content
    
    # LCEL 链在节点内部
    llm_chain = (
        prompt
        | llm
        | StrOutputParser()
    )
    
    # 传入完整的 messages 历史和最新的 input
    response_content = llm_chain.invoke({
        "messages": messages, # 提供给 MessagesPlaceholder
        "input": latest_human_message # 提供给 {input}
    })

    # 返回新的 AIMessage，LangGraph 会将其添加到状态的 messages 列表中
    return {"messages": [AIMessage(content=response_content)]}

# 5. 构建 LangGraph 图
workflow = StateGraph(AgentState)

# 添加 LLM 节点
workflow.add_node("llm_agent", call_llm_node)

# 设置图的入口
workflow.set_entry_point("llm_agent")

# 设置图的出口 (简单场景，直接结束)
workflow.add_edge("llm_agent", END)

# 编译图，并传入 RedisSaver 作为检查点
# session_id (thread_id) 将作为键来持久化状态
langgraph_app = workflow.compile(checkpointer=memory_checkpointer)

# --- FastAPI WebSocket 端点 ---
@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    # 为每个新的 WebSocket 连接生成一个唯一的 session_id
    session_id = str(uuid.uuid4())
    print(f"New WebSocket connection. Session ID: {session_id}")

    initial_word = "apple" # 默认值
    try:
        # 接收可选的初始单词，用于定制会话
        init_data = await websocket.receive_text()
        if init_data.strip():
            initial_word = init_data.strip()
    except Exception:
        pass # 如果没有收到初始数据，则使用默认值

    try:
        # 初始化 LangGraph 状态并发送欢迎语
        # 传入初始状态，特别是 'word'。
        # 对于首次欢迎语，我们传入一个空的 HumanMessage，让模型根据 system prompt 生成。
        initial_input_messages = []
        # 如果需要模型在启动时说欢迎语，可以添加一个空的 HumanMessage
        # 或更明确地，在系统提示中引导模型在空输入时欢迎
        initial_input_messages.append(HumanMessage(content="")) # 触发首次模型响应
        
        initial_state_input = {"messages": initial_input_messages, "word": initial_word}
        
        # 使用 stream 方法迭代 LangGraph 进程
        # config 字典用于传递 LangGraph 内部配置，包括 thread_id
        async for s in langgraph_app.stream(
            initial_state_input,
            config={"configurable": {"thread_id": session_id}}
        ):
            # 迭代 LangGraph 的状态更新
            # 这里的 s 是 LangGraph 每次状态更新后的字典
            # 当流到达 END 节点时，s 会包含 "__end__" 键，其值是最终的状态
            if "__end__" in s:
                final_state = s["__end__"]
                # 提取 AI 的回复（通常是 messages 列表中的最后一个 AIMessage）
                ai_message = next((msg for msg in reversed(final_state["messages"]) if isinstance(msg, AIMessage)), None)
                if ai_message:
                    await websocket.send_text(ai_message.content)
                break # 退出循环，因为首次流程已结束
            
            # 如果你未来有更复杂的图，中间节点有输出，可以在这里处理
            # 比如，如果 LangGraph 有多个节点，每个节点都有输出
            # for key, value in s.items():
            #     if key != "__end__":
            #         # 假设节点返回的消息在 messages 字段
            #         if "messages" in value and value["messages"]:
            #             last_msg = value["messages"][-1]
            #             if isinstance(last_msg, AIMessage):
            #                 await websocket.send_text(last_msg.content)
            #                 await websocket.send_text("[PARTIAL_END]") # 标记部分完成

        await websocket.send_text("[END]") # 标记首次回复结束

        # 开始持续的用户输入和 AI 回复循环
        while True:
            user_input = await websocket.receive_text()
            if user_input.lower() in ["exit", "quit", "q"]:
                await websocket.close()
                # LangGraph 已经自动持久化了，无需手动 clear
                # 如果你想清除特定会话的历史，可以使用 memory_checkpointer.delete(thread_id=session_id)
                return

            # 将用户输入添加到 LangGraph 的状态中
            # 注意：这里我们只需要传递最新的 HumanMessage。
            # LangGraph 会根据 thread_id 从 Redis 加载之前的历史，并自动合并新的输入。
            current_input_messages = [HumanMessage(content=user_input)]
            
            async for s in langgraph_app.stream(
                {"messages": current_input_messages}, # 仅传递最新用户消息
                config={"configurable": {"thread_id": session_id}}
            ):
                if "__end__" in s:
                    final_state = s["__end__"]
                    ai_message = next((msg for msg in reversed(final_state["messages"]) if isinstance(msg, AIMessage)), None)
                    if ai_message:
                        await websocket.send_text(ai_message.content)
                    break # 退出循环，因为当前轮次流程已结束
            await websocket.send_text("[END]")

    except WebSocketDisconnect:
        print(f"WebSocket disconnected. Session ID: {session_id}")
        # 在这里，你可以选择清除此会话的 Redis 历史，如果不需要长期保存
        # memory_checkpointer.delete(thread_id=session_id)
        pass
    except Exception as e:
        print(f"An error occurred: {e}")
        await websocket.send_text(f"Error: {e}")
        await websocket.close()