from langchain.agents import initialize_agent, AgentType, load_tools
from langchain.llms import OpenAI

# 初始化 LLM
llm = OpenAI(openai_api_key="你的OPENAI_API_KEY")

# 加载内置工具（如 Calculator）
tools = load_tools(["llm-math"], llm=llm)

# 初始化 Agent
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# 运行 Agent
if __name__ == "__main__":
    question = "3的5次方是多少？"
    result = agent.run(question)
    print("Agent回答：", result)
