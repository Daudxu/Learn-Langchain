# AutoGen与LangChain集成示例
import os
from dotenv import load_dotenv
import autogen
from langchain_openai import OpenAI
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate

# 加载环境变量
load_dotenv()

# LangChain组件 - 创建一个简单的链
llm = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("BASE_URL"),
    temperature=0.1
)

prompt = PromptTemplate.from_template("解释下面的概念: {concept}")
langchain_explainer = LLMChain(llm=llm, prompt=prompt)

# AutoGen组件 - 创建智能体
config_list = [
    {
        "model": "gpt-3.5-turbo",
        "api_key": os.getenv("OPENAI_API_KEY"),
    }
]

# 创建用户代理（代表人类）
user_proxy = autogen.UserProxyAgent(
    name="用户",
    human_input_mode="TERMINATE",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={"work_dir": "coding"}
)

# 创建助手智能体并集成LangChain功能
assistant = autogen.AssistantAgent(
    name="助手",
    llm_config={"config_list": config_list}
)

# LangChain与AutoGen集成的自定义智能体
class LangChainAgent(autogen.AssistantAgent):
    def __init__(self, name, langchain_chain, **kwargs):
        super().__init__(name=name, **kwargs)
        self.langchain_chain = langchain_chain
    
    async def a_run(self, message, sender, config):
        if "解释概念:" in message.get("content", ""):
            # 提取概念并使用LangChain处理
            concept = message.get("content").split("解释概念:")[1].strip()
            explanation = self.langchain_chain.run(concept=concept)
            return {"content": f"通过LangChain解释: {explanation}"}
        else:
            # 使用原始AutoGen处理
            return await super().a_run(message, sender, config)

# 创建集成LangChain的智能体
langchain_integrated_agent = LangChainAgent(
    name="LangChain知识库",
    langchain_chain=langchain_explainer,
    llm_config={"config_list": config_list}
)

# 初始化多智能体工作流
def start_multi_agent_workflow():
    user_proxy.initiate_chat(
        langchain_integrated_agent,
        message="解释概念: 检索增强生成(RAG)"
    )
    
    # 继续与常规AutoGen助手交谈
    user_proxy.initiate_chat(
        assistant,
        message="基于上面的RAG解释，与AutoGen相比，RAG的主要优势是什么？"
    )

if __name__ == "__main__":
    # 运行多智能体系统
    start_multi_agent_workflow()