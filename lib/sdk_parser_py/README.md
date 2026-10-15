# SDK Response Parser - Python

A generic, reusable parser for Claude API and similar SDK responses. Python implementation for Claude Certified Architect Foundation practice projects.

## Features

- ✨ **Generic Design**: Works with any SDK response format following the standard structure
- 🛡️ **Type-Safe**: Full type hints support for better IDE experience
- 🎯 **Flexible**: Support for text extraction, tool use parsing, and custom transformations
- 📊 **Utilities**: Helper functions for common operations like token counting and stop reason formatting
- 🔄 **Result Pattern**: Explicit error handling with `success`/`error` pattern (no exceptions by default)
- 🧩 **Modular**: Use individual utilities or the full parser class
- 🐍 **Pythonic**: Follows Python conventions and best practices

## Installation

Copy the `lib/sdk_parser_py` folder into your project:

```bash
# Copy the directory
cp -r lib/sdk_parser_py your_project/lib/
```

Or add to your Python path:

```python
import sys
sys.path.insert(0, '/path/to/sdk_parser_py')
```

## Quick Start

```python
from lib.sdk_parser_py import create_parser

parser = create_parser()
result = parser.parse(sdk_response)

if result.get("success"):
    data = result.get("data")
    print(data.text)
    print(data.tool_uses)
else:
    error = result.get("error")
    print(error.message)
```

## API Reference

### SDKResponseParser Class

Main parser class for processing SDK responses.

#### Constructor Options

```python
from lib.sdk_parser_py import ParserOptions

options = ParserOptions(
    include_raw=True,       # Include raw response (default: True)
    throw_on_error=False,   # Throw exceptions instead of returning errors (default: False)
    parse_tool_uses=True,   # Parse tool use blocks (default: True)
)
```

#### Methods

##### `parse(response: Any) -> Dict[str, Any]`

Parse a single SDK response.

```python
result = parser.parse(response)
if result.get("success"):
    parsed = result.get("data")
    print(parsed.id, parsed.model, parsed.text)
```

##### `parse_many(responses: List[Any]) -> Dict[str, Any]`

Parse multiple responses at once.

```python
result = parser.parse_many([response1, response2, response3])
if result.get("success"):
    parsed_list = result.get("data")
```

##### `get_text(response: Any) -> Dict[str, Any]`

Extract only text content from a response.

```python
result = parser.get_text(response)
if result.get("success"):
    text = result.get("data")
```

##### `get_tool_uses(response: Any) -> Dict[str, Any]`

Extract tool use blocks from a response.

```python
result = parser.get_tool_uses(response)
if result.get("success"):
    tools = result.get("data")
    for tool in tools:
        print(tool.name, tool.input)
```

##### `get_usage(response: Any) -> Dict[str, Any]`

Get token usage information.

```python
result = parser.get_usage(response)
if result.get("success"):
    usage = result.get("data")
    print(f"Input: {usage.input_tokens}, Output: {usage.output_tokens}")
```

##### `uses_tools(response: Any) -> Dict[str, Any]`

Check if response uses tools.

```python
result = parser.uses_tools(response)
if result.get("success") and result.get("data"):
    print("Response uses tools")
```

##### `get_metadata(response: Any) -> Dict[str, Any]`

Get response metadata.

```python
result = parser.get_metadata(response)
if result.get("success"):
    metadata = result.get("data")
    print(metadata["id"], metadata["model"], metadata["stop_reason"])
```

##### `transform(response: Any, formatter: Callable) -> Dict[str, Any]`

Transform a parsed response with a custom formatter.

```python
def my_formatter(parsed):
    return {
        "message": parsed.text,
        "tool_count": len(parsed.tool_uses),
    }

result = parser.transform(response, my_formatter)
if result.get("success"):
    transformed = result.get("data")
```

### Utility Functions

#### `extract_text(blocks: List[ContentBlock]) -> Optional[str]`

Extract text from content blocks.

```python
from lib.sdk_parser_py import extract_text

text = extract_text(response_content)
```

#### `extract_tool_uses(blocks: List[ContentBlock]) -> List[ToolUseBlock]`

Extract tool use blocks.

```python
from lib.sdk_parser_py import extract_tool_uses

tools = extract_tool_uses(response_content)
```

