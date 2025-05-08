from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate  # New import
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取环境变量
base_url = os.getenv("BASE_URL")
model_api_key = os.getenv("MODEL_API_KEY")
model_name = os.getenv("MODEL_NAME")

# 1. 初始化语言模型
llm = ChatOpenAI(
    base_url=base_url,
    api_key=model_api_key,
    model=model_name,
    temperature=0.1,
    streaming=True  # 启用流式输出
)

# 2. 初始化对话记忆
memory = ConversationBufferMemory()

# 3. 创建自定义提示模板
template = """
你是一个友好的聊天机器人助手。
这是当前的对话历史:
{history}
人类: {input}
AI助手:"""
PROMPT = PromptTemplate(
    input_variables=["history", "input"], 
    template=template
)

# 4. 创建对话链 (使用自定义提示)
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    prompt=PROMPT,  # Use custom prompt
    verbose=True  # 设置为 True 可以看到链的详细运行过程
)

if __name__ == "__main__":
    print("你好！我是一个聊天机器人。输入 '退出' 来结束对话。")
    while True:
        user_input = input("你: ")
        if user_input.lower() == '退出':
            print("机器人: 再见！")
            break
        response = conversation.predict(input=user_input)
        print(f"机器人: {response}")
