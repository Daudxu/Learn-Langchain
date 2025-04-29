from google.adk.agents import Agent

# 原始的 Gemini 模型代理
gemini_agent = Agent(
    name="simple_agent",
    model="gemini-2.0-flash",
    description=(
        "you are a helpful assistant."
    ),
    instruction=(
        "you are a helpful assistant."
    ),  # 这里缺少了逗号
    tools=[],
)


