import os
from dotenv import load_dotenv
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.callbacks import BaseCallbackHandler
import time

# 加载环境变量
load_dotenv()

# 获取环境变量
base_url = os.getenv("BASE_URL")
model_api_key = os.getenv("MODEL_API_KEY")
model_name = os.getenv("MODEL_NAME")

# 创建正确的CallbackHandler实现
class CustomStreamingHandler(BaseCallbackHandler):
    """流式输出处理器，只处理LLM生成的新token"""
    
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """处理LLM生成的新token"""
        print(token, end="", flush=True)

# 初始化LLM模型 - 启用流式输出
llm = ChatOpenAI(
    base_url=base_url,
    api_key=model_api_key,
    model=model_name,
    temperature=0.1,
    streaming=True  # 启用流式输出
)

# 定义工具
@tool
def search_tool(query: str) -> str:
    """当需要查找信息时使用这个搜索工具"""
    # 模拟延迟以便展示流式效果
    print("\n正在搜索相关信息...", end="", flush=True)
    time.sleep(1)
    return f"这是关于'{query}'的搜索结果: [模拟搜索结果]"

@tool
def calculator_tool(expression: str) -> str:
    """当需要计算数学表达式时使用这个工具"""
    try:
        result = eval(expression)
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"

# 创建提示模板
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个有用的AI助手，能够使用工具来解决问题。回答时使用中文，确保回复简洁清晰。"),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

# 创建Agent
agent = create_openai_functions_agent(
    llm=llm,
    tools=[search_tool, calculator_tool],
    prompt=prompt
)

# 创建Agent执行器
agent_executor = AgentExecutor(
    agent=agent,
    tools=[search_tool, calculator_tool],
    verbose=False,
    handle_parsing_errors=True,
    max_iterations=3
)

# 主程序 - 支持流式输出
if __name__ == "__main__":
    print("🤖 简易LangChain Agent 示例 (支持流式输出)")
    print("输入'退出'结束对话")
    
    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ["退出", "exit", "quit"]:
            print("谢谢使用!")
            break
            
        try:
            print("\n助手: ", end="", flush=True)
            
            # 每次创建新的回调处理器
            stream_handler = CustomStreamingHandler()
            
            # 使用invoke方法，传入回调
            response = agent_executor.invoke(
                {"input": user_input},
                config={"callbacks": [stream_handler]}
            )
            
            print()  # 添加换行
        except Exception as e:
            print(f"处理出错: {str(e)}")
            # 打印更详细的错误信息以便调试
            import traceback
            print(traceback.format_exc())