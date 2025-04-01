from langchain import OpenAI, LLMChain, PromptTemplate
import os

# 设置OpenAI API密钥
os.environ["OPENAI_API_KEY"] = "your_openai_api_key"

# 定义Prompt模板
template = """
你是一个NPC代理，你的名字是{npc_name}。
你有以下特征：{npc_traits}。
你当前的对话背景是：{context}。
用户对你说：{user_input}
你的回答是：
"""

prompt = PromptTemplate(
    input_variables=["npc_name", "npc_traits", "context", "user_input"],
    template=template,
)

# 初始化LLM模型
llm = OpenAI(temperature=0.7)  # 你可以选择不同的温度值来控制输出的随机性

# 创建LLM链
chain = LLMChain(llm=llm, prompt=prompt)

# 定义NPC的特征和背景
npc_name = "艾丽丝"
npc_traits = "友好、好奇、乐于助人"
context = "在一个神秘的森林里，你遇到了一位旅行者。"

# 与NPC交互
def interact_with_npc(user_input):
    response = chain.run(npc_name=npc_name, npc_traits=npc_traits, context=context, user_input=user_input)
    return response

# 示例对话
print("NPC: 你好，旅行者！我是艾丽丝。")
while True:
    user_input = input("你: ")
    if user_input.lower() in ["退出", "再见"]:
        print("NPC: 再见，祝你旅途愉快！")
        break
    response = interact_with_npc(user_input)
    print(f"NPC: {response}")
