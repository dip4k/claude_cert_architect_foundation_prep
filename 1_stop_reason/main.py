"""
Async Tool Use & Stop Reason Agentic Loop using Anthropic Python SDK
WITH RESPONSE TRAIL LOGGING

Reference: https://platform.claude.com/docs/en/agents-and-tools/tool-use/build-a-tool-using-agent

Demonstrates:
- Asynchronous client usage with `anthropic.AsyncAnthropic`.
- Asynchronous tool execution with concurrent multi-tool handling (`asyncio.gather`).
- Handling `response.stop_reason` ('tool_use', 'end_turn', 'max_tokens', etc.).
- The asynchronous agentic loop feeding `tool_result` blocks back to Claude.
- Response trail logging for audit and offline replay (NEW)

Response trails enable:
  - Audit trail of all API interactions
  - Offline replay without re-running the API
  - Performance analysis (latency tracking)
  - Debugging agent behavior
"""

import os
import sys
from pathlib import Path
import json
import time
import asyncio
import uuid
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

# Ensure repository root is on sys.path so 'lib' can be resolved when executing directly
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import anthropic
from lib.response_logger import ResponseTrail, replay_trail, get_agent_trail_path

# Load API key from .env if available
load_dotenv()


# ==============================================================================
# 1. Async Tool Implementations (Python functions)
# ==============================================================================

POKEMON_DATABASE: Dict[str, Dict[str, Any]] = {
    "pikachu": {
        "name": "Pikachu",
        "type": "Electric",
        "category": "Mouse Pokémon",
        "base_stats": {"hp": 35, "attack": 55, "defense": 40, "speed": 90},
        "abilities": ["Static", "Lightning Rod"],
        "signature_moves": ["Thunderbolt", "Quick Attack", "Volt Tackle"],
        "fun_fact": "When several Pikachu gather, electricity can cause thunderous storms.",
    },
    "charizard": {
        "name": "Charizard",
        "type": "Fire / Flying",
        "category": "Flame Pokémon",
        "base_stats": {"hp": 78, "attack": 84, "defense": 78, "speed": 100},
        "abilities": ["Blaze", "Solar Power"],
        "signature_moves": ["Flamethrower", "Fire Blast", "Air Slash"],
        "fun_fact": "It spits fire hot enough to melt boulders. Known to cause forest fires accidentally.",
    },
    "bulbasaur": {
        "name": "Bulbasaur",
        "type": "Grass / Poison",
        "category": "Seed Pokémon",
        "base_stats": {"hp": 45, "attack": 49, "defense": 49, "speed": 45},
        "abilities": ["Overgrow", "Chlorophyll"],
        "signature_moves": ["Vine Whip", "Razor Leaf", "Solar Beam"],
        "fun_fact": "A strange seed was planted on its back at birth and grows with this Pokémon.",
    },
    "blastoise": {
        "name": "Blastoise",
        "type": "Water",
        "category": "Shellfish Pokémon",
        "base_stats": {"hp": 79, "attack": 83, "defense": 100, "speed": 78},
        "abilities": ["Torrent", "Rain Dish"],
        "signature_moves": ["Hydro Pump", "Water Gun", "Skull Bash"],
        "fun_fact": "The rocket cannons on its shell fire water jets capable of punching holes through steel.",
    },
    "gengar": {
        "name": "Gengar",
        "type": "Ghost / Poison",
        "category": "Shadow Pokémon",
        "base_stats": {"hp": 60, "attack": 65, "defense": 60, "speed": 110},
        "abilities": ["Cursed Body"],
        "signature_moves": ["Shadow Ball", "Sludge Bomb", "Hypnosis"],
        "fun_fact": "If you feel a sudden chill, Gengar is hiding nearby stealing the warmth.",
    },
    "mewtwo": {
        "name": "Mewtwo",
        "type": "Psychic",
        "category": "Genetic Pokémon",
        "base_stats": {"hp": 106, "attack": 110, "defense": 90, "speed": 130},
        "abilities": ["Pressure", "Unnerve"],
        "signature_moves": ["Psystrike", "Psychic", "Aura Sphere"],
        "fun_fact": "Created after years of gene-splicing experiments, its power is unmatched.",
    },
}

