# 字符串模板
from  langchain.prompts import PromptTemplate
prompt = PromptTemplate.from_template("你是一个{name},帮我起1个具有{county}特色的{sex}名字")
prompts = prompt.format(name="起名大师", county="可爱", sex="女孩")
print(prompts)