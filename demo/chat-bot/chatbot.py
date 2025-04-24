from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.load_tools import load_tools
import os
from dotenv import load_dotenv

load_dotenv()

base_url = os.getenv("BASE_URL")
model_api_key = os.getenv("MODEL_API_KEY")
model_name = os.getenv("MODEL_NAME")


def main():
    llm = ChatOpenAI(
        base_url=base_url,
        api_key=model_api_key,
        model=model_name,
        temperature=0.1,
        max_tokens=1000
    )
    # 只加载 llm-math 工具，避免 serpapi 报错
    tools = load_tools(["llm-math"], llm=llm)
    # 初始化 Agent
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True
    )
    print("输入 'exit' 退出对话。\n")
    while True:
        user_input = input("你：")
        if user_input.strip().lower() == 'exit':
            print("结束对话。"); break
        result = agent.run(user_input)
        print("AI：", result)

if __name__ == "__main__":
    main()