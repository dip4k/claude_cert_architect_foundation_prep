"""
Mock Claude Client for Offline Testing & Simulation.

Allows testing agentic loops, tool calling, and stop_reason workflows
without making live Anthropic API calls and consuming tokens.
"""

from typing import Any, Dict, List, Optional
import uuid


class MockContentBlock:
    """Simulates an Anthropic ContentBlock (text or tool_use)."""

    def __init__(
        self,
        block_type: str,
        text: Optional[str] = None,
        name: Optional[str] = None,
        tool_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ):
        self.type = block_type
        self.text = text
        self.name = name
        self.id = tool_id or f"toolu_{uuid.uuid4().hex[:12]}"
        self.input = input_data or {}

    def model_dump(self) -> Dict[str, Any]:
        """Convert block to dictionary representation."""
        data: Dict[str, Any] = {"type": self.type}
        if self.text is not None:
            data["text"] = self.text
        if self.name is not None:
            data["name"] = self.name
        if self.id is not None:
            data["id"] = self.id
        if self.input is not None:
            data["input"] = self.input
        return data


class MockUsage:
    """Simulates Anthropic Token Usage."""

    def __init__(self, input_tokens: int = 150, output_tokens: int = 75):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_creation_input_tokens = 0
        self.cache_read_input_tokens = 0

    def model_dump(self) -> Dict[str, Any]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
        }


class MockMessageResponse:
    """Simulates an Anthropic Message Response."""

    def __init__(
        self,
        content: List[MockContentBlock],
        stop_reason: str = "end_turn",
        model: str = "claude-haiku-4-5",
        response_id: Optional[str] = None,
    ):
        self.id = response_id or f"msg_{uuid.uuid4().hex[:12]}"
        self.type = "message"
        self.role = "assistant"
        self.content = content
        self.model = model
        self.stop_reason = stop_reason
        self.stop_sequence = None
        self.usage = MockUsage()

    def model_dump(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "role": self.role,
            "content": [b.model_dump() for b in self.content],
            "model": self.model,
            "stop_reason": self.stop_reason,
            "stop_sequence": self.stop_sequence,
            "usage": self.usage.model_dump(),
        }


class MockMessagesEndpoint:
    """Simulates client.messages with programmable or queued responses."""

    def __init__(self, responses: Optional[List[MockMessageResponse]] = None):
        self.responses: List[MockMessageResponse] = list(responses or [])
        self.call_history: List[Dict[str, Any]] = []

    def queue_response(self, response: MockMessageResponse) -> None:
        self.responses.append(response)

    def create(self, **kwargs: Any) -> MockMessageResponse:
        """Synchronous create simulation."""
        self.call_history.append(kwargs)
        if self.responses:
            return self.responses.pop(0)

        # Default fallback response
        return MockMessageResponse(
            content=[MockContentBlock(block_type="text", text="Mock direct answer")],
            stop_reason="end_turn",
        )

    async def acreate(self, **kwargs: Any) -> MockMessageResponse:
        """Asynchronous create simulation."""
        return self.create(**kwargs)


class MockClaudeClient:
    """Mock Anthropic Client supporting both sync and async testing."""

    def __init__(self, responses: Optional[List[MockMessageResponse]] = None):
        self.messages = MockMessagesEndpoint(responses)


class AsyncMockMessagesEndpoint(MockMessagesEndpoint):
    async def create(self, **kwargs: Any) -> MockMessageResponse:
        return super().create(**kwargs)


class AsyncMockClaudeClient:
    """Mock AsyncAnthropic Client."""

    def __init__(self, responses: Optional[List[MockMessageResponse]] = None):
        self.messages = AsyncMockMessagesEndpoint(responses)
