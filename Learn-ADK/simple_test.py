"""
一个简单的 Google ADK 代理示例，用于演示 'adk web' 命令的使用。
"""

from google.adk.agents import Agent

def hello_world(name: str = "World") -> str:
    """一个简单的打招呼函数
    
    Args:
        name: 要打招呼的对象名称
        
    Returns:
        打招呼的字符串
    """
    return f"你好，{name}！欢迎使用 Google ADK！"

# 创建一个简单的代理
simple_agent = Agent(
    name="simple_test_agent",
    model="gemini-2.0-flash",
    description="一个用于测试 ADK Web 界面的简单代理",
    instruction="你是一个友好的助手，可以回答问题并使用工具帮助用户。请使用中文回复。",
    tools=[hello_world],
)

# 为了便于外部访问
def get_agent():
    return simple_agent

# 当直接运行此文件时的简单交互功能
if __name__ == "__main__":
    print("开始与测试代理聊天。输入'退出'结束对话。")
    print("示例: 跟小明打个招呼")
    
    # 创建聊天会话
    chat_session = simple_agent.start_chat()
    
    while True:
        user_input = input("\n您: ")
        if user_input.lower() in ["退出", "exit", "quit"]:
            break
        
        # 发送消息并获取响应
        response = chat_session.send_message(user_input)
        print(f"\n代理: {response.content}")