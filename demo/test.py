from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
from bs4 import BeautifulSoup as Soup
from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

load_dotenv()

# lcel download the page
url = "https://python.langchain.com/docs/concepts/lcel/"
loader = RecursiveUrlLoader(
        url=url, 
        max_depth=20, 
        extractor=lambda x: Soup(x, "html.parser").text
    )

docs = loader.load()

d_sorted = sorted(docs, key=lambda x: x.metadata["source"])
d_reversed = list(reversed(d_sorted))
concatenated_text = "\n\n\n --- \n\n\n".join([doc.page_content for doc in d_reversed])

print("Number of documents: ", concatenated_text)



BASE_URL = os.getenv("BASE_URL")
DS_API_KEY = os.getenv("DS_API_KEY")
MODEL_API_KEY = os.getenv("MODEL_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

code_gen_prompt = ChatPromptTemplate.from_messages([
    ("system", 
     """
    你是一位精通LCEL【LangChain表达式语言】的编程助手。
    这里是LCEL文档的完整集合：
    --
    {context}
    --
    请根据上述提供的文档回答用户问题。确保你提供的任何代码都可以执行，
    包含所有必要的导入和已定义的变量。请按照以下结构组织你的回答：
    首先描述代码解决方案，然后列出导入语句，最后给出功能完整的代码块。
    以下是用户问题："""),
    ("placeholder", "{message}"),
])

from typing import ClassVar

class code(BaseModel):
    profile: str = Field(description="问题和解决方案的描述")
    imports: str = Field(description="代码块导入语句")
    code: str = Field(description="不包括导入语句的代码块")

llm = ChatDeepSeek(
    api_key=DS_API_KEY,
    base_url="https://api.deepseek.com",
    model="deepseek-chat",
    temperature=0.1,
    max_tokens=1000,
)

llm2 = ChatOpenAI(
    api_key=MODEL_API_KEY,
    base_url=BASE_URL,
    model=MODEL_NAME,
    temperature=0.1,
    max_tokens=1000,
)



code_gen_chain_oai = code_gen_prompt | llm.with_structured_output(code)

question = "如何使用LangChain表达式语言（LCEL）来创建一个简单的聊天机器人？"
solution = code_gen_chain_oai.invoke({
    "context": concatenated_text, 
    "message": [{"role": "user", "content": question}]
})
print(solution)
# solution