FORTUNE_RESPONSES = [
    {"answer": "Yes", "verdict": "The stars align favorably! Destiny smiles upon your quest.", "aura": "Golden Light"},
    {"answer": "Signs point to yes", "verdict": "Encouraging omens reveal themselves in the mists.", "aura": "Emerald Glow"},
    {"answer": "Most definitely yes", "verdict": "Unquestionably! The cosmic energies clear your path.", "aura": "Radiant Sapphire"},
    {"answer": "Reply hazy, ask again later", "verdict": "Cosmic currents are turbulent right now. Meditate and ask once more.", "aura": "Smoky Quartz"},
    {"answer": "No", "verdict": "The crystal sphere darkens. Obstacles lie directly ahead.", "aura": "Midnight Obsidian"},
    {"answer": "Outlook not so good", "verdict": "The shadows whisper caution: now is not the right time.", "aura": "Crimson Spark"},
]

async def get_pokemon_tool(name: str, type: Optional[str] = None) -> Dict[str, Any]:
    """Async Tool: Returns info for a specific Pokemon or lists available ones."""
    # Simulate async I/O (e.g., database or network call)
    await asyncio.sleep(0.01)

    query = name.strip().lower()

    if query in ["all", "list"]:
        matches = list(POKEMON_DATABASE.values())
        if type:
            filter_type = type.strip().lower()
            matches = [p for p in matches if filter_type in p["type"].lower()]
        return {
            "found": True,
            "count": len(matches),
            "pokemons": [
                {"name": p["name"], "type": p["type"], "abilities": p["abilities"]}
                for p in matches
            ],
        }

    if query in POKEMON_DATABASE:
        return {"found": True, "pokemon": POKEMON_DATABASE[query]}

    return {
        "found": False,
        "error": f"Pokémon '{name}' not found.",
        "available_pokemons": list(POKEMON_DATABASE.keys()),
    }


async def fortune_teller_tool(question: str) -> Dict[str, Any]:
    """Async Tool: Answers a yes/no fortune telling question using a mystical oracle."""
    # Simulate async I/O
    await asyncio.sleep(0.01)

    choice_idx = abs(hash(question.strip().lower())) % len(FORTUNE_RESPONSES)
    chosen = FORTUNE_RESPONSES[choice_idx]
    lucky_num = (abs(hash(question)) % 99) + 1

    return {
        "question": question,
        "oracle_answer": chosen["answer"],
        "verdict": chosen["verdict"],
        "crystal_ball_aura": chosen["aura"],
        "lucky_number": lucky_num,
    }


