"""
Shared helpers for the Domain 1 agent loops (TS 1.1 - 1.7).

Loop control uses response.stop_reason only. Every stop_reason is handled explicitly:
tool_use and pause_turn continue the loop; end_turn finishes it; max_tokens, stop_sequence,
refusal and any unknown value raise LoopStopped so the caller cannot mistake them for success.
"""

from typing import Any, Optional

COORDINATOR_MODEL = "claude-sonnet-4-5"  # orchestration and reasoning
WORKER_MODEL = "claude-haiku-4-5"  # bounded, fast leaf tasks

KNOWN_STOP_REASONS = ("tool_use", "end_turn", "max_tokens", "stop_sequence", "pause_turn", "refusal")


class LoopStopped(RuntimeError):
    """The loop ended on a stop_reason other than end_turn."""

    def __init__(self, stop_reason: Optional[str], partial_text: str = "") -> None:
        self.stop_reason = stop_reason
        self.partial_text = partial_text
        label = stop_reason if stop_reason in KNOWN_STOP_REASONS else f"unexpected:{stop_reason}"
        super().__init__(f"Agent loop stopped on stop_reason={label}")


def read_stop_reason(parser: Any, response: Any) -> Optional[str]:
    """Return the response stop_reason via the parser, with no silent default."""
    result = parser.parse(response.model_dump())
    if result.get("success"):
        return result["data"].stop_reason
    return getattr(response, "stop_reason", None)


def response_text(response: Any) -> str:
    """Join the text blocks of a response (thinking and tool_use blocks are skipped)."""
    return "".join(
        b.text for b in response.content if getattr(b, "type", "") == "text" and b.text
    )


def stop_status(stop_reason: Optional[str]) -> str:
    """Trail status label for a stop_reason that ends the loop."""
    if stop_reason in KNOWN_STOP_REASONS:
        return str(stop_reason)
    return f"unexpected_stop_reason:{stop_reason}"
