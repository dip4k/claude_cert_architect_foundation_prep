import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage

from weather_tool import weather_server


async def main():
    # Agentic loop: streams messages as Claude works
    async for message in query(
        prompt="What is the weather in London right now?",
        options=ClaudeAgentOptions(
            allowed_tools=[
                "Read",
                "Edit",
                "Glob",
                "mcp__weather__get_london_weather",
            ],  # Auto-approve these tools
            permission_mode="acceptEdits",  # Auto-approve file edits
            mcp_servers={"weather": weather_server},  # Register the weather tool server
        ),
    ):
        # Print human-readable output
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)  # Claude's reasoning
                elif hasattr(block, "name"):
                    print(f"Tool: {block.name}")  # Tool being called
        elif isinstance(message, ResultMessage):
            print(f"Done: {message.subtype}")  # Final result


asyncio.run(main())