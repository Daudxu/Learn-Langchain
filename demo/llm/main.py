from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

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
        max_tokens=1000,
        streaming=True
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个有用的助手。"),
        ("user", "{input}")
    ])

    print("输入 'exit' 退出对话。\n")
    while True:
        user_input = input("你：")
        if user_input.strip().lower() == 'exit':
            print("结束对话。"); break
        print("AI：", end="", flush=True)
        # 直接用 llm.stream() 实现流式输出
        for chunk in llm.stream(prompt.format_messages(input=user_input)):
            print(chunk.content, end="", flush=True)
        print()

if __name__ == "__main__":
    main()