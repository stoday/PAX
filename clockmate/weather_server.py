# weather_server.py
from mcp.server.fastmcp import FastMCP  # noqa: E402

mcp = FastMCP("Weather", port=8000)


@mcp.tool()
async def get_weather(location: str) -> str:
    """Get weather for location."""
    location = location.lower()
    if location == "taipei" or location == "台北":
        return "It's always rainning in Taipei"
    elif location == "kaohsiung" or location == "高雄":
        return "It's always sunny in Kaohsiung"
    elif location == "new york" or location == "紐約":
        return "It's always sunny in New York"
    else:
        return f"It's cloudy in {location}"


if __name__ == "__main__":
    mcp.run(transport="sse")