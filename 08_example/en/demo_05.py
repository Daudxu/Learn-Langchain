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
        self.word_related_commands = {
            "意思", "详细用法", "固定搭配", "词根词缀", "例句", "出一道选择题"
        }
        self.init_system_prompt()
        
    def init_system_prompt(self):
        """初始化系统提示词"""
        self.system_prompt = f"""
        你是一位专业的英语单词学习助手，当前学习单词为"{self.current_word}"。
        规则：
        1. 当用户输入"{self.current_word}"时，回答其意思并以"你理解这个意思了吗？"结尾；
        2. 当用户输入"详细用法"时，详细解释用法并以"你理解了吗？"结尾；
        3. 当用户输入"固定搭配"时，列举常见搭配并以"你记住这个搭配了吗？"结尾；
        4. 当用户输入"词根词缀"时，解释词根词缀并以"现在你理解了吗？"结尾；
        5. 当用户输入"例句"时，提供例句并以"你能理解这个例句中"{self.current_word}"的用法吗？"结尾；
        6. 当用户输入"出一道选择题"时，设计一道选择题并以"请选择A、B或C。你能找出正确答案吗？"结尾；
        7. 当用户输入选择题答案（A/B/C）时，判断正误并回复；
        8. 对其他输入保持沉默。
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
        self.dialog_history.append({"role": "user", "content": user_prompt})
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        
        payload = {
            "model": MODEL,
            "messages": self.dialog_history,
            "temperature": 0.1,
            "max_tokens": 256,
            "stream": False
        }
        
        try:
            response = requests.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()
            answer = response.json()["choices"][0]["message"]["content"]
            
            # 检查回答是否包含切换单词的欢迎语（异常情况）
            if f"同学你好，针对单词\"{user_prompt}\"" in answer:
                return None
                
            self.dialog_history.append({"role": "assistant", "content": answer})
            return answer
        except Exception as e:
            print(f"API错误: {e}")
            return None
    
    def run(self):
        """运行单词学习助手"""
        print(f"同学你好，针对单词\"{self.current_word}\"，还有什么想要了解的，我可以为你详细讲解哦~你也可以点击对话框上方的选项来进行提问。")
        
        while True:
            user_input = input("\n你想问什么？").strip()
            
            if user_input.lower() == "退出":
                print("感谢使用单词学习助手！")
                break
                
            # 处理单词切换
            if self.is_valid_english_word(user_input) and user_input.lower() != self.current_word.lower():
                print(self.switch_word(user_input.lower()))
                continue
                
            # 处理与当前单词相同的输入
            if user_input.lower() == self.current_word.lower():
                response = self.get_api_response(self.current_word)
                if response:
                    print(f"AI: {response}")
                else:
                    print(f"AI: 这个单词的意思是“男孩”，你理解这个意思了吗？")
                continue
                
            # 处理单词相关命令
            if user_input in self.word_related_commands:
                response = self.get_api_response(user_input)
                if response:
                    print(f"AI: {response}")
                else:
                    # 根据命令类型提供默认回答
                    if user_input == "详细用法":
                        print(f"AI: 在描述某个具体的男孩时，“{self.current_word}”可以直接用...你理解了吗？")
                    elif user_input == "固定搭配":
                        print(f"AI: “{self.current_word}”常见的固定搭配有...你记住这个搭配了吗？")
                    elif user_input == "词根词缀":
                        print(f"AI: “{self.current_word}”这个单词没有常见的词根词缀哦...现在你理解了吗？")
                    elif user_input == "例句":
                        print(f"AI: 那老师给你一个例句 “The {self.current_word} is playing football.”...你能理解吗？")
                    elif user_input == "出一道选择题":
                        print(f"AI: 以下哪个句子中“{self.current_word}”的用法是正确的呢？A. ...  B. ... 请选择A、B或C。你能找出正确答案吗？")
                    elif user_input == "意思":
                        print(f"AI: 这个单词的意思是“男孩”，你理解这个意思了吗？")
                continue
                
            # 处理选择题答案
            if len(user_input) == 1 and user_input.upper() in {'A', 'B', 'C'}:
                response = self.get_api_response(user_input)
                if response:
                    print(f"AI: {response}")
                else:
                    print(f"AI: 回答正确！“{self.current_word}”在这里是...你理解了吗？")
                continue
                
            # 处理无关问题
            print(f"咱们还是专注于\"{self.current_word}\"这个单词吧，你在这个单词上还有什么疑问吗？")

if __name__ == "__main__":
    tutor = VocabularyTutor()
    tutor.run()