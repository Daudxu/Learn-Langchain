from langchain_core.prompts import ChatPromptTemplate
from langchain_deepseek import ChatDeepSeek
from bs4 import BeautifulSoup as Soup
from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from typing import ClassVar, List, Dict, Any, Optional
from typing_extensions import TypedDict
from langgraph.graph import END, StateGraph, START
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.runnables import RunnablePassthrough

import os
import json
import re

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
DS_API_KEY = os.getenv("DS_API_KEY")
MODEL_API_KEY = os.getenv("MODEL_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")

# 使用 DeepSeek 而不是 OpenAI，因为之前测试显示 DeepSeek 不会出现 response_format 兼容性问题
llm = ChatDeepSeek(
    api_key=DS_API_KEY,
    base_url="https://api.deepseek.com",
    model="deepseek-chat",
    temperature=0.1,
    max_tokens=1500,
)

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

# print("Number of documents: ", concatenated_text)


code_gen_prompt = ChatPromptTemplate.from_messages([
    ("system", 
     """
    你是一位精通LCEL【LangChain表达式语言】的编程助手。
    这里是LCEL文档的完整集合：
    --
    {context}
    --
    请根据上述提供的文档回答用户问题。确保你提供的任何代码都可以执行，
    包含所有必要的导入和已定义的变量。
    
    你需要输出三个部分:
    1. 解决方案简介 - 简要描述你的解决方案
    2. 导入语句 - 仅包含必要的导入语句
    3. 代码部分 - 实现功能的代码，不包括导入语句
    
    请使用以下格式回复:

    解决方案简介:
    <描述问题和解决方案>
    
    导入语句:
    ```python
    <导入语句>
    ```
    
    代码:
    ```python
    <代码>
    ```
    
    以下是用户问题："""),
    ("placeholder", "{message}"),
])

class code(BaseModel):
    profile: str = Field(description="问题和解决方案的描述")
    imports: str = Field(description="代码块导入语句")
    code: str = Field(description="不包括导入语句的代码块")

# 自定义处理函数，从文本响应中提取所需的代码部分
def extract_components_from_text(text: str) -> Dict[str, str]:
    # 提取解决方案简介
    profile_match = re.search(r"解决方案简介:(.*?)(?=导入语句:|$)", text, re.DOTALL)
    profile = profile_match.group(1).strip() if profile_match else ""
    
    # 提取导入语句
    imports_match = re.search(r"导入语句:.*?```python(.*?)```", text, re.DOTALL)
    imports = imports_match.group(1).strip() if imports_match else ""
    
    # 提取代码部分
    code_match = re.search(r"代码:.*?```python(.*?)```", text, re.DOTALL)
    code_str = code_match.group(1).strip() if code_match else ""
    
    # 如果没有找到特定格式，尝试通用提取
    if not (profile or imports or code_str):
        # 尝试提取任何代码块
        code_blocks = re.findall(r"```python(.*?)```", text, re.DOTALL)
        if len(code_blocks) >= 2:
            imports = code_blocks[0].strip()
            code_str = code_blocks[1].strip()
        elif len(code_blocks) == 1:
            code_str = code_blocks[0].strip()
            # 尝试从代码块中分离导入语句
            import_lines = []
            other_lines = []
            for line in code_str.split('\n'):
                if line.startswith('import ') or line.startswith('from '):
                    import_lines.append(line)
                else:
                    other_lines.append(line)
            imports = '\n'.join(import_lines)
            code_str = '\n'.join(other_lines)
    
    return {
        "profile": profile or "解决方案描述未找到",
        "imports": imports,
        "code": code_str
    }

def process_llm_response(response: str) -> code:
    components = extract_components_from_text(response)
    return code(
        profile=components["profile"],
        imports=components["imports"],
        code=components["code"]
    )

# 重写链的定义，使用更稳健的响应处理
code_gen_chain_oai = (
    code_gen_prompt 
    | llm 
    | StrOutputParser() 
    | (lambda text: process_llm_response(text))
)

# 定义状态
class GraphState(TypedDict):
    """
        图状态：
        error: 错误信息
        message: 消息列表
        generation: 代码解决方案
        iterations: 尝试次数
    """
    error: str
    message: List
    generation: code
    iterations: int

