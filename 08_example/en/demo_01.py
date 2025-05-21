import requests
import json
import os
from dotenv import load_dotenv
from collections import defaultdict

# 加载环境变量
load_dotenv()

# 豆包API配置
API_KEY = os.getenv("ARK_API_KEY")
API_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
MODEL = "doubao-1.5-pro-32k-250115"

class VocabularyTutor:
    def __init__(self):
        self.current_word = "apple"
        self.dialog_history = []  # 完整对话历史
        self.word_stats = defaultdict(lambda: {"queries": 0, "correct": 0})  # 单词学习统计
        self.init_system_prompt()
        self.setup_user_commands()
        
    def init_system_prompt(self):
        """初始化系统提示词"""
        self.system_prompt = f"""
        你是一位专业的英语单词学习助手，当前学习单词为"{self.current_word}"。
        规则：
        1. 当用户输入有效英文单词时，自动切换学习内容；
        2. 当用户输入"统计"时，展示当前单词的学习进度；
        3. 当用户输入"帮助"时，显示使用指南；
        4. 当用户输入"重置"时，重置当前单词的学习统计；
        5. 当用户输入选择题答案时，判断正误并更新统计；
        6. 其他输入按常规问题处理。
        请保持回答简洁，并在每轮结束时以疑问句确认用户理解。
        """
        self.dialog_history = [{"role": "system", "content": self.system_prompt}]
        
    def setup_user_commands(self):
        """设置用户命令映射"""
        self.user_commands = {
            "统计": self.show_stats,
            "帮助": self.show_help,
            "重置": self.reset_stats,
        }
        
    def is_valid_english_word(self, text):
        """更严格的英文单词检测"""
        if not text.isalpha():
            return False
        if len(text) < 2 or len(text) > 20:
            return False
        vowels = {'a', 'e', 'i', 'o', 'u'}
        return any(char in vowels for char in text.lower())
        
    def switch_word(self, new_word):
        """切换学习单词并重置对话历史"""
        self.current_word = new_word
        self.init_system_prompt()
        return f"✅ 已切换至单词：{new_word}"
        
    def show_stats(self):
        """显示学习统计"""
        stats = self.word_stats[self.current_word]
        return f"📊 单词 '{self.current_word}' 的学习统计：\n" \
               f"   练习次数：{stats['queries']}\n" \
               f"   正确率：{stats['correct']}/{stats['queries']} ({self._calculate_accuracy(stats):.1f}%)\n" \
               "需要我继续讲解这个单词吗？"
               
    def _calculate_accuracy(self, stats):
        """计算正确率"""
        if stats["queries"] == 0:
            return 0
        return stats["correct"] / stats["queries"] * 100
        
    def reset_stats(self):
        """重置学习统计"""
        self.word_stats[self.current_word] = {"queries": 0, "correct": 0}
        return f"🔄 已重置单词 '{self.current_word}' 的学习统计。是否继续学习？"
        
    def show_help(self):
        """显示帮助信息"""
        return """
        📘 使用指南：
        1. 输入英文单词（如'apple'）：切换学习内容
        2. 输入问题（如'用法'/'例句'）：获取单词详解
        3. 输入'统计'：查看当前单词学习进度
        4. 输入'重置'：重置当前单词学习统计
        5. 输入'退出'：结束学习会话
        6. 输入选择题答案（如'A'）：提交答案
        
        现在想继续学习还是切换单词？
        """
        
    def process_user_input(self, user_input):
        """处理用户输入，区分命令和常规问题"""
        # 检查是否为命令
        if user_input in self.user_commands:
            return "command", user_input
            
        # 检查是否为选择题答案
        if len(user_input) == 1 and user_input.upper() in {'A', 'B', 'C', 'D'}:
            return "answer", user_input.upper()
            
        # 检查是否为有效英文单词
        if self.is_valid_english_word(user_input):
            return "switch_word", user_input.lower()
            
        # 常规问题
        return "question", user_input
        
    def update_answer_stats(self, user_answer):
        """更新选择题答案统计"""
        # 从最后一轮对话中提取正确答案（需要模型配合特定格式）
        last_assistant_msg = next(
            (msg for msg in reversed(self.dialog_history) 
             if msg["role"] == "assistant"), 
            None
        )
        
        if not last_assistant_msg:
            return "无法找到上一轮问题，请尝试其他问题。"
            
        # 简单模式匹配提取正确答案（实际需根据模型回答格式调整）
        correct_answer = None
        for line in last_assistant_msg["content"].split('\n'):
            if "正确答案是" in line:
                correct_answer = line.split("正确答案是")[-1].strip()[0].upper()
                break
                
        if not correct_answer:
            return "抱歉，我无法验证这个问题的答案。是否需要继续学习？"
            
        is_correct = user_answer == correct_answer
        stats = self.word_stats[self.current_word]
        stats["queries"] += 1
        if is_correct:
            stats["correct"] += 1
            
        feedback = "✅ 回答正确！" if is_correct else f"❌ 回答错误，正确答案是 {correct_answer}。"
        return f"{feedback} 你已完成 {stats['queries']} 次练习，正确率为 {self._calculate_accuracy(stats):.1f}%。需要继续练习吗？"
        
    def get_api_response(self, user_prompt):
        """调用豆包API获取流式回答"""
        self.dialog_history.append({"role": "user", "content": user_prompt})
        
        # 限制对话历史长度
        if len(self.dialog_history) > 11:
            self.dialog_history = [self.dialog_history[0]] + self.dialog_history[-10:]
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        
        payload = {
            "model": MODEL,
            "messages": self.dialog_history,
            "temperature": 0.1,
            "max_tokens": 512,
            "stream": True
        }
        
        try:
            response = requests.post(API_URL, headers=headers, data=json.dumps(payload), stream=True)
            response.raise_for_status()
            
            full_response = ""
            print("\r助手: ", end="", flush=True)
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')[6:]
                    if line != "[DONE]":
                        try:
                            data = json.loads(line)
                            content = data['choices'][0]['delta'].get('content', '')
                            print(content, end="", flush=True)
                            full_response += content
                        except:
                            print(f"\n⚠️ 解析错误: {line}")
            
            print()
            self.dialog_history.append({"role": "assistant", "content": full_response})
            return full_response
        except Exception as e:
            print(f"\n⚠️ API错误: {e}")
            return "抱歉，暂时无法回答，请重试。"
    
    def run(self):
        """运行单词学习助手"""
        print(f"🎓 欢迎使用单词学习助手！当前学习单词：{self.current_word}")
        print("📝 输入规则：英文单词（如'apple'）切换学习内容，问题（如'用法'）获取解答，'退出'结束")
        
        while True:
            user_input = input("\n你想了解什么？").strip()
            
            if user_input.lower() == "退出":
                self.show_final_stats()
                print("感谢使用单词学习助手，祝你学习进步！")
                break
                
            input_type, content = self.process_user_input(user_input)
            
            if input_type == "command":
                print(self.user_commands[content]())
            elif input_type == "answer":
                print(self.update_answer_stats(content))
            elif input_type == "switch_word":
                print(self.switch_word(content))
            else:
                self.get_api_response(content)
                
    def show_final_stats(self):
        """显示最终学习统计"""
        print("\n📋 学习总结：")
        for word, stats in self.word_stats.items():
            if stats["queries"] > 0:
                print(f"  - {word}: 练习 {stats['queries']} 次，正确率 {self._calculate_accuracy(stats):.1f}%")

if __name__ == "__main__":
    tutor = VocabularyTutor()
    tutor.run()