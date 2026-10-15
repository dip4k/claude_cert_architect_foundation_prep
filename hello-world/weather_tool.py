"""SDK tool that exposes a London weather lookup to Claude.

Wires together weather_lookup (fetch) and weather_json_parser (parse) into a
single Claude Agent SDK tool, served via an in-process MCP server.
"""
from claude_agent_sdk import tool, create_sdk_mcp_server

from weather_lookup import get_london_weather
from weather_json_parser import parse_weather_json


@tool(
    "get_london_weather",
    "Look up the current weather for London using a free, open-source "
    "weather API (wttr.in). Takes no arguments.",
    {},
)
async def get_london_weather_tool(args):
    raw = get_london_weather()
    weather = parse_weather_json(raw)

    summary = (
        f"Weather in {weather['city'] or 'London'}: "
        f"{weather['description']}, {weather['temperature_C']}°C "
        f"(feels like {weather['feels_like_C']}°C), "
        f"humidity {weather['humidity']}%, "
        f"wind {weather['wind_speed_kmph']} km/h."
    )

    return {"content": [{"type": "text", "text": summary}]}


weather_server = create_sdk_mcp_server(
    name="weather",
    version="1.0.0",
    tools=[get_london_weather_tool],
)
