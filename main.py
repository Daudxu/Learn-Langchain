# # ...existing code...
# from mcp_tool import mcp_tool
# from langchain.agents import initialize_agent, AgentType
# from langchain.llms import OpenAI

# # ...existing code...

# llm = OpenAI(openai_api_key="你的API_KEY")
# tools = [mcp_tool]  # 可以和其他工具一起用

# agent = initialize_agent(
#     tools,
#     llm,
#     agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
#     verbose=True
# )


# result = agent.run("请用MCP工具处理这段文本")
# print(result)
# # ...existing code...