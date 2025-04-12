from langchain.agents import initialize_agent, Tool
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI

# 定义提示词工具
def english_assistant_tool(query: str) -> str:
    """
    仅回答与英语相关的问题。
    """
    if "英语" in query or "English" in query:
        return f"这是与英语相关的回答: {query}"
    else:
        return "抱歉，我只能回答与英语相关的问题。"

# 初始化工具
tools = [
    Tool(
        name="EnglishAssistant",
        func=english_assistant_tool,
        description="回答与英语相关的问题，例如语法、词汇、翻译等。"
    )
]

# 定义提示模板
template = """
你是一位专业的英语助手，专注于帮助用户提升英语水平。

职责:
1. 回答英语学习相关的所有问题
2. 提供准确的语法解释
3. 协助词汇学习和用法讲解
4. 帮助改进英语写作和口语表达
5. 提供地道的英语表达建议

如果收到与英语无关的问题，请礼貌地说明你的专业领域仅限于英语学习。

记住:
- 回答要简洁清晰
- 使用易懂的解释
- 适当提供例句
- 保持专业和耐心

问题: {input}
"""
prompt = PromptTemplate(input_variables=["input"], template=template)

# 初始化 LLM 和 Agent
llm = OpenAI(temperature=0)
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

# 测试 Agent
if __name__ == "__main__":
    while True:
        user_input = input("请输入您的问题: ")
        if user_input.lower() in ["退出", "exit", "quit"]:
            print("感谢使用英语助手，再见！")
            break
        response = agent.run(prompt.format(input=user_input))
        print(response)