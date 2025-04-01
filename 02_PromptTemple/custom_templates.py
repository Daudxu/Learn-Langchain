# 自定义提示词模板
from langchain_core.prompts import StringPromptTemplate
from typing import Dict, Any

class CodeExplainerPromptTemplate(StringPromptTemplate):
    """自定义提示词模板，用于解释代码"""
    
    template: str
    
    def format(self, **kwargs) -> str:
        # 使用传入的参数格式化模板
        return self.template.format(**kwargs)
    
    # def _prompt_type(self):
    #     return "code-explainer"

def create_prompt_template(name, age, hobby):
    template = "你好，我叫{name}，我今年{age}岁，我的爱好是{hobby}。"
    return template.format(name=name, age=age, hobby=hobby)

def explain_function(function_name, source_code):
    """
    生成函数解释的提示词
    
    Args:
        function_name: 函数名称
        source_code: 函数源代码
    
    Returns:
        格式化后的提示词
    """
    