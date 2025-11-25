### run the weather_server.py using "pyhon weather_server.py" in command line to activate the server
### then we can use akasha agent to call the tools in MCP server ###

import akasha  # noqa: E402
import dotenv
from llm_clockmate import prompt_create, parse_llm_output
dotenv.load_dotenv()

MODEL = "gemini:gemini-2.5-flash"

prompt = """89+37=?"""
prompt = """tell me the weather in Taipei"""
prompt = """use get_per_day_work_times_by_llm to help me Standardization my work times to JSON for this month"""
system_prompt = prompt_create()
user_prompt = prompt + "\n" + system_prompt
connection_info = {
    "get_per_day_work_times_by_llm": {
        # the first arg is the path of your python file
        "url": "http://localhost:8001/sse",
        "transport": "sse",
    },    
    # "math": {
        # "command": "python",
        # the first arg is the path of your python file
        # "args": ["cal_server.py"],
        # "transport": "stdio",
    # },
    # "weather": {
        # make sure you start your weather server with correct port
        # "url": "http://localhost:8000/sse",
        # "transport": "sse",
    # },
}


## connection_info is the information of multiple MCP servers and  agent can use them to get the tools
## call_mcp_agent will call the agent and return the response
agent = akasha.agents(
    model=MODEL,
    temperature=1.0,
    verbose=True,
    keep_logs=True,
)
response = agent.mcp_agent(connection_info, user_prompt)
agent.save_logs("logs_agent.json")