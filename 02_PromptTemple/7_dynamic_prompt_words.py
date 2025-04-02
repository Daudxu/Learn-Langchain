# 根据长度动态选择
# 根据语义相似度动态选择
# 使用最大边际相关性进行选择

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core import example_selectors
from langchain_core.example_selectors import LengthBasedExampleSelector
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
import this

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
# 定义例子
examples  = [
    {"input": "happy", "output": "sad"},
    {"input": "tall", "output": "short"},
    {"input": "energetic", "output": "lethargic"},
    {"input": "sunny", "output": "gloomy"},
    {"input": "windy", "output": "calm"},
]
# 定义模板
example_prompt = PromptTemplate(
    input_variables=["input", "output"],
    template="原词: {input}\n反义词: {output}\n",  
)

# 调用长度选择器
example_selectors = LengthBasedExampleSelector(
    examples=examples,
    example_prompt=example_prompt,
    max_length=25, 
)
# 动态选择器
# Update the suffix to use the correct variable name
dynamic_prompt = FewShotPromptTemplate(
    example_selector=example_selectors,
    example_prompt=example_prompt,
    prefix="给出每个输入的反义词",
    suffix="原词: {adjective}\n反义词:",  
    input_variables=["adjective"],  
)

# print(dynamic_prompt)

print(dynamic_prompt.format(adjective="big"))