#!/usr/bin/env python
from dingtalk_stream import AckMessage, ChatbotMessage, DingTalkStreamClient, Credential,ChatbotHandler,CallbackMessage
from src.Agents import AgentClass
from src.Storage import add_user
from dotenv import load_dotenv as _load_dotenv
_load_dotenv()
import os
import logging


user_storage = {}

class EchoTextHandler(ChatbotHandler):
    def __init__(self):
        super(ChatbotHandler, self).__init__()

    async def process(self, callback: CallbackMessage):
        incoming_message = ChatbotMessage.from_dict(callback.data)
        print(incoming_message)
        print(callback.data)
        text = incoming_message.text.content.strip()
        userid = callback.data['senderStaffId']
        add_user("userid",userid)
        msg = AgentClass().run_agent(text)
        print(msg)
        self.reply_text(msg['output'], incoming_message)
        return AckMessage.STATUS_OK, 'OK'



def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("dingtalk_connection.log")
        ]
    )
    return logging.getLogger("DingTalk")

def main():
    logger = setup_logging()
    logger.info("Starting DingTalk Stream Client")
    # 从环境变量中获取钉钉的app id和app secret
    logger.info(f"App ID: {os.getenv('DINGDING_ID')}")
    logger.info(f"Using credentials to connect to DingTalk")
    
    try:
        credential = Credential(os.getenv("DINGDING_ID"), os.getenv("DINGDING_SECRET"))
        client = DingTalkStreamClient(credential)
        logger.info("DingTalk client created successfully")
        
        # 注册回调处理器
        client.register_callback_handler(ChatbotMessage.TOPIC, EchoTextHandler())
        logger.info("Registered callback handler for ChatbotMessage")
        
        # 启动客户端
        logger.info("Starting DingTalk client...")
        client.start_forever()
    except Exception as e:
        logger.error(f"Error connecting to DingTalk: {e}", exc_info=True)


if __name__ == '__main__':
    main()