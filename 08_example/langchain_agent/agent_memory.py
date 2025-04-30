"""
基于LangGraph实现的具有记忆功能的Agent示例

这个示例展示了如何使用LangGraph框架为LangChain Agent添加记忆功能，
使Agent能够记住之前的对话内容，提供更连贯的回答。

主要功能：
1. 使用LangGraph管理对话状态
2. 实现会话历史记录（持久化存储到文件）
3. 支持流式输出回答
4. 使用工具增强Agent能力

注意：此实现将对话历史保存到JSON文件中，程序重启后仍可读取历史记录。
"""

import os
import json
from dotenv import load_dotenv
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import HumanMessage, AIMessage, message_to_dict, messages_from_dict
from typing import Dict, List, Any, Tuple, Optional, TypedDict
from langgraph.graph import StateGraph, END
import time
from pathlib import Path

# 加载环境变量
load_dotenv()

# 获取环境变量
base_url = os.getenv("BASE_URL")  # API基础URL
model_api_key = os.getenv("MODEL_API_KEY")  # API密钥
model_name = os.getenv("MODEL_NAME")  # 模型名称

# 自定义流式输出处理器
class CustomStreamingHandler(BaseCallbackHandler):
    """
    流式输出处理器，负责实时显示LLM生成的文本
    
    这个处理器会捕获LLM生成的每个新token并立即打印出来，
    从而实现流畅的输出效果，提升用户体验。
    """
    
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """
        处理LLM生成的每个新token
        
        参数:
            token (str): LLM生成的单个token
            kwargs: 其他参数
        """
        print(token, end="", flush=True)

# 初始化LLM模型 - 启用流式输出
llm = ChatOpenAI(
    base_url=base_url,
    api_key=model_api_key,
    model=model_name,
    temperature=0.1,  # 较低的温度使输出更加确定性
    streaming=True    # 启用流式输出，以便实时显示生成内容
)

# 定义Agent可用的工具

@tool
def search_tool(query: str) -> str:
    """
    模拟搜索工具 - 当Agent需要查找信息时使用
    
    参数:
        query (str): 搜索查询
    
    返回:
        str: 模拟的搜索结果
    """
    # 模拟延迟以展示真实搜索场景
    print("\n正在搜索相关信息...", end="", flush=True)
    time.sleep(1)
    return f"这是关于'{query}'的搜索结果: [模拟搜索结果]"

@tool
def calculator_tool(expression: str) -> str:
    """
    计算器工具 - 当Agent需要进行数学计算时使用
    
    参数:
        expression (str): 数学表达式，如"2 + 2"
    
    返回:
        str: 计算结果或错误信息
    """
    try:
        result = eval(expression)
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"

