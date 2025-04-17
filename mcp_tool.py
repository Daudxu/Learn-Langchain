from langchain.tools import Tool
import requests

def call_mcp_api(input_text: str) -> str:
    # 这里替换为你的MCP API地址和参数
    url = "https://your-mcp-endpoint/api"
    payload = {"input": input_text}
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json().get("result", "")

mcp_tool = Tool(
    name="MCP工具",
    func=call_mcp_api,
    description="调用MCP工具处理输入文本"
)
