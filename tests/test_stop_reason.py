"""
Tests for stop_reason tool-use agent and tools (Offline, zero API tokens).
"""

import asyncio
import importlib
import pytest
from lib.mock_claude import AsyncMockClaudeClient, MockMessageResponse, MockContentBlock
from lib.response_logger import ResponseTrail

# Import from 1_stop_reason.main dynamically since directory starts with a digit
stop_reason_module = importlib.import_module("1_stop_reason.main")
get_pokemon_tool = stop_reason_module.get_pokemon_tool
fortune_teller_tool = stop_reason_module.fortune_teller_tool
execute_tool = stop_reason_module.execute_tool
run_agent = stop_reason_module.run_agent
TOOLS = stop_reason_module.TOOLS


def test_tools_schema():
    """Verify tool schemas conform to Anthropic tool use format."""
    tool_names = [t["name"] for t in TOOLS]
    assert "get_pokemon" in tool_names
    assert "fortune_teller" in tool_names

    for tool in TOOLS:
        assert "name" in tool
        assert "description" in tool
        assert "input_schema" in tool
        assert tool["input_schema"]["type"] == "object"
        assert "properties" in tool["input_schema"]
        assert "required" in tool["input_schema"]


def test_get_pokemon_tool_found():
    """Test retrieving an existing Pokémon."""
    result = asyncio.run(get_pokemon_tool("pikachu"))
    assert result["found"] is True
    assert result["pokemon"]["name"] == "Pikachu"
    assert result["pokemon"]["type"] == "Electric"
    assert "Static" in result["pokemon"]["abilities"]


def test_get_pokemon_tool_not_found():
    """Test retrieving a non-existent Pokémon."""
    result = asyncio.run(get_pokemon_tool("nonexistent_mon"))
    assert result["found"] is False
    assert "not found" in result["error"]
    assert "available_pokemons" in result


def test_get_pokemon_tool_list_all():
    """Test listing all Pokémon."""
    result = asyncio.run(get_pokemon_tool("all"))
    assert result["found"] is True
    assert result["count"] >= 5
    assert len(result["pokemons"]) == result["count"]


def test_fortune_teller_tool():
    """Test the yes/no oracle fortune teller tool."""
    result = asyncio.run(fortune_teller_tool("Will I pass my Claude Architect certification?"))
    assert "oracle_answer" in result
    assert result["oracle_answer"] in [
        "Yes",
        "Signs point to yes",
        "Most definitely yes",
        "Reply hazy, ask again later",
        "No",
        "Outlook not so good",
    ]
    assert "verdict" in result
    assert "crystal_ball_aura" in result
    assert "lucky_number" in result
    assert 1 <= result["lucky_number"] <= 100


def test_execute_tool():
    """Test the tool dispatcher."""
    poke_res = asyncio.run(execute_tool("get_pokemon", {"name": "charizard"}))
    assert poke_res["found"] is True
    assert poke_res["pokemon"]["name"] == "Charizard"

    fortune_res = asyncio.run(execute_tool("fortune_teller", {"question": "Is today a lucky day?"}))
    assert "oracle_answer" in fortune_res

    err_res = asyncio.run(execute_tool("invalid_tool", {}))
    assert "error" in err_res


def test_run_tool_agent_loop_with_tool(tmp_path):
    """Test agentic loop when Claude requests a tool call (stop_reason='tool_use' -> 'end_turn')."""
    trail = ResponseTrail(path=str(tmp_path / "test_trail.jsonl"))

    # Turn 1: tool_use (calls get_pokemon for Pikachu)
    resp_turn_1 = MockMessageResponse(
        content=[
            MockContentBlock(block_type="text", text="Looking up Pikachu..."),
            MockContentBlock(
                block_type="tool_use",
                name="get_pokemon",
                tool_id="call_123",
                input_data={"name": "pikachu"},
            ),
        ],
        stop_reason="tool_use",
    )

    # Turn 2: end_turn (returns answer based on tool results)
    resp_turn_2 = MockMessageResponse(
        content=[
            MockContentBlock(
                block_type="text",
                text="Pikachu is an Electric type Pokémon with the Static ability.",
            )
        ],
        stop_reason="end_turn",
    )

    client = AsyncMockClaudeClient([resp_turn_1, resp_turn_2])

    result = asyncio.run(
        run_agent(
            prompt="Tell me about Pikachu",
            client=client,
            trail=trail,
            max_turns=3,
        )
    )

    assert "Pikachu is an Electric type" in result
    assert len(client.messages.call_history) == 2


def test_run_tool_agent_loop_direct(tmp_path):
    """Test agentic loop when Claude answers directly (immediate stop_reason='end_turn')."""
    trail = ResponseTrail(path=str(tmp_path / "test_trail.jsonl"))

    resp_direct = MockMessageResponse(
        content=[MockContentBlock(block_type="text", text="Hello there! How can I help you today?")],
        stop_reason="end_turn",
    )

    client = AsyncMockClaudeClient([resp_direct])

    result = asyncio.run(
        run_agent(
            prompt="Hello world",
            client=client,
            trail=trail,
            max_turns=3,
        )
    )

    assert "Hello there!" in result
    assert len(client.messages.call_history) == 1
