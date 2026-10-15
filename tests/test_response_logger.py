"""
Tests for Response Logger: serialization, trail parsing, block repair, and message reconstruction.
Runs completely offline with zero API calls.
Compatible with both unittest and pytest.
"""

import os
import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lib.response_logger import (
    ResponseTrail,
    parse_block_repr,
    parse_trail,
    query_trail,
    reconstruct_session_messages,
    repair_trail_file,
)
from lib.response_logger.logger import _serialize_content, _serialize_message


class MockToolUseBlock:
    """Simulates an Anthropic SDK ToolUseBlock object with model_dump()."""

    def __init__(self, id: str, name: str, input_data: Dict[str, Any]):
        self.id = id
        self.name = name
        self.input = input_data
        self.type = "tool_use"

    def model_dump(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "id": self.id,
            "name": self.name,
            "input": self.input,
        }

    def __repr__(self) -> str:
        return (
            f"ToolUseBlock(id='{self.id}', "
            f"caller=DirectCaller(type='direct'), "
            f"input={self.input}, "
            f"name='{self.name}', "
            f"type='{self.type}', "
            f"toolset_name=None)"
        )


class MockTextBlock:
    """Simulates an Anthropic SDK TextBlock object with model_dump()."""

    def __init__(self, text: str):
        self.text = text
        self.type = "text"

    def model_dump(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "text": self.text,
        }

    def __repr__(self) -> str:
        return f"TextBlock(citations=None, text='{self.text}', type='text')"