# 最大尝试次数
max_iterations = 3
# 反思
flag = "do not reflect"

def generate(state: GraphState):
        """
        生成代码解决方案

        参数：
          state (dict) 当前图状态
        返回：
           state (dict) 向状态添加新的值，generation
        """
        print("生成代码解决方案")

        # 状态
        message = state["message"]
        iterations = state["iterations"]
        error = state["error"]

        # 因错误重新路由到生成

        if error == "yes":
                message += [
                        {
                        "role": "user",
                        "content": "请重试，调用code工具来构建包含前言、导入和代码块的输出。"
                        }
                ]
        

        # 解决方案
        code_solution = code_gen_chain_oai.invoke({
            "context": concatenated_text, 
            "message": message
        })

        message += [
                {
                    "role": "assistant",
                    "content": f"{code_solution.profile} \n 导入: {code_solution.imports} \n 代码: {code_solution.code}"        
                }
        ]

        # 增加迭代次数

        iterations = iterations + 1
        return{ "generation": code_solution, "message": message, "iterations": iterations}


def code_check(state: GraphState):
        """
        检查代码解决方案

        参数：
          state (dict) 当前图状态
        返回：
           state (dict) 向状态添加新的值，error
        """
        print("检查代码解决方案")

        # 状态
        message = state["message"]
        iterations = state["iterations"]
        error = state["error"]

        # 获得解决方案组件
        code_solution = state["generation"]
        imports = code_solution.imports
        code = code_solution.code

        # 检查导入

        try:
            exec(imports)
        except Exception as e:
            print(f"===导入导入检查:失败===")
            error_message = [{
                  "role": "user",
                  "content": f"你的解决方案未通过导入测试 \n 错误信息: {e}"
            }]
            message += error_message
            return {
                "generation": code_solution,  
                "iterations": iterations,
                "message": message,
                "error": "yes",
            }

        # 无错误
        print("===无代码测试失败===")      
        return {
            "generation": code_solution,
            "iterations": iterations,
            "message": message,
            "error": "no",
        }

def reflect(state: GraphState):
        """
        反思代码解决方案

        参数：
          state (dict) 当前图状态
        返回：
           state (dict) 向状态添加新的值，error
        """
        print("反思代码解决方案")

        # 状态
        message = state["message"]
        iterations = state["iterations"]
        error = state["error"]
        code_solution = state["generation"]

        reflections = code_gen_chain_oai.invoke({
            "context": concatenated_text, 
            "message": message
        })

        message += [
             {
                "role": "assistant",
                "content": f"以下对错误反思: {reflections}"
             }
        ]

        return {
            "generation": code_solution,
            "iterations": iterations,
            "message": message,
        }

def decide_to_finish(state: GraphState):
        """
        决定是否完成

        参数：
          state (dict) 当前图状态
        返回：
           state (dict) 向状态添加新的值，error
        """
        print("决定是否完成")

        # 状态
        iterations = state["iterations"]
        error = state["error"]

        if error == "no" or iterations == max_iterations:
               print("===完成===")
               return "end"
        else:   
                print("===继续===")
                if flag == "reflect":
                    return "reflect"
                else:       
                    return "generate"

# 创建工作流
workflow = StateGraph(GraphState)

workflow.add_node("generate", generate)
workflow.add_node("code_check", code_check)
workflow.add_node("reflect", reflect)

workflow.add_edge(START, "generate")
workflow.add_edge("generate", "code_check")
workflow.add_conditional_edges("code_check", decide_to_finish, {
    "end" : END,
    "reflect" : "reflect",
    "generate" : "generate",
})
workflow.add_edge("reflect", "generate")
app = workflow.compile()

if __name__ == "__main__":
    question = "如何使用LangChain表达式语言（LCEL）来创建一个简单的聊天机器人？"
    solution = app.invoke({
        "message": [{"role": "user", "content": question}],
        "error": "no",
        "iterations": 0,
    })
    print("\n最终解决方案:\n")
    print(solution["generation"].profile)
    print("\n导入:\n")
    print(solution["generation"].imports)
    print("\n代码:\n")
    print(solution["generation"].code)