from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from src.Prompt import PromptClass
from dotenv import load_dotenv
load_dotenv()
import os

redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
print(f"Redis URL: {redis_url}")


class MemoryClass:
    def __init__(self, memorykey="chat_history", model=os.getenv("BASE_MODEL")):
        self.memorykey = memorykey
        self.memory = []
        self.chatmodel = ChatOpenAI(model=model)

    def summary_chain(self, store_message):
        try:
            SystemPrompt = PromptClass().SystemPrompt.format(feelScore=5, who_you_are="")
            Moods = PromptClass().MOODS
            prompt = ChatPromptTemplate.from_messages([
                ("system", SystemPrompt + "\n这是一段你和用户的对话记忆，对其进行总结摘要，摘要使用第一人称'我'，并且提取其中的关键信息，以如下格式返回：\n 总结摘要 | 过去对话关键信息\n例如 用户张三问候我好，我礼貌回复，然后他问我langchain的向量库信息，我回答了他今年的问题，然后他又问了比特币价格。|Langchain, 向量库,比特币价格"),
                ("user", "{input}")
            ])
            chain = prompt | self.chatmodel
            summary = chain.invoke({"input": store_message, "who_you_are": Moods["default"]["roloSet"]})
            return summary
        except KeyError as e:
            print("总结出错")
            print(e)

    def get_memory(self, session_id: str = "session1"):
        try:
            print("session_id:", session_id)
            print("redis_url:", redis_url)
            chat_message_history = RedisChatMessageHistory(
                url=redis_url, session_id=session_id
            )
            # 对超长的聊天记录进行摘要
            store_message = chat_message_history.messages
            if len(store_message) > 80:
                str_message = ""
                for message in store_message:
                    str_message += f"{type(message).__name__}: {message.content}"
                summary = self.summary_chain(str_message)
                chat_message_history.clear()  # 清空原有的对话
                chat_message_history.add_message(summary)  # 保存总结
                print("添加总结后:", chat_message_history.messages)
                return chat_message_history
            else:
                print("go to next step")
                return chat_message_history
        except Exception as e:
            print(e)
            return None

    def set_memory(self, session_id: str = "session1"):
        chat_memory = self.get_memory(session_id=session_id)
        if chat_memory is None:
            print("chat_memory is None")
            # 创建一个默认的 RedisChatMessageHistory 实例
            chat_memory = RedisChatMessageHistory(url=redis_url, session_id=session_id)

        self.memory = ConversationBufferMemory(
            llm=self.chatmodel,
            human_prefix="user",
            ai_prefix="小浪助手",
            memory_key=self.memorykey,
            output_key="output",
            return_messages=True,
            max_token_limit=1000,
            chat_memory=chat_memory,
        )
        return self.memory