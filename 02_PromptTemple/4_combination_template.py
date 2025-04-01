# 组合模板
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

sy = SystemMessage(
    content="你是一个人工职能助手",
    additeional_kwargs={
        "助手名字": "小助手"
     }
    )

hu = HumanMessage(
    content="请问你叫什么？"
)

ai = AIMessage(
    content="我叫小助手" 
)

# 创建消息列表并赋值给变量
messages = [sy, hu, ai]

print(messages)