#### `validate_response(response: Any) -> bool`

Validate response structure.

```python
from lib.sdk_parser_py import validate_response

if validate_response(response):
    # Response is valid
```

#### `format_token_usage(usage: UsageInfo) -> str`

Format token usage as a readable string.

```python
from lib.sdk_parser_py import format_token_usage

usage_str = format_token_usage(response.usage)
print(usage_str)  # "Input: 100, Output: 50"
```

#### `calculate_total_tokens(usage: UsageInfo) -> int`

Calculate total tokens used.

```python
from lib.sdk_parser_py import calculate_total_tokens

total = calculate_total_tokens(response.usage)
```

#### `has_tool_use(blocks: List[ContentBlock]) -> bool`

Check if blocks contain tool use.

```python
from lib.sdk_parser_py import has_tool_use

if has_tool_use(response_content):
    # Handle tool use
```

#### `has_text(blocks: List[ContentBlock]) -> bool`

Check if blocks contain text.

```python
from lib.sdk_parser_py import has_text

if has_text(response_content):
    # Handle text response
```

#### `format_stop_reason(stop_reason: str) -> str`

Format stop reason as human-readable string.

```python
from lib.sdk_parser_py import format_stop_reason

readable = format_stop_reason("end_turn")
# "Response completed naturally"
```

#### `count_blocks_by_type(blocks: List[ContentBlock]) -> Dict[str, int]`

Count blocks by type.

```python
from lib.sdk_parser_py import count_blocks_by_type

counts = count_blocks_by_type(response_content)
print(counts)  # {"text": 1, "tool_use": 2}
```

#### `filter_blocks_by_type(blocks: List[ContentBlock], block_type: str) -> List[ContentBlock]`

Filter blocks by type.

```python
from lib.sdk_parser_py import filter_blocks_by_type

text_blocks = filter_blocks_by_type(response_content, "text")
```

### Type Definitions

#### `ParsedResponse`

Main parsed response dataclass.

```python
@dataclass
class ParsedResponse:
    id: str
    model: str
    stop_reason: str
    text: Optional[str]
    tool_uses: List[ToolUseBlock]
    all_blocks: List[ContentBlock]
    usage: UsageInfo
    raw: Optional[Dict[str, Any]]
```

#### `UsageInfo`

Token usage information.

```python
@dataclass
class UsageInfo:
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: Optional[int]
    cache_read_input_tokens: Optional[int]
```

#### `ToolUseBlock`

Tool use block information.

```python
@dataclass
class ToolUseBlock(ContentBlock):
    type: str
    id: str
    name: str
    input: Dict[str, Any]
```

## Examples

### Basic Usage

```python
from lib.sdk_parser_py import create_parser

parser = create_parser()
result = parser.parse(api_response)

if result.get("success"):
    data = result.get("data")
    print("Response ID:", data.id)
    print("Model:", data.model)
    print("Text:", data.text)
    print("Stop Reason:", data.stop_reason)
else:
    error = result.get("error")
    print("Parse failed:", error.message)
```

### Error Handling with Exceptions

```python
from lib.sdk_parser_py import create_parser, ParserOptions

options = ParserOptions(throw_on_error=True)
parser = create_parser(options)

try:
    result = parser.parse(response)
    data = result.get("data")
    # Handle parsed data
except Exception as error:
    # Handle error
    print(f"Parse error: {error}")
```

### Custom Transformation

```python
def custom_formatter(parsed):
    return {
        "summary": parsed.text[:100] if parsed.text else "",
        "tool_count": len(parsed.tool_uses),
        "tokens_used": parsed.usage.input_tokens + parsed.usage.output_tokens,
    }

result = parser.transform(response, custom_formatter)
if result.get("success"):
    data = result.get("data")
    print(data)
```

### Processing Tool Calls

```python
result = parser.get_tool_uses(response)

if result.get("success"):
    tools = result.get("data")
    for tool in tools:
        print(f"Calling tool: {tool.name}")
        print(f"With inputs: {tool.input}")
```

### Batch Processing

```python
responses = [...]  # List of SDK responses

result = parser.parse_many(responses)

if result.get("success"):
    parsed_list = result.get("data")
    for parsed in parsed_list:
        print(f"Response from {parsed.model}: {parsed.text}")
```

### Token Usage Analysis

