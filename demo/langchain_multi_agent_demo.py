# LangChain多智能体系统示例
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import BaseTool
from langchain.chains import LLMChain
from langchain_core.tools import StructuredTool
from typing import Optional, Type

# 加载环境变量
load_dotenv()

# 初始化LLM
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("BASE_URL"),
    temperature=0.1
)

# 创建专家智能体的工具

# 1. 数学专家工具
class MathematicsExpertTool(BaseTool):
    name = "mathematics_expert"
    description = "当遇到数学问题时，使用这个工具。提供数学问题的详细信息。"
    
    def _run(self, query: str) -> str:
        # 这里我们使用LLM链来模拟数学专家的回答
        math_template = "你是一位数学专家。请解答以下数学问题：{question}"
        math_prompt = ChatPromptTemplate.from_template(math_template)
        math_chain = LLMChain(llm=llm, prompt=math_prompt)
        return math_chain.run(question=query)
    
    def _arun(self, query: str):
        # 异步版本
        raise NotImplementedError("暂不支持异步操作")

# 2. 语言学专家工具
class LinguisticsExpertTool(BaseTool):
    name = "linguistics_expert"
    description = "当遇到语言、语法、词源学或翻译相关问题时，使用这个工具。"
    
    def _run(self, query: str) -> str:
        linguistics_template = "你是一位语言学专家。请回答以下语言相关问题：{question}"
        linguistics_prompt = ChatPromptTemplate.from_template(linguistics_template)
        linguistics_chain = LLMChain(llm=llm, prompt=linguistics_prompt)
        return linguistics_chain.run(question=query)
    
    def _arun(self, query: str):
        raise NotImplementedError("暂不支持异步操作")

# 3. 历史学家工具
class HistorianTool(BaseTool):
    name = "historian"
    description = "当遇到历史事件、人物或时期相关问题时，使用这个工具。"
    
    def _run(self, query: str) -> str:
        history_template = "你是一位历史学家。请回答以下历史相关问题：{question}"
        history_prompt = ChatPromptTemplate.from_template(history_template)
        history_chain = LLMChain(llm=llm, prompt=history_prompt)
        return history_chain.run(question=query)
    
    def _arun(self, query: str):
        raise NotImplementedError("暂不支持异步操作")

# 创建研究助手工具函数
def research_assistant(question: str) -> str:
    """当需要查找事实或进行研究时使用。"""
    template = "你是一位研究助手，擅长查找信息。请研究并回答：{question}"
    prompt = ChatPromptTemplate.from_template(template)
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run(question=question)

# 创建总结工具函数
def summarizer(text: str) -> str:
    """对提供的文本进行总结。"""
    template = "请简明扼要地总结以下内容：\n\n{text}"
    prompt = ChatPromptTemplate.from_template(template)
    chain = LLMChain(llm=llm, prompt=prompt)
    return chain.run(text=text)

# 初始化各专家工具
mathematics_tool = MathematicsExpertTool()
linguistics_tool = LinguisticsExpertTool()
historian_tool = HistorianTool()

# 创建结构化工具
research_tool = StructuredTool.from_function(
    func=research_assistant,
    name="research_assistant",
    description="当需要查找事实或进行研究时使用。",
    args_schema=None
)

summarize_tool = StructuredTool.from_function(
    func=summarizer,
    name="summarizer",
    description="对提供的文本进行总结。",
    args_schema=None
)

# 创建工具列表
tools = [
    mathematics_tool,
    linguistics_tool,
    historian_tool,
    research_tool,
    summarize_tool
]

# 初始化协调智能体 - 这是主智能体，负责选择调用哪个专家智能体
coordinator = initialize_agent(
    tools,
    llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
    handle_parsing_errors=True,
)

def run_multi_agent_system(query):
    """运行多智能体系统，处理用户查询"""
    print(f"用户查询: {query}")
    print("\n正在协调智能体系统处理您的请求...\n")
    response = coordinator.run(query)
    print(f"\n最终回答: {response}")
    return response

if __name__ == "__main__":
    # 测试多智能体系统
    queries = [
        "计算235乘以17.5等于多少?",
        "解释'语言相对论'的基本原理是什么?",
        "中国古代丝绸之路的主要路线和历史意义是什么?"
    ]
    
    for query in queries:
        print("\n" + "="*50)
        run_multi_agent_system(query)
        print("="*50)