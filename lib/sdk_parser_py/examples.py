"""
Usage Examples for SDK Response Parser (Python)
Reference implementations for common scenarios
"""

import os
import sys
from pathlib import Path

try:
    from .parser import create_parser, SDKResponseParser, ParserOptions
    from .utils import calculate_total_tokens, format_token_usage
except (ImportError, ValueError):
    REPO_ROOT = Path(__file__).resolve().parent.parent.parent
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from lib.sdk_parser_py.parser import create_parser, SDKResponseParser, ParserOptions
    from lib.sdk_parser_py.utils import calculate_total_tokens, format_token_usage


def basic_parsing():
    """Example 1: Basic response parsing"""
    parser = create_parser()

    # Simulated API response
    api_response = {
        "id": "msg_123",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "Hello! How can I help you today?",
            },
        ],
        "model": "claude-3-5-sonnet-20241022",
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": 10,
            "output_tokens": 15,
        },
    }

    result = parser.parse(api_response)

    if result.get("success"):
        data = result.get("data")
        print("Message ID:", data.id)
        print("Response text:", data.text)
        print("Stop reason:", data.stop_reason)


def tool_use_parsing():
    """Example 2: Tool use parsing"""
    parser = create_parser()

    tool_response = {
        "id": "msg_456",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "I'll help you with that. Let me call the appropriate tool.",
            },
            {
                "type": "tool_use",
                "id": "tool_call_1",
                "name": "get_weather",
                "input": {
                    "location": "San Francisco",
                    "unit": "celsius",
                },
            },
        ],
        "model": "claude-3-5-sonnet-20241022",
        "stop_reason": "tool_use",
        "usage": {
            "input_tokens": 50,
            "output_tokens": 100,
        },
    }

    result = parser.parse(tool_response)

    if result.get("success"):
        data = result.get("data")
        print("Text response:", data.text)

        for tool in data.tool_uses:
            print(f"Tool: {tool.name}")
            print("Input:", tool.input)


def batch_processing():
    """Example 3: Batch processing multiple responses"""
    parser = create_parser()

    responses = [
        {
            "id": "msg_001",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "First response"}],
            "model": "claude-3-5-sonnet-20241022",
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 10, "output_tokens": 20},
        },
        {
            "id": "msg_002",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Second response"}],
            "model": "claude-3-5-sonnet-20241022",
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 15, "output_tokens": 25},
        },
    ]

    result = parser.parse_many(responses)

    if result.get("success"):
        for idx, parsed in enumerate(result.get("data"), 1):
            print(f"Response {idx}: {parsed.text}")
            print(f"Total tokens: {calculate_total_tokens(parsed.usage)}")


def error_handling():
    """Example 4: Error handling"""
    parser = create_parser(ParserOptions(throw_on_error=False))

    invalid_response = {
        # Missing required fields
        "id": "msg_789",
    }

    result = parser.parse(invalid_response)

    if not result.get("success"):
        error = result.get("error")
        print("Parse error:")
        print("Code:", error.code)
        print("Message:", error.message)


def custom_transformation():
    """Example 5: Custom transformation"""
    parser = create_parser()

    response = {
        "id": "msg_999",
        "type": "message",
        "role": "assistant",
        "content": [
            {"type": "text", "text": "Hello, world!"},
            {
                "type": "tool_use",
                "id": "tool_1",
                "name": "search",
                "input": {"query": "Claude API"},
            },
        ],
        "model": "claude-3-5-sonnet-20241022",
        "stop_reason": "tool_use",
        "usage": {"input_tokens": 50, "output_tokens": 100},
    }

    def custom_formatter(parsed):
        return {
            "summary": {
                "message_id": parsed.id,
                "model": parsed.model,
                "has_text": parsed.text is not None,
                "tool_count": len(parsed.tool_uses),
            },
            "content": {
                "text": parsed.text or "No text response",
                "tools": [{"name": t.name, "input": t.input} for t in parsed.tool_uses],
            },
            "efficiency": {
                "input_tokens": parsed.usage.input_tokens,
                "output_tokens": parsed.usage.output_tokens,
                "total_tokens": calculate_total_tokens(parsed.usage),
            },
        }

    result = parser.transform(response, custom_formatter)

    if result.get("success"):
        import json
        print(json.dumps(result.get("data"), indent=2))


def check_response_characteristics():
    """Example 6: Checking response characteristics"""
    parser = create_parser()

    response = {
        "id": "msg_abc",
        "type": "message",
        "role": "assistant",
        "content": [
            {"type": "text", "text": "Processing..."},
            {
                "type": "tool_use",
                "id": "tool_x",
                "name": "analyze",
                "input": {"data": "sample"},
            },
        ],
        "model": "claude-3-5-sonnet-20241022",
        "stop_reason": "tool_use",
        "usage": {"input_tokens": 100, "output_tokens": 50},
    }

    has_tools = parser.uses_tools(response)
    metadata = parser.get_metadata(response)

    if has_tools.get("success") and has_tools.get("data"):
        print("This response uses tools")

    if metadata.get("success"):
        m = metadata.get("data")
        print("Response characteristics:")
        print(f"- ID: {m['id']}")
        print(f"- Model: {m['model']}")
        print(f"- Has text: {m['has_text']}")
        print(f"- Has tool use: {m['has_tool_use']}")
        print(f"- Stop reason: {m['stop_reason']}")


