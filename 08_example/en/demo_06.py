import requests
import json
import os
from dotenv import load_dotenv
import re

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
        self.init_system_prompt()
        
    def init_system_prompt(self):
        """初始化系统提示词"""
        self.system_prompt = f"""
        你是一位专业的英语单词学习助手，当前学习单词为"{self.current_word}"。
        规则：
        1. 用户输入单词本身时，回答其意思并以"你理解这个意思了吗？"结尾；
        2. 用户输入"详细用法"时，详细解释只写1~2种用法并以"你理解了吗？"结尾；
        3. 用户输入"固定搭配"时，列举常见搭配并以"你记住这个搭配了吗？"结尾；
        4. 用户输入"词根词缀"时，解释词根词缀并以"现在你理解了吗？"结尾；
        5. 用户输入"例句"时，提供例句1种并以"你能理解这个例句中"{self.current_word}"的用法吗？"结尾；
        6. 用户输入"出一道选择题"时，设计一道选择题并以"请选择A、B或C。你能找出正确答案吗？"结尾；
        7. 用户输入选择题答案（A/B/C）时，判断正误并回复；
        8. 只要问与当前单词无关的问题，均回答 咱们还是专注于“{self.current_word}”这个单词吧，你在这个单词上还有什么疑问吗？。
        9. 禁止切换单词，若用户输入其他英文单词，回复：咱们还是专注于“{self.current_word}”这个单词吧，你在这个单词上还有什么疑问吗？。
        """
        self.dialog_history = [{"role": "system", "content": self.system_prompt}]
        
    def is_valid_english_word(self, text):
        """检测是否为有效英文单词（只允许英文字母，且2-20位）"""
        return bool(re.fullmatch(r"[a-zA-Z]{2,20}", text))
        
    def get_api_response(self, user_prompt):
        """调用豆包API获取回答，严格过滤异常回复"""
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
            
            # 关键过滤：防止AI将指令或无关单词误判为新单词
            if (
                f"同学你好，针对单词\"{user_prompt}\"" in answer
                or (self.is_valid_english_word(user_prompt) and user_prompt != self.current_word.lower())
            ):
                return None
                
            self.dialog_history.append({"role": "assistant", "content": answer})
            return answer
        except Exception as e:
            print(f"API错误: {e}")
            return None
    
    def classify_user_input(self, user_input):
        """智能分类用户输入类型"""
        user_input = user_input.lower()
        
        # 检查是否为退出命令
        if user_input in {"退出", "结束", "再见"}:
            return "exit"
            
        # 优先处理单词相关指令
        if any(keyword in user_input for keyword in {"意思", "用法", "搭配", "词根", "例句", "选择题"}):
            return "word_related"
            
        # 检查是否为当前单词（查询意思）
        if user_input == self.current_word.lower():
            return "word_meaning"
            
        # 检查是否为选择题答案
        if len(user_input) == 1 and user_input in {'a', 'b', 'c'}:
            return "answer"
            
        # 其他情况视为无关问题（包括其他英文单词）
        return "irrelevant"
    
    def run(self):
        """运行单词学习助手"""
        # 初始化时获取AI欢迎语
        welcome_prompt = f"同学你好，针对单词\"{self.current_word}\"，还有什么想要了解的？"
        welcome_response = self.get_api_response(welcome_prompt)
        
        if welcome_response:
            print(welcome_response)
        else:
            # API异常时使用默认欢迎语
            print(f"同学你好，针对单词\"{self.current_word}\"，还有什么想要了解的，我可以为你详细讲解哦~你也可以输入指令（如'意思'/'用法'）。")
        
        while True:
            user_input = input("\n你想问什么？").strip()
            input_type = self.classify_user_input(user_input)
            
            if input_type == "exit":
                print("感谢使用单词学习助手！")
                break
                
            if input_type in ["word_meaning", "word_related", "answer"]:
                response = self.get_api_response(user_input)
                if response:
                    print(f"AI: {response}")
                else:
                    # API异常时使用固定回复
                    print(f"咱们还是专注于\"{self.current_word}\"这个单词吧，你在这个单词上还有什么疑问吗？")
                continue
                
            # 所有其他情况（包括切换单词请求）都回复固定提示
            print(f"咱们还是专注于\"{self.current_word}\"这个单词吧，你在这个单词上还有什么疑问吗？")

if __name__ == "__main__":
    # 初始化时传入单词，后续无法切换
    tutor = VocabularyTutor("apple")  # 这里可以修改为任何单词
    tutor.run()