# 创建Agent提示模板
prompt = ChatPromptTemplate.from_messages([
    # 系统消息定义Agent的行为和能力
    ("system", "你是一个有用的AI助手，能够使用工具来解决问题。回答时使用中文，确保回复简洁清晰。"),
    # 聊天历史记录占位符 - 用于插入历史消息
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    # 用户当前输入
    ("human", "{input}"),
    # Agent思考过程占位符 - 用于插入工具调用过程
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

# 创建OpenAI函数调用Agent
agent = create_openai_functions_agent(
    llm=llm,
    tools=[search_tool, calculator_tool],
    prompt=prompt
)

# 创建Agent执行器 - 负责执行Agent的决策
agent_executor = AgentExecutor(
    agent=agent,
    tools=[search_tool, calculator_tool],
    verbose=False,  # 不显示详细执行日志
    handle_parsing_errors=True,  # 自动处理解析错误
    max_iterations=3  # 最大工具调用次数，防止无限循环
)

# --------------- LangGraph内存实现 ---------------

# 定义图状态类型
class GraphState(TypedDict):
    """
    LangGraph状态定义 - 包含会话历史和当前输入
    
    这个类定义了图在执行过程中传递的状态数据结构，
    包含了维护对话连贯性所需的所有信息。
    """
    chat_history: List[Any]  # 聊天历史记录列表
    input: str               # 当前用户输入

# 定义节点处理函数

def initialize_memory() -> GraphState:
    """
    初始化内存状态
    
    返回:
        GraphState: 包含空聊天历史和空输入的初始状态
    """
    return {
        "chat_history": [],  # 空聊天历史
        "input": ""          # 空输入
    }

def process_input(state: GraphState) -> GraphState:
    """
    处理用户输入(可扩展用于输入预处理)
    
    参数:
        state (GraphState): 当前图状态
        
    返回:
        GraphState: 处理后的图状态
    """
    return state

def agent_node(state: GraphState) -> GraphState:
    """
    Agent处理节点 - 调用Agent处理用户输入，并将结果保存到聊天历史
    
    这是LangGraph工作流的核心节点，负责：
    1. 从状态中提取聊天历史和用户输入
    2. 调用Agent处理输入
    3. 更新聊天历史
    4. 返回更新后的状态
    
    参数:
        state (GraphState): 当前图状态，包含聊天历史和用户输入
        
    返回:
        GraphState: 更新后的图状态，包含新的聊天历史
    """
    # 从状态中获取聊天历史和当前输入
    chat_history = state["chat_history"]
    user_input = state["input"]
    
    # 准备Agent调用的输入参数
    agent_input = {
        "input": user_input,
        "chat_history": chat_history  # 传入历史记录，使Agent感知上下文
    }
    
    # 创建流式输出处理器
    stream_handler = CustomStreamingHandler()
    
    # 调用Agent执行器，附加回调处理流式输出
    response = agent_executor.invoke(
        agent_input,
        config={"callbacks": [stream_handler]}  # 配置流式输出回调
    )
    output = response.get("output", "抱歉，我无法处理这个请求。")
    
    # 更新聊天历史 - 添加用户输入和AI回复
    new_history = list(chat_history)  # 创建历史记录的副本
    new_history.append(HumanMessage(content=user_input))  # 添加用户消息
    new_history.append(AIMessage(content=output))         # 添加AI消息
    
    # 返回更新后的状态
    return {
        "chat_history": new_history,  # 更新后的聊天历史
        "input": user_input           # 保留当前输入(可用于日志或分析)
    }

# 持久化存储相关常量和函数
MEMORY_DIR = Path("memory")  # 内存文件存储目录
MEMORY_FILE = MEMORY_DIR / "chat_history.json"  # 内存文件路径

def save_chat_history(chat_history: List[Any], verbose: bool = False) -> None:
    """
    将聊天历史保存到JSON文件
    
    参数:
        chat_history (List[Any]): 聊天历史记录
        verbose (bool): 是否打印保存消息，默认为False
    """
    # 确保目录存在
    MEMORY_DIR.mkdir(exist_ok=True)
    
    # 将消息对象转换为可序列化的字典
    serializable_history = [message_to_dict(msg) for msg in chat_history]
    
    # 保存到文件
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(serializable_history, f, ensure_ascii=False, indent=2)
    
    # 仅在详细模式下打印保存消息
    if verbose:
        print(f"✅ 聊天历史已保存到: {MEMORY_FILE}")

def load_chat_history() -> List[Any]:
    """
    从JSON文件加载聊天历史
    
    返回:
        List[Any]: 加载的聊天历史记录，如果文件不存在则返回空列表
    """
    # 检查文件是否存在
    if not MEMORY_FILE.exists():
        print("💡 未找到历史记录文件，将创建新的对话历史")
        return []
    
    try:
        # 从文件读取
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            serialized_history = json.load(f)
        
        # 将字典转换回消息对象
        history = messages_from_dict(serialized_history)
        print(f"✅ 已加载 {len(history)} 条历史消息")
        return history
    except Exception as e:
        print(f"⚠️ 加载历史记录时出错: {e}")
        return []

# 使用LangGraph创建工作流
workflow = StateGraph(GraphState)

# 添加节点到图
workflow.add_node("agent", agent_node)  # 添加Agent处理节点

# 配置图的执行流程
workflow.set_entry_point("agent")  # 设置入口点
workflow.add_edge("agent", END)    # 设置出口点

# 编译工作流
memory_graph = workflow.compile()

# --------------- 主程序 ---------------

# 主程序 - 使用LangGraph处理带有内存的对话
if __name__ == "__main__":
    print("🤖 LangGraph 内存增强的 LangChain Agent 示例")
    print("输入'退出'结束对话")
    
    # 从文件加载历史对话记录
    loaded_history = load_chat_history()
    
    # 初始化会话状态 - 使用加载的历史记录
    session_state = {"chat_history": loaded_history, "input": ""}
    
    # 如果有历史记录，显示摘要
    if loaded_history:
        history_count = len(loaded_history) // 2  # 一问一答为一组对话
        print(f"📚 已加载 {history_count} 组历史对话")
        
        # 显示最后一组对话作为提示
        if history_count > 0:
            last_user_msg = loaded_history[-2].content if len(loaded_history) >= 2 else ""
            last_ai_msg = loaded_history[-1].content if len(loaded_history) >= 1 else ""
            print(f"\n上次对话:")
            print(f"用户: {last_user_msg[:50]}{'...' if len(last_user_msg) > 50 else ''}")
            print(f"助手: {last_ai_msg[:50]}{'...' if len(last_ai_msg) > 50 else ''}")
    
    try:
        while True:
            user_input = input("\n用户: ")
            if user_input.lower() in ["退出", "exit", "quit"]:
                # 保存历史记录到文件，并显示保存消息
                save_chat_history(session_state["chat_history"], verbose=True)
                print("谢谢使用!")
                break
            
            try:
                print("\n助手: ", end="", flush=True)
                
                # 更新输入
                session_state["input"] = user_input
                
                # 使用LangGraph执行工作流
                new_state = memory_graph.invoke(
                    session_state,
                    {"configurable": {"thread_id": "memory_thread"}}
                )
                
                # 更新会话状态
                session_state = new_state
                
                # 定期保存聊天历史 (静默保存，不显示消息)
                save_chat_history(session_state["chat_history"])
                
                print()  # 换行
                
            except Exception as e:
                print(f"处理出错: {str(e)}")
                import traceback
                print(traceback.format_exc())
    
    # 确保在程序退出时保存历史记录（即使是由于异常）
    finally:
        if session_state["chat_history"]:
            save_chat_history(session_state["chat_history"], verbose=True)
            print("⚠️ 程序异常退出，已保存聊天历史")