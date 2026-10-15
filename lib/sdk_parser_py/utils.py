"""
Utility functions for SDK Response Parser
"""

from typing import Any, Dict, List, Optional
from .types import (
    ContentBlock,
    TextBlock,
    ToolUseBlock,
    UsageInfo,
)


def extract_text(blocks: List[ContentBlock]) -> Optional[str]:
    """
    Extract text content from content blocks

    Args:
        blocks: List of content blocks

    Returns:
        Combined text from all text blocks, or None if no text blocks
    """
    text_blocks = [b for b in blocks if b.type == "text" and isinstance(b, TextBlock)]
    if not text_blocks:
        return None
    return "\n".join(b.text for b in text_blocks)


def extract_tool_uses(blocks: List[ContentBlock]) -> List[ToolUseBlock]:
    """
    Extract tool use blocks from content

    Args:
        blocks: List of content blocks

    Returns:
        List of tool use blocks
    """
    return [b for b in blocks if b.type == "tool_use" and isinstance(b, ToolUseBlock)]


def validate_response(response: Any) -> bool:
    """
    Validate required fields in response

    Args:
        response: Response to validate

    Returns:
        True if response is valid, False otherwise
    """
    if not isinstance(response, dict):
        return False

    required_fields = ["id", "content", "model", "stop_reason", "usage"]
    return all(field in response for field in required_fields)


def format_token_usage(usage: UsageInfo) -> str:
    """
    Format token usage information as human-readable string

    Args:
        usage: Usage info object

    Returns:
        Formatted usage string
    """
    result = f"Input: {usage.input_tokens}, Output: {usage.output_tokens}"

    if usage.cache_creation_input_tokens:
        result += f", Cache Creation: {usage.cache_creation_input_tokens}"

    if usage.cache_read_input_tokens:
        result += f", Cache Read: {usage.cache_read_input_tokens}"

    return result


def calculate_total_tokens(usage: UsageInfo) -> int:
    """
    Calculate total tokens used

    Args:
        usage: Usage info object

    Returns:
        Total tokens (includes cache read tokens)
    """
    return (
        usage.input_tokens
        + usage.output_tokens
        + (usage.cache_read_input_tokens or 0)
    )


def has_tool_use(blocks: List[ContentBlock]) -> bool:
    """
    Check if response has tool use content

    Args:
        blocks: List of content blocks

    Returns:
        True if any tool use blocks exist
    """
    return any(b.type == "tool_use" for b in blocks)


def has_text(blocks: List[ContentBlock]) -> bool:
    """
    Check if response has text content

    Args:
        blocks: List of content blocks

    Returns:
        True if any text blocks exist
    """
    return any(b.type == "text" for b in blocks)


def format_stop_reason(stop_reason: str) -> str:
    """
    Get stop reason as human-readable string

    Args:
        stop_reason: Raw stop reason string

    Returns:
        Formatted stop reason
    """
    reason_map = {
        "end_turn": "Response completed naturally",
        "max_tokens": "Maximum token limit reached",
        "stop_sequence": "Stop sequence encountered",
        "tool_use": "Tool use initiated",
    }
    return reason_map.get(stop_reason, stop_reason)


def extract_content_blocks(content: List[Dict[str, Any]]) -> List[ContentBlock]:
    """
    Convert raw content dictionaries to ContentBlock objects

    Args:
        content: List of raw content dictionaries

    Returns:
        List of ContentBlock objects
    """
    blocks = []
    for block_data in content:
        block_type = block_data.get("type", "text")

        if block_type == "tool_use":
            blocks.append(ToolUseBlock.from_dict(block_data))
        elif block_type == "text":
            blocks.append(TextBlock.from_dict(block_data))
        else:
            blocks.append(ContentBlock.from_dict(block_data))

    return blocks


def merge_text_blocks(blocks: List[ContentBlock], separator: str = "\n") -> str:
    """
    Merge all text blocks into a single string

    Args:
        blocks: List of content blocks
        separator: Separator to use between text blocks

    Returns:
        Merged text string
    """
    text_blocks = [b.text for b in blocks if b.type == "text" and isinstance(b, TextBlock) and b.text]
    return separator.join(text_blocks)


def count_blocks_by_type(blocks: List[ContentBlock]) -> Dict[str, int]:
    """
    Count blocks by type

    Args:
        blocks: List of content blocks

    Returns:
        Dictionary with counts per block type
    """
    counts: Dict[str, int] = {}
    for block in blocks:
        counts[block.type] = counts.get(block.type, 0) + 1
    return counts


def filter_blocks_by_type(blocks: List[ContentBlock], block_type: str) -> List[ContentBlock]:
    """
    Filter blocks by type

    Args:
        blocks: List of content blocks
        block_type: Type to filter by

    Returns:
        Filtered list of blocks
    """
    return [b for b in blocks if b.type == block_type]