class TestResponseLogger(unittest.TestCase):
    """Test suite for trail logging serialization, repair, parsing, and recovery."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_serialize_content_primitives(self):
        """Verify that primitives pass through untouched."""
        self.assertEqual(_serialize_content("hello"), "hello")
        self.assertEqual(_serialize_content(42), 42)
        self.assertEqual(_serialize_content(3.14), 3.14)
        self.assertIs(_serialize_content(True), True)
        self.assertIsNone(_serialize_content(None))

    def test_serialize_content_sdk_blocks(self):
        """Verify that SDK blocks with model_dump() are converted to dicts."""
        block = MockToolUseBlock("toolu_123", "get_pokemon", {"name": "charizard"})
        serialized = _serialize_content([block])

        self.assertIsInstance(serialized, list)
        self.assertEqual(len(serialized), 1)
        self.assertIsInstance(serialized[0], dict)
        self.assertEqual(
            serialized[0],
            {
                "type": "tool_use",
                "id": "toolu_123",
                "name": "get_pokemon",
                "input": {"name": "charizard"},
            },
        )

    def test_api_request_logs_proper_json(self):
        """Verify api_request logs JSON dicts instead of stringified repr."""
        trail_file = os.path.join(self.test_dir, "test_trail.jsonl")
        trail = ResponseTrail(trail_file)

        session_id = "sess-001"
        messages = [
            {"role": "user", "content": "Tell me about Charizard"},
            {
                "role": "assistant",
                "content": [MockToolUseBlock("toolu_123", "get_pokemon", {"name": "charizard"})],
            },
            {
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": "toolu_123", "content": "{}"}],
            },
        ]

        trail.api_request(session_id, turn=2, messages=messages)

        with open(trail_file, "r", encoding="utf-8") as f:
            line = f.readline()
            record = json.loads(line)

        self.assertEqual(record["event"], "api_request")
        msgs = record["payload"]["messages"]
        self.assertEqual(len(msgs), 3)

        # Check that assistant message content is a list containing a DICT, not a repr string!
        assistant_msg = msgs[1]
        self.assertEqual(assistant_msg["role"], "assistant")
        self.assertIsInstance(assistant_msg["content"], list)
        self.assertIsInstance(assistant_msg["content"][0], dict)
        self.assertEqual(assistant_msg["content"][0]["name"], "get_pokemon")
        self.assertEqual(assistant_msg["content"][0]["input"], {"name": "charizard"})
        self.assertEqual(assistant_msg["content"][0]["id"], "toolu_123")
        self.assertEqual(assistant_msg["content"][0]["type"], "tool_use")

    def test_parse_block_repr_tool_use(self):
        """Test parsing a stringified ToolUseBlock repr."""
        repr_str = (
            "ToolUseBlock(id='toolu_01RsJ7LRShG4nRaALkWf8RPn', "
            "caller=DirectCaller(type='direct'), "
            "input={'name': 'charizard'}, "
            "name='get_pokemon', "
            "type='tool_use', "
            "toolset_name=None)"
        )

        parsed = parse_block_repr(repr_str)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["type"], "tool_use")
        self.assertEqual(parsed["id"], "toolu_01RsJ7LRShG4nRaALkWf8RPn")
        self.assertEqual(parsed["name"], "get_pokemon")
        self.assertEqual(parsed["input"], {"name": "charizard"})

    def test_parse_block_repr_fortune_teller(self):
        """Test parsing a tool use block with question string containing spaces."""
        repr_str = (
            "ToolUseBlock(id='toolu_012mUGnhmEJxxLPgqnwyH8M8', "
            "caller=DirectCaller(type='direct'), "
            "input={'question': 'Will I pass the Claude Certified Architect Foundation exam tomorrow?'}, "
            "name='fortune_teller', "
            "type='tool_use', "
            "toolset_name=None)"
        )

        parsed = parse_block_repr(repr_str)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["type"], "tool_use")
        self.assertEqual(parsed["name"], "fortune_teller")
        self.assertEqual(parsed["id"], "toolu_012mUGnhmEJxxLPgqnwyH8M8")
        self.assertEqual(
            parsed["input"],
            {"question": "Will I pass the Claude Certified Architect Foundation exam tomorrow?"},
        )

    def test_parse_trail_with_auto_repair(self):
        """Test parsing a trail that has legacy stringified blocks."""
        trail_file = os.path.join(self.test_dir, "legacy_trail.jsonl")
        legacy_record = {
            "ts": "2026-09-14T12:00:00+00:00",
            "session_id": "legacy-session",
            "event": "api_request",
            "payload": {
                "turn": 2,
                "messages": [
                    {"role": "user", "content": "Hi"},
                    {
                        "role": "assistant",
                        "content": [
                            "ToolUseBlock(id='toolu_999', caller=DirectCaller(type='direct'), "
                            "input={'name': 'pikachu'}, name='get_pokemon', type='tool_use', toolset_name=None)"
                        ],
                    },
                ],
            },
        }
        with open(trail_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(legacy_record) + "\n")

        # Parse with repair
        records = parse_trail(trail_file, repair_blocks=True)
        self.assertEqual(len(records), 1)
        assistant_content = records[0]["payload"]["messages"][1]["content"]
        self.assertIsInstance(assistant_content[0], dict)
        self.assertEqual(assistant_content[0]["name"], "get_pokemon")
        self.assertEqual(assistant_content[0]["input"], {"name": "pikachu"})

    def test_reconstruct_session_messages(self):
        """Test state reconstruction for crash recovery (Domain 5, TS 5.4)."""
        trail_file = os.path.join(self.test_dir, "recovery_trail.jsonl")
        trail = ResponseTrail(trail_file)
        session_id = "recover-sess"

        trail.session_start(session_id, "Lookup Pikachu", "claude-haiku-4-5")
        trail.api_request(session_id, turn=1, messages=[{"role": "user", "content": "Lookup Pikachu"}])
        trail.api_request(
            session_id,
            turn=2,
            messages=[
                {"role": "user", "content": "Lookup Pikachu"},
                {
                    "role": "assistant",
                    "content": [MockToolUseBlock("toolu_pik", "get_pokemon", {"name": "pikachu"})],
                },
                {
                    "role": "user",
                    "content": [{"type": "tool_result", "tool_use_id": "toolu_pik", "content": "{}"}],
                },
            ],
        )

        # Reconstruct
        messages = reconstruct_session_messages(trail_file, session_id=session_id)
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertEqual(messages[1]["content"][0]["name"], "get_pokemon")
        self.assertEqual(messages[2]["role"], "user")

    def test_repair_trail_file(self):
        """Test in-place file repair."""
        trail_file = os.path.join(self.test_dir, "corrupted_trail.jsonl")
        corrupted_record = {
            "ts": "2026-09-14T12:00:00+00:00",
            "session_id": "corrupted-session",
            "event": "api_request",
            "payload": {
                "turn": 2,
                "messages": [
                    {
                        "role": "assistant",
                        "content": [
                            "ToolUseBlock(id='toolu_corrupt', input={'x': 1}, name='tool_x', type='tool_use')"
                        ],
                    }
                ],
            },
        }
        with open(trail_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(corrupted_record) + "\n")

        repaired_count = repair_trail_file(trail_file)
        self.assertEqual(repaired_count, 1)

        # Read repaired file
        with open(trail_file, "r", encoding="utf-8") as f:
            repaired_rec = json.loads(f.readline())

        content = repaired_rec["payload"]["messages"][0]["content"]
        self.assertIsInstance(content[0], dict)
        self.assertEqual(content[0]["id"], "toolu_corrupt")
        self.assertEqual(content[0]["name"], "tool_x")
        self.assertEqual(content[0]["input"], {"x": 1})


if __name__ == "__main__":
    unittest.main()

