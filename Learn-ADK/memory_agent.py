"""
一个具有内存功能的 Google ADK 代理示例
"""

import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
from google.adk.memory import InMemoryMemoryService
from google.adk.memory import InMemorySessionService
from google.adk.sessions import load_memory

# 创建内存服务和会话服务
memory_service = InMemoryMemoryService()
session_service = InMemorySessionService(memory_service=memory_service)

def get_weather(city: str) -> dict:
    """获取指定城市的当前天气报告。

    Args:
        city (str): 需要获取天气报告的城市名称。

    Returns:
        dict: 包含状态和结果或错误信息的字典。
    """
    # 城市天气数据字典 - 在实际应用中应该连接到真实的天气API
    city_weather = {
        "new york": {
            "status": "success",
            "report": "The weather in New York is sunny with a temperature of 25 degrees Celsius (77 degrees Fahrenheit)."
        },
        "newyork": {
            "status": "success",
            "report": "The weather in New York is sunny with a temperature of 25 degrees Celsius (77 degrees Fahrenheit)."
        },
        "纽约": {
            "status": "success",
            "report": "纽约天气晴朗，气温25摄氏度（77华氏度）。"
        },
        "shanghai": {
            "status": "success",
            "report": "The weather in Shanghai is cloudy with a temperature of 22 degrees Celsius (72 degrees Fahrenheit)."
        },
        "shang hai": {
            "status": "success",
            "report": "The weather in Shanghai is cloudy with a temperature of 22 degrees Celsius (72 degrees Fahrenheit)."
        },
        "上海": {
            "status": "success",
            "report": "上海今天多云，气温22摄氏度（72华氏度）。"
        },
        "beijing": {
            "status": "success", 
            "report": "The weather in Beijing is sunny with a temperature of 24 degrees Celsius (75 degrees Fahrenheit)."
        },
        "北京": {
            "status": "success",
            "report": "北京今天晴朗，气温24摄氏度（75华氏度）。"
        },
        "london": {
            "status": "success",
            "report": "The weather in London is rainy with a temperature of 18 degrees Celsius (64 degrees Fahrenheit)."
        },
        "伦敦": {
            "status": "success",
            "report": "伦敦今天下雨，气温18摄氏度（64华氏度）。"
        },
        "tokyo": {
            "status": "success",
            "report": "The weather in Tokyo is partly cloudy with a temperature of 26 degrees Celsius (79 degrees Fahrenheit)."
        },
        "东京": {
            "status": "success",
            "report": "东京今天多云间晴，气温26摄氏度（79华氏度）。"
        }
    }
    
    city_lower = city.lower()
    if city_lower in city_weather:
        return city_weather[city_lower]
    else:
        return {
            "status": "error",
            "error_message": f"Weather information for '{city}' is not available."
        }


def get_current_time(city: str) -> dict:
    """返回指定城市的当前时间。

    Args:
        city (str): 需要获取当前时间的城市名称。

    Returns:
        dict: 包含状态和结果或错误信息的字典。
    """
    # 城市到时区的映射字典
    city_to_timezone = {
        "new york": "America/New_York",
        "newyork": "America/New_York",
        "纽约": "America/New_York",
        "shanghai": "Asia/Shanghai",
        "shang hai": "Asia/Shanghai",
        "上海": "Asia/Shanghai",
        "beijing": "Asia/Shanghai", 
        "北京": "Asia/Shanghai",
        "london": "Europe/London",
        "伦敦": "Europe/London",
        "tokyo": "Asia/Tokyo",
        "东京": "Asia/Tokyo"
    }
    
    city_lower = city.lower()
    if city_lower in city_to_timezone:
        tz_identifier = city_to_timezone[city_lower]
    else:
        return {
            "status": "error",
            "error_message": (
                f"Sorry, I don't have timezone information for {city}."
            ),
        }

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    report = (
        f'The current time in {city} is {now.strftime("%Y-%m-%d %H:%M:%S %Z%z")}'
    )
    return {"status": "success", "report": report}


# 添加便笺记录工具
def save_note(content: str) -> dict:
    """保存用户的便笺到代理的记忆中。

    Args:
        content: 要保存的便笺内容

    Returns:
        保存状态信息
    """
    return {
        "status": "success",
        "message": f"我已将您的便笺保存到记忆中: '{content}'"
    }


# 创建带有记忆功能的代理
memory_agent = Agent(
    name="memory_agent",
    model="gemini-2.0-flash",
    description="一个具有记忆功能的代理，可以记住用户的便笺并在需要时回忆起来。",
    instruction=(
        "你是一个友好的助手，可以帮助用户处理以下任务："
        "1. 查询城市天气（使用get_weather工具）"
        "2. 查询城市时间（使用get_current_time工具）"
        "3. 保存用户的便笺（使用save_note工具）"
        "4. 在需要时从记忆中检索过去的信息（使用load_memory工具）\n\n"
        "当用户要求你记住某些内容时，使用save_note工具保存。"
        "当用户询问过去的便笺或信息时，使用load_memory工具从记忆中检索相关信息。"
        "支持的城市包括：纽约(New York)、上海(Shanghai)、北京(Beijing)、伦敦(London)和东京(Tokyo)。"
    ),
    tools=[get_weather, get_current_time, save_note, load_memory],
)

# 为了便于外部访问
def get_agent():
    return memory_agent

# 当直接运行此文件时的交互功能
if __name__ == "__main__":
    print("开始与记忆代理聊天。输入'退出'结束对话。")
    print("示例操作:")
    print("- 上海今天的天气怎么样？")
    print("- 请记住我的生日是8月15日")
    print("- 你能告诉我我的生日是什么时候吗？")
    
    # 为该用户创建唯一标识符
    user_id = "demo_user_001"
    app_name = "memory_test_app"
    
    # 创建或检索会话
    session = session_service.get_or_create_session(
        app_name=app_name,
        user_id=user_id
    )
    
    # 使用session启动聊天
    chat_session = memory_agent.start_chat(session=session)
    
    while True:
        user_input = input("\n您: ")
        if user_input.lower() in ["退出", "exit", "quit"]:
            # 将会话添加到记忆中以便日后检索
            memory_service.add_session_to_memory(session)
            break
        
        # 发送消息并获取响应
        response = chat_session.send_message(user_input)
        print(f"\n代理: {response.content}")
        
    print("聊天已结束，您的会话已保存到记忆中。")