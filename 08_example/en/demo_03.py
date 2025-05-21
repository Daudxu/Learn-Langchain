import requests
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 豆包API配置
API_KEY = os.getenv("ARK_API_KEY")
API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
MODEL = "doubao-1.5-pro-32k-250115"

class VocabularyTutor:
    def __init__(self, initial_word="boy"):
        self.current_word = initial_word
        self.dialog_history = []
        self.question_types = {
            "意思", "详细用法", "固定搭配", "词根词缀", "例句", "出一道选择题"
        }
        self.init_system_prompt()
        
    def init_system_prompt(self):
        """初始化系统提示词，严格定义AI回复格式"""
        self.system_prompt = f"""
        你是一位专业的英语单词学习助手，当前学习单词为"{self.current_word}"。
        规则：
        1. 当用户输入"意思"时，回答单词的中文意思，并以"你理解这个意思了吗？"结尾；
        2. 当用户输入"详细用法"时，详细解释用法，并以"你理解了吗？"结尾；
        3. 当用户输入"固定搭配"时，列举常见搭配，并以"你记住这个搭配了吗？"结尾；
        4. 当用户输入"词根词缀"时，解释词根词缀，并以"现在你理解了吗？"结尾；
        5. 当用户输入"例句"时，提供例句，并以"你能理解这个例句中"{self.current_word}"的用法吗？"结尾；
        6. 当用户输入"出一道选择题"时，设计一道选择题，并以"请选择A、B或C。你能找出正确答案吗？"结尾；
        7. 当用户输入选择题答案（A/B/C）时，判断正误并回复；
        8. 当用户输入有效英文单词时，切换学习内容并提示；
        9. 对于其他输入，保持沉默。
        请严格遵循以上规则，保持回答简洁。
        """
        self.dialog_history = [{"role": "system", "content": self.system_prompt}]
        
    def is_valid_english_word(self, text):
        """检测是否为有效英文单词"""
        return text.isalpha() and 2 <= len(text) <= 20
        
    def switch_word(self, new_word):
        """切换学习单词并重置对话历史"""
        self.current_word = new_word
        self.init_system_prompt()
        return f"同学你好，针对单词\"{new_word}\"，还有什么想要了解的，我可以为你详细讲解哦~你也可以点击对话框上方的选项来进行提问。"
        
    def get_api_response(self, user_prompt):
        """调用豆包API获取回答"""
        # 添加用户提问到对话历史
        self.dialog_history.append({"role": "user", "content": user_prompt})
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        
        payload = {
            "model": MODEL,
            "messages": self.dialog_history,
            "temperature": 0.1,  # 确保回答确定性
            "max_tokens": 256,
            "stream": False  # 非流式输出，确保完整回答
        }
        
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()
            answer = response.json()["choices"][0]["message"]["content"]
            
            # 添加AI回答到对话历史
            self.dialog_history.append({"role": "assistant", "content": answer})
            return answer
        except Exception as e:
            print(f"API调用错误: {e}")
            return f"抱歉，暂时无法回答关于\"{self.current_word}\"的问题，请重试。"
    
    def process_user_input(self, user_input):
        """处理用户输入，区分与单词相关的问题和无关问题"""
        # 检查是否为退出命令
        if user_input.lower() == "退出":
            return "exit", None
            
        # 检查是否为切换单词请求
        if self.is_valid_english_word(user_input) and user_input.lower() != self.current_word:
            return "switch_word", user_input.lower()
            
        # 检查是否为预定义的问题类型
        if any(keyword in user_input for keyword in self.question_types):
            return "word_related", user_input
            
        # 检查是否为选择题答案
        if len(user_input) == 1 and user_input.upper() in {'A', 'B', 'C'}:
            return "answer", user_input.upper()
            
        # 其他情况视为无关问题
        return "irrelevant", user_input
            
    def run(self):
        """运行单词学习助手"""
        # 输出初始欢迎语
        print(f"同学你好，针对单词\"{self.current_word}\"，还有什么想要了解的，我可以为你详细讲解哦~你也可以点击对话框上方的选项来进行提问。")
        
        while True:
            user_input = input("\n你想问什么？").strip()
            
            input_type, content = self.process_user_input(user_input)
            
            if input_type == "exit":
                print("感谢使用单词学习助手，祝你学习进步！")
                break
                
            if input_type == "switch_word":
                print(self.switch_word(content))
                continue
                
            if input_type == "irrelevant":
                print(f"咱们还是专注于\"{self.current_word}\"这个单词吧，你在这个单词上还有什么疑问吗？")
                continue
                
            # 对于与单词相关的问题和选择题答案，调用API获取回答
            response = self.get_api_response(content)
            print(f"AI: {response}")

if __name__ == "__main__":
    # 可以指定默认单词，默认为"boy"
    tutor = VocabularyTutor(initial_word="boy")
    tutor.run()