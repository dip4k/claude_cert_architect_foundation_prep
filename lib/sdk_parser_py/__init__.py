"""
SDK Response Parser - Python Implementation
A generic, reusable parser for Claude API and similar SDK responses.
"""

# Import main components
from .parser import SDKResponseParser, create_parser, parse
from .types import (
    ContentBlock,
    ParserError,
    ParserOptions,
    ParsedResponse,
    TextBlock,
    ToolUseBlock,
    UsageInfo,
    error_result,
    is_error,
    is_success,
    success_result,
)
from .utils import (
    calculate_total_tokens,
    count_blocks_by_type,
    extract_content_blocks,
    extract_text,
    extract_tool_uses,
    filter_blocks_by_type,
    format_stop_reason,
    format_token_usage,
    has_text,
    has_tool_use,
    merge_text_blocks,
    validate_response,
)

__version__ = "1.0.0"
__author__ = "Claude Certified Architect Foundation"

__all__ = [
    # Parser
    "SDKResponseParser",
    "create_parser",
    "parse",
    # Types
    "ContentBlock",
    "ParsedResponse",
    "ParserError",
    "ParserOptions",
    "TextBlock",
    "ToolUseBlock",
    "UsageInfo",
    "error_result",
    "is_error",
    "is_success",
    "success_result",
    # Utils
    "calculate_total_tokens",
    "count_blocks_by_type",
    "extract_content_blocks",
    "extract_text",
    "extract_tool_uses",
    "filter_blocks_by_type",
    "format_stop_reason",
    "format_token_usage",
    "has_text",
    "has_tool_use",
    "merge_text_blocks",
    "validate_response",
]
