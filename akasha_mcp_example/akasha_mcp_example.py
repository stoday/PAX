import akasha  # noqa: E402
import dotenv
dotenv.load_dotenv()
MODEL = "gemini:gemini-2.5-flash"

prompt = """89+37=?"""
# prompt = """tell me the weather in Taipei"""
connection_info = {
    "math": {
        "command": "python",
        # the first arg is the path of your python file
        "args": ["cal_server.py"],
        "transport": "stdio",
    },
}

## connection_info is the information of multiple MCP servers and  agent can use them to get the tools
## call_mcp_agent will call the agent and return the response
agent = akasha.agents(
    model=MODEL,
    temperature=1.0,
    verbose=True,
    keep_logs=True,
)
response = agent.mcp_agent(connection_info, prompt)
# agent.save_logs("logs_agent.json")
print("Final response:")
print(response)