def token_analysis():
    """Example 7: Token analysis and reporting"""
    parser = create_parser()

    responses = [
        {
            "id": "msg_1",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Short response"}],
            "model": "claude-3-5-sonnet-20241022",
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 50, "output_tokens": 20},
        },
        {
            "id": "msg_2",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "text", "text": "Much longer response with more details..."}],
            "model": "claude-3-5-sonnet-20241022",
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 50, "output_tokens": 200},
        },
    ]

    parse_result = parser.parse_many(responses)

    if parse_result.get("success"):
        total_input_tokens = 0
        total_output_tokens = 0

        for idx, parsed in enumerate(parse_result.get("data"), 1):
            print(f"\nResponse {idx}:")
            print(format_token_usage(parsed.usage))
            total_input_tokens += parsed.usage.input_tokens
            total_output_tokens += parsed.usage.output_tokens

        print(f"\nBatch Summary:")
        print(f"Total input tokens: {total_input_tokens}")
        print(f"Total output tokens: {total_output_tokens}")
        print(f"Total tokens: {total_input_tokens + total_output_tokens}")


def exception_handling():
    """Example 8: Exception-based error handling"""
    # Parser with throw_on_error enabled
    parser = create_parser(ParserOptions(throw_on_error=True))

    try:
        invalid_response = {"id": "test"}  # Missing required fields
        result = parser.parse(invalid_response)
        print("Parsed successfully:", result)
    except Exception as error:
        print("Failed to parse response:", error)


def cache_token_handling():
    """Example 9: Working with cache tokens"""
    parser = create_parser()

    cached_response = {
        "id": "msg_cache",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "Using cached context..."}],
        "model": "claude-3-5-sonnet-20241022",
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": 50,
            "output_tokens": 100,
            "cache_creation_input_tokens": 1000,
            "cache_read_input_tokens": 500,
        },
    }

    result = parser.parse(cached_response)

    if result.get("success"):
        data = result.get("data")
        print("Token usage with cache:")
        print(format_token_usage(data.usage))
        print(f"Total tokens (including cache): {calculate_total_tokens(data.usage)}")


def build_response_logger():
    """Example 10: Building a response logger"""
    parser = create_parser(ParserOptions(include_raw=True))

    def log_response(response):
        result = parser.parse(response)

        if not result.get("success"):
            error = result.get("error")
            print("Failed to parse response:", error)
            return

        data = result.get("data")
        from datetime import datetime
        timestamp = datetime.now().isoformat()

        print(f"[{timestamp}] Response Log:")
        print(f"  ID: {data.id}")
        print(f"  Model: {data.model}")
        print(f"  Stop Reason: {data.stop_reason}")
        print(f"  Content: {data.text or '(tool use only)'}")
        print(f"  Tools Called: {len(data.tool_uses)}")
        print(f"  Token Usage: {format_token_usage(data.usage)}")

    # Example usage
    sample_response = {
        "id": "msg_log_test",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "Logging test response"}],
        "model": "claude-3-5-sonnet-20241022",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 10, "output_tokens": 30},
    }

    log_response(sample_response)


def build_response_validator():
    """Example 11: Creating a response validator"""
    parser = create_parser()

    def validate_api_response(response):
        result = parser.parse(response)

        if not result.get("success"):
            error = result.get("error")
            return {
                "is_valid": False,
                "errors": [error.message],
            }

        data = result.get("data")
        errors = []

        # Custom validation rules
        if not data.text and len(data.tool_uses) == 0:
            errors.append("Response contains neither text nor tool calls")

        if data.usage.output_tokens > 4000:
            errors.append("Output tokens exceed expected limit")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
        }

    # Example usage
    response = {
        "id": "msg_validate",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "Valid response"}],
        "model": "claude-3-5-sonnet-20241022",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 20, "output_tokens": 40},
    }

    validation = validate_api_response(response)
    print("Validation result:", validation)


if __name__ == "__main__":
    print("=== Example 1: Basic Parsing ===")
    basic_parsing()

    print("\n=== Example 2: Tool Use Parsing ===")
    tool_use_parsing()

    print("\n=== Example 3: Batch Processing ===")
    batch_processing()

    print("\n=== Example 4: Error Handling ===")
    error_handling()

    print("\n=== Example 5: Custom Transformation ===")
    custom_transformation()

    print("\n=== Example 6: Check Response Characteristics ===")
    check_response_characteristics()

    print("\n=== Example 7: Token Analysis ===")
    token_analysis()

    print("\n=== Example 8: Exception Handling ===")
    exception_handling()

    print("\n=== Example 9: Cache Token Handling ===")
    cache_token_handling()

    print("\n=== Example 10: Response Logger ===")
    build_response_logger()

    print("\n=== Example 11: Response Validator ===")
    build_response_validator()
