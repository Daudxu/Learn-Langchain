from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.tools import tool
from langchain.agents import AgentExecutor, create_structured_chat_agent
import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 加载环境变量
load_dotenv()

base_url = os.getenv("BASE_URL")
model_api_key = os.getenv("MODEL_API_KEY")
model_name = os.getenv("MODEL_NAME")

llm = ChatOpenAI(
    base_url=base_url,
    api_key=model_api_key,
    model=model_name,
    temperature=0.1,
    streaming=True
)

current_word = {"word": None}

@tool
def word_meaning(word: str) -> str:
    """获取英文单词的中文释义"""
    prompt = PromptTemplate(
        input_variables=["word"],
        template="请用简明中文解释英文单词：{word}，只返回最常用的中文释义，不要例句。"
    )
    current_word["word"] = word
    return llm.invoke(prompt.format(word=word)).strip()

@tool
def detailed_usage(word: str) -> str:
    """获取英文单词的详细用法"""
    prompt = PromptTemplate(
        input_variables=["word"],
        template="请用亲切口语化的中文详细说明单词“{word}”的用法，包括单复数、常见语境、语法等，举例说明，结尾加一句“你理解了吗？”"
    )
    return llm.invoke(prompt.format(word=word)).strip()

@tool
def fixed_collocations(word: str) -> str:
    """获取英文单词的固定搭配"""
    prompt = PromptTemplate(
        input_variables=["word"],
        template="请列举“{word}”常见的固定搭配，每个搭配后用括号补充中文含义，风格亲切，结尾加一句“你记住了吗？”"
    )
    return llm.invoke(prompt.format(word=word)).strip()

@tool
def word_roots_affixes(word: str) -> str:
    """获取英文单词的词根词缀"""
    prompt = PromptTemplate(
        input_variables=["word"],
        template="请判断“{word}”是否有常见词根词缀，如果有请说明并举例，没有就说明没有，风格亲切，结尾加一句“你理解了吗？”"
    )
    return llm.invoke(prompt.format(word=word)).strip()

@tool
def example_sentences(word: str) -> str:
    """获取英文单词的例句"""
    prompt = PromptTemplate(
        input_variables=["word"],
        template="请用“{word}”造一个简单英文例句，并给出中文翻译，风格亲切，结尾加一句“你能理解这个例句中“{word}”的用法吗？”"
    )
    return llm.invoke(prompt.format(word=word)).strip()

@tool
def multiple_choice(word: str) -> str:
    """针对英文单词出一道选择题"""
    prompt = PromptTemplate(
        input_variables=["word"],
        template="请针对“{word}”设计一道英文用法选择题，4个选项，只有一个正确，风格亲切，结尾加“回复选项字母，老师会告诉你答案哦！”"
    )
    return llm.invoke(prompt.format(word=word)).strip()

TOOLS = [word_meaning, detailed_usage, fixed_collocations, word_roots_affixes, example_sentences, multiple_choice]

system_prompt = (
    "你是单词学习小助手～每次会专注陪你学习一个英文单词哦！\n"
    "【对话规则】\n"
    "❶ 请先输入一个英文单词（如boy、apple），我会先告诉你词义，然后陪你深入学习\n"
    "❷ 全程围绕该单词展开，你可以随时提问：详细用法、固定搭配、词根词缀、例句、选择题\n"
    "❸ 其他无关问题会礼貌引导回单词学习，记得要专注哦～\n"
    "【交互语气参考】\n"
    "✨ 回复用亲切的口语化表达，比如“同学你好”“老师考考你”\n"
    "✨ 每个功能模块后主动询问理解情况，用“你理解了吗？”“记住了吗？”引导互动\n"
    "✨ 遇到无关问题时，温柔提醒：“咱们还是专注于[单词]的学习吧～”\n"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
]).partial(
    tools="\n".join([f"{tool.name}: {tool.description}" for tool in TOOLS]),
    tool_names=", ".join([tool.name for tool in TOOLS])
)

agent = create_structured_chat_agent(
    llm=llm,
    tools=TOOLS,
    prompt=prompt
)

agent_executor = AgentExecutor(agent=agent, tools=TOOLS, verbose=True)

def main():
    print("欢迎使用单词学习小助手！输入 exit 退出。")
    while True:
        user_input = input("请输入一个英文单词或功能指令（详细用法/固定搭配/词根词缀/例句/出一道选择题）：")
        if user_input.lower() == 'exit':
            print("再见！")
            break
        # 如果还没有单词，优先当作单词释义
        if current_word["word"] is None or user_input.isalpha() and user_input.isascii():
            result = agent_executor.invoke({
                "input": f"{user_input} 的中文释义是什么？",
                "intermediate_steps": []
            })
        else:
            # 其它功能直接交给 agent 解析
            result = agent_executor.invoke({
                "input": user_input,
                "intermediate_steps": []
            })
        print(result["output"])

if __name__ == "__main__":
    main()
