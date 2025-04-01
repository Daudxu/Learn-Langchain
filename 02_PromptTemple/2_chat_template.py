# 对话模板应用
from  langchain.prompts import ChatPromptTemplate
chat_template = ChatPromptTemplate.from_messages([
    ("system", "你是一名起名大师，你的名字叫{name}。"),
    ("human", "你好{name}! 你感觉如何？"),
    ("ai", "我很好，谢谢！"),
    ("human", "你叫什么名字？"),
    ("ai", "我叫{name}。"),
    ("human", "{user_input}"),
])

chats = chat_template.format_messages(name="小冰", user_input="你叫什么名字？")
print(chats)