async def execute_tool(tool_name: str, tool_inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Executes the corresponding async Python function for a requested tool."""
    if tool_name == "get_pokemon":
        return await get_pokemon_tool(
            name=tool_inputs.get("name", ""),
            type=tool_inputs.get("type"),
        )
    elif tool_name == "fortune_teller":
        return await fortune_teller_tool(
            question=tool_inputs.get("question", ""),
        )
    else:
        return {"error": f"Unknown tool: '{tool_name}'"}


# ==============================================================================
# 2. Tool Declarations (Anthropic API Format)
# ==============================================================================

TOOLS = [
    {
        "name": "get_pokemon",
        "description": (
            "Lookup stats, type, signature moves, and abilities for a Pokémon by name "
            "(e.g., 'pikachu', 'charizard', 'bulbasaur', 'blastoise', 'gengar', 'mewtwo') "
            "or use 'all' to list Pokémon."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the Pokémon to look up, or 'all' to list.",
                },
                "type": {
                    "type": "string",
                    "description": "Optional type filter (e.g. 'electric', 'fire', 'water', 'grass').",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "fortune_teller",
        "description": (
            "Consults a mystical oracle to answer any fortune-telling or yes/no prediction question "
            "(e.g. 'Will I pass my Claude Architect exam?', 'Is today my lucky day?')."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The yes/no fortune or prediction question to ask the oracle.",
                },
            },
            "required": ["question"],
        },
    },
]


# ==============================================================================
# 3. Async Agentic Loop Handling stop_reason
# ==============================================================================

async def run_agent(
    prompt: str,
    client: anthropic.AsyncAnthropic,
    trail: ResponseTrail,
    model: str = "claude-haiku-4-5",
    max_turns: int = 5,
) -> str:
    """
    Standard asynchronous agentic loop following Anthropic docs:
    1. Send user prompt and tools to Claude asynchronously.
    2. Inspect `response.stop_reason`:
       - 'tool_use': Claude requested one or more tool calls.
         a. Append assistant response (with tool_use blocks) to messages.
         b. Concurrently execute all requested tools using `asyncio.gather`.
         c. Append user message containing `tool_result` blocks.
         d. Loop again to let Claude observe results.
       - 'end_turn': Claude has finished answering. Extract final text and return.
       - 'max_tokens': Max output tokens exceeded.

    All events are logged to the response trail for offline replay and audit.

    Args:
        prompt: User prompt/input
        client: AsyncAnthropic client instance
        trail: ResponseTrail logger instance
        model: Claude model to use
        max_turns: Maximum turns in the agentic loop
    """
    session_id = str(uuid.uuid4())
    trail.session_start(session_id, prompt, model)

    print("\n" + "=" * 60)
    print(f"User Prompt: {prompt}")
    print(f"Session ID: {session_id[:8]}...")
    print("=" * 60)

    # Maintain conversation state
    messages: List[Dict[str, Any]] = [
        {"role": "user", "content": prompt}
    ]

    for turn in range(1, max_turns + 1):
        print(f"\n--- Turn {turn} ---")

        # Log outgoing request
        trail.api_request(session_id, turn, messages)

        # 1. Async API Call to Claude (with latency tracking)
        t0 = time.perf_counter()
        response = await client.messages.create(
            model=model,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )
        latency_s = time.perf_counter() - t0

        # Log full response with latency
        trail.api_response(session_id, turn, response, latency_s)

        stop_reason = response.stop_reason
        print(f"Claude Stop Reason: {stop_reason}  (latency: {latency_s:.2f}s)")

        # Print any reasoning / thought text Claude provided
        for block in response.content:
            if block.type == "text":
                print(f"Claude: {block.text}")

        # 2. Handle Stop Reasons
        if stop_reason == "tool_use":
            # (a) Append Claude's assistant message containing the tool_use blocks
            messages.append({"role": "assistant", "content": response.content})

            # Filter tool_use blocks
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

            for block in tool_use_blocks:
                print(f"🔧 Tool Call: {block.name} (ID: {block.id})")
                print(f"📥 Input: {json.dumps(block.input)}")
                # Log tool call to trail
                trail.tool_call(session_id, turn, block.name, block.id, block.input)

            # (b) Concurrently execute all tools requested in this turn
            results = await asyncio.gather(
                *[execute_tool(b.name, b.input) for b in tool_use_blocks]
            )

            # (c) Construct the tool_result content blocks
            tool_results = []
            for block, result in zip(tool_use_blocks, results):
                print(f"📤 Output [{block.name}]: {json.dumps(result, indent=2)}")
                # Log tool result to trail
                trail.tool_result(session_id, turn, block.name, block.id, result)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

            # (d) Send tool results back to Claude in a user message
            messages.append({"role": "user", "content": tool_results})
            print("🔄 Sending tool results back to Claude...")

        elif stop_reason == "end_turn":
            print("\n✨ Claude finished turn (stop_reason == 'end_turn').")
            final_text = "".join(
                b.text for b in response.content if b.type == "text"
            )
            trail.session_end(session_id, final_text, "end_turn")
            return final_text

        elif stop_reason == "max_tokens":
            print("⚠️ Claude stopped because max_tokens was reached.")
            trail.session_end(session_id, "", "max_tokens")
            break

        elif stop_reason == "stop_sequence":
            print("🛑 Custom stop sequence encountered.")
            trail.session_end(session_id, "", "stop_sequence")
            break

        else:
            print(f"❓ Unexpected stop_reason: {stop_reason}")
            trail.session_end(session_id, "", f"unexpected:{stop_reason}")
            break

    # Loop exhausted without end_turn
    trail.session_end(session_id, "", "max_turns_exhausted")
    return ""


# ==============================================================================
# 4. Entry Point
# ==============================================================================

async def main():
    # Retrieve API key (set in your environment or in a .env file)
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Please set your ANTHROPIC_API_KEY in environment or in a .env file.")
        print("Example: set ANTHROPIC_API_KEY=sk-ant-...")
        return

    # Asynchronous Anthropic client
    client = anthropic.AsyncAnthropic(api_key=api_key)

    # Initialize response trail logger
    # Trail path is relative to this script's directory (stop_reason/)
    trail_path = get_agent_trail_path(__file__)
    trail = ResponseTrail(path=trail_path)

    # Example 1: Pokemon Tool Call
    await run_agent(
        prompt="Can you give me Charizard's stats and signature moves?",
        client=client,
        trail=trail,
    )

    # Example 2: Fortune Teller Yes/No Oracle
    await run_agent(
        prompt="Will I pass the Claude Certified Architect Foundation exam tomorrow?",
        client=client,
        trail=trail,
    )

    # Example 3: Multi-intent / Concurrent Tool Calling (Pokemon + Fortune Telling)
    await run_agent(
        prompt="Look up Pikachu's abilities, and tell my fortune on whether I will catch one today.",
        client=client,
        trail=trail,
    )

    # Replay trail offline (no API calls!)
    print("\n" + "🔄 REPLAYING TRAIL (offline, no API calls)...\n")
    replay_trail(trail_path)


if __name__ == "__main__":
    asyncio.run(main())
