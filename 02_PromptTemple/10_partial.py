# 使用Partial实战部分格式化效果
from datetime import datetime
from langchain_core.prompts import PromptTemplate

def _get_date_time():
    now = datetime.now()
    return now.strftime("%m/%d/%Y, %H:%M:%S")

prompt = PromptTemplate(
    template="tell me a {adjective} joke about the day {date}.",
    input_variables=["adjective", "date"],
)

partial_prompt = prompt.partial(date=_get_date_time())
print(partial_prompt)
print(partial_prompt.format(adjective="funny"))