```python
from lib.sdk_parser_py import calculate_total_tokens, format_token_usage

result = parser.parse(response)
if result.get("success"):
    data = result.get("data")
    print(format_token_usage(data.usage))
    total = calculate_total_tokens(data.usage)
    print(f"Total tokens: {total}")
```

## Development

### Project Structure

```
lib/sdk_parser_py/
├── __init__.py      # Module exports
├── types.py         # Type definitions
├── parser.py        # Main parser class
├── utils.py         # Utility functions
├── examples.py      # Working examples
└── README.md        # This file
```

### Running Examples

```bash
python -m lib.sdk_parser_py.examples
```

Or import and run specific examples:

```python
from lib.sdk_parser_py.examples import basic_parsing, tool_use_parsing

basic_parsing()
tool_use_parsing()
```

### Testing

Create a test file:

```python
# test_parser.py
from lib.sdk_parser_py import create_parser

def test_basic_parsing():
    parser = create_parser()
    response = {
        "id": "test_123",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "Hello"}],
        "model": "claude-3-5-sonnet-20241022",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 10, "output_tokens": 20},
    }
    
    result = parser.parse(response)
    assert result.get("success")
    assert result.get("data").text == "Hello"

if __name__ == "__main__":
    test_basic_parsing()
    print("✓ Test passed")
```

## Best Practices

1. **Reuse Parser Instance**: Create a parser once and reuse it for multiple responses
2. **Check Success Flag**: Always check `result.get("success")` before accessing data
3. **Handle Edge Cases**: Tool responses may have null text; check before using
4. **Type Hints**: Use type hints in your code for better IDE support
5. **Custom Formatters**: Leverage transformations for domain-specific processing
6. **Log Errors**: Log parser errors for debugging

## Extending the Parser

You can subclass the `SDKResponseParser` for domain-specific implementations:

```python
from lib.sdk_parser_py import SDKResponseParser

class CustomParser(SDKResponseParser):
    def parse_and_validate(self, response):
        result = self.parse(response)
        if not result.get("success"):
            return result
        
        # Custom validation logic
        data = result.get("data")
        if len(data.tool_uses) > 5:
            from lib.sdk_parser_py import error_result, ParserError
            return error_result(ParserError(
                code="TOO_MANY_TOOLS",
                message="Response uses too many tools"
            ))
        
        return result

parser = CustomParser()
result = parser.parse_and_validate(response)
```

## Common Patterns

### Response Logger

```python
from datetime import datetime
from lib.sdk_parser_py import create_parser, format_token_usage

class ResponseLogger:
    def __init__(self):
        self.parser = create_parser()
    
    def log(self, response):
        result = self.parser.parse(response)
        if not result.get("success"):
            print(f"Error: {result.get('error')}")
            return
        
        data = result.get("data")
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] {data.model}: {data.text}")
        print(f"  Tokens: {format_token_usage(data.usage)}")

logger = ResponseLogger()
logger.log(response)
```

### Response Validator

```python
from lib.sdk_parser_py import create_parser

class ResponseValidator:
    def __init__(self):
        self.parser = create_parser()
    
    def validate(self, response):
        result = self.parser.parse(response)
        if not result.get("success"):
            return False, [str(result.get("error"))]
        
        data = result.get("data")
        errors = []
        
        if not data.text and not data.tool_uses:
            errors.append("No content in response")
        
        if data.usage.output_tokens > 4000:
            errors.append("Output exceeds limit")
        
        return len(errors) == 0, errors

validator = ResponseValidator()
is_valid, errors = validator.validate(response)
```

## Error Codes

- `INVALID_RESPONSE` - Response doesn't match expected structure
- `PARSE_ERROR` - General parsing error
- `UNKNOWN_ERROR` - Unexpected error occurred
- `BATCH_PARSE_ERROR` - Error during batch parsing
- `TRANSFORM_ERROR` - Custom formatter threw an error

## Performance Considerations

- Parser is stateless and thread-safe
- Reuse parser instances for better performance
- Disable `include_raw` if working with large responses
- Use specific methods (`get_text()`, `get_tool_uses()`) when you only need one thing

## Compatibility

- Python 3.8+
- No external dependencies (uses only standard library)

## License

Part of Claude Certified Architect Foundation practice projects.
