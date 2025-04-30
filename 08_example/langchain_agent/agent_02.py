import os
import time
from typing import List, Dict, Any

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

# 导入LangChain Agent相关模块
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.agents import AgentType, Tool, initialize_agent

# 加载环境变量
load_dotenv()

# 获取环境变量
base_url = os.getenv("BASE_URL")
model_api_key = os.getenv("MODEL_API_KEY")
model_name = os.getenv("MODEL_NAME")

# 创建流式输出处理器
class StreamingHandler(BaseCallbackHandler):
    """处理LLM流式输出的回调处理器"""
    
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """每当LLM生成新token时调用"""
        print(token, end="", flush=True)

# 初始化LLM模型
llm = ChatOpenAI(
    base_url=base_url,
    api_key=model_api_key,
    model=model_name,
    temperature=0.1,
    streaming=True
)

# 定义工具函数
@tool
def search_knowledge(query: str) -> str:
    """搜索知识库获取相关信息。输入需要查询的问题。"""
    # 这里模拟知识库查询
    time.sleep(0.5)  # 模拟查询延迟
    search_results = {
        "langchain": "LangChain是一个用于构建LLM应用的框架，帮助开发者创建强大的AI应用。",
        "agent": "Agent是LangChain中的智能代理，能够使用工具解决复杂问题，具有规划和推理能力。",
        "prompt": "提示词工程是设计有效提示以引导LLM行为的技术，是LLM应用的核心。",
        "rag": "RAG(检索增强生成)是结合检索系统和生成模型的技术，提高LLM回答的准确性和可靠性。"
    }
    
    # 简单匹配查询
    for key, value in search_results.items():
        if key.lower() in query.lower():
            return value
    
    return "未找到相关信息。请尝试其他查询或提供更多细节。"

@tool
def calculate(expression: str) -> str:
    """计算数学表达式。输入需要计算的表达式如'2 + 2'或'(3 * 4) / 2'。"""
    try:
        # 警告：在生产环境中使用eval可能存在安全风险
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"

@tool
def current_time() -> str:
    """获取当前的日期和时间"""
    from datetime import datetime
    now = datetime.now()
    return f"当前时间是: {now.strftime('%Y-%m-%d %H:%M:%S')}"

# 创建Agent的提示模板 - 移除记忆相关部分
prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一个智能助手，可以回答问题并使用工具来帮助用户。
    
当你需要外部信息时，请使用提供的工具。工具使用规则:
1. 先思考用户问题需要什么信息
2. 选择合适的工具获取所需信息
3. 使用工具获取的信息给用户全面、准确的回答

保持回答简洁、有礼貌，并使用中文回复。每次只使用一个工具，如有必要可以使用多次工具。
"""),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# 创建工具列表
tools = [
    search_knowledge,
    calculate,
    current_time
]

# 创建Agent - 使用OpenAI Functions方法
agent = create_openai_functions_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

# 创建Agent执行器 - 没有记忆功能
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=False,
    handle_parsing_errors=True,
    max_iterations=3
)

# 演示通过initialize_agent创建Agent的方法（可选）
def create_agent_with_initialize():
    """演示使用initialize_agent函数创建Agent的方法"""
    # 将@tool装饰的函数转换为Tool对象
    tool_objs = [
        Tool(
            name="知识搜索",
            func=search_knowledge,
            description="搜索知识库获取相关信息。输入需要查询的问题。"
        ),
        Tool(
            name="计算器",
            func=calculate,
            description="计算数学表达式。输入需要计算的表达式如'2 + 2'。"
        ),
        Tool(
            name="获取时间",
            func=current_time,
            description="获取当前的日期和时间"
        )
    ]
    
    # 使用initialize_agent创建Agent (无记忆)
    return initialize_agent(
        tools=tool_objs,
        llm=llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=True,
        handle_parsing_errors=True
    )

# 主程序
if __name__ == "__main__":
    print("🤖 LangChain Agent 示例 (无记忆版)")
    print("输入'退出'结束对话，输入'帮助'查看可用命令")
    
    # 用于切换Agent类型的标志
    use_old_style = False
    current_agent = agent_executor
    
    while True:
        user_input = input("\n用户: ")
        
        if user_input.lower() in ["退出", "exit", "quit"]:
            print("谢谢使用!")
            break
        elif user_input.lower() in ["帮助", "help"]:
            print("\n可用命令:")
            print("- 帮助: 显示此帮助信息")
            print("- 退出: 结束对话")
            print("- 切换: 切换Agent实现方式")
            print("- 工具: 列出可用工具")
            continue
        elif user_input.lower() in ["切换", "switch"]:
            use_old_style = not use_old_style
            if use_old_style:
                current_agent = create_agent_with_initialize()
                print("\n已切换到 initialize_agent 方式")
            else:
                current_agent = agent_executor
                print("\n已切换到 create_openai_functions_agent 方式")
            continue
        elif user_input.lower() in ["工具", "tools"]:
            print("\n可用工具:")
            for t in tools:
                print(f"- {t.name}: {t.description}")
            continue
            
        try:
            print("\n助手: ", end="", flush=True)
            
            # 创建流式处理器
            stream_handler = StreamingHandler()
            
            # 使用Agent处理用户输入
            current_agent.invoke(
                {"input": user_input},
                config={"callbacks": [stream_handler]}
            )
            
            print()  # 添加换行
        except Exception as e:
            print(f"处理出错: {str(e)}")
            import traceback
            print(traceback.format_exc())