# 消息占位符应用

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, prompt
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

prompt_template = ChatPromptTemplate([
   ("system", "你是一个厉害的人工职能助手"),
   MessagesPlaceholder("msge"),
])

result = prompt_template.invoke({"msge": [HumanMessage(content="hi")]})
print(result)