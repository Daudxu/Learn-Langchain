# FewShot 示例 大模型学习示例
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate

load_dotenv()

base_url = os.getenv("BASE_URL")
model_api_key = os.getenv("MODEL_API_KEY")
model_name = os.getenv("MODEL_NAME")

llm = ChatOpenAI(
    base_url=base_url,
    api_key=model_api_key,  # 确保这个密钥是有效的
    model=model_name,  # type: ignore
    temperature=0.1,   # type: ignore
    max_tokens=1000,  # type: ignore
    streaming=True
)


# 例子
examples = [
    {"input": "2 👋 2", "output": "4"},
    {"input": "2 👋 3", "output": "6"}, 
]

# 例子模板
example_prompt = ChatPromptTemplate.from_messages([
    ("human", "{input}"),
    ("ai", "{output}"),
])

# 动态 few-shot 提示
few_shot_prompt = FewShotChatMessagePromptTemplate(
    examples=examples,
    example_prompt=example_prompt
)

# 格式化 few-shot 提示
print(few_shot_prompt.invoke({}).to_messages())

# 最终提示
final_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个数学老师"),
    few_shot_prompt,
    ("human", "{input}"), 
])

chain = final_prompt | llm
resault = chain.invoke({"input": "5 👋 5"})
print(resault)