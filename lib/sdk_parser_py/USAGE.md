# SDK Parser Python - Quick Reference

## Installation & Setup

### 1. Import the Parser

```python
from lib.sdk_parser_py import create_parser
```

### 2. Create a Parser Instance

```python
parser = create_parser()
```

### 3. Parse a Response

```python
result = parser.parse(api_response)

if result.get("success"):
    # Use result data
    data = result.get("data")
    print(data.text)
else:
    # Handle error
    error = result.get("error")
    print(error.message)
```

## Common Patterns

### Extract Text Only

```python
result = parser.get_text(response)
if result.get("success"):
    text = result.get("data")  # str or None
```

### Extract Tool Uses Only

```python
result = parser.get_tool_uses(response)
if result.get("success"):
    tools = result.get("data")
    for tool in tools:
        print(tool.name, tool.input)
```

### Get Token Usage

```python
result = parser.get_usage(response)
if result.get("success"):
    usage = result.get("data")
    print(f"Used {usage.input_tokens} input tokens")
```

### Check if Response Uses Tools

```python
result = parser.uses_tools(response)
if result.get("success") and result.get("data"):
    print("This response triggered tool use")
```

### Get Response Metadata

```python
result = parser.get_metadata(response)
if result.get("success"):
    meta = result.get("data")
    print(meta["id"], meta["model"], meta["stop_reason"])
```

## Advanced Patterns

### Custom Transformation

```python
def formatter(parsed):
    return {
        "message": parsed.text,
        "tools_used": [t.name for t in parsed.tool_uses],
        "tokens_used": parsed.usage.input_tokens + parsed.usage.output_tokens,
    }

result = parser.transform(response, formatter)
if result.get("success"):
    data = result.get("data")
```

### Batch Processing

```python
result = parser.parse_many([response1, response2, response3])
if result.get("success"):
    parsed_list = result.get("data")
    for parsed in parsed_list:
        # Process each response
```

### Exception-Based Error Handling

```python
from lib.sdk_parser_py import ParserOptions

options = ParserOptions(throw_on_error=True)
parser = create_parser(options)

try:
    result = parser.parse(response)
    data = result.get("data")
except Exception as error:
    # Handle error
```

### Disable Raw Response in Parsed Output

```python
from lib.sdk_parser_py import ParserOptions

options = ParserOptions(include_raw=False)
parser = create_parser(options)
# Raw response won't be included in parsed.raw
```

### Disable Tool Use Parsing

```python
from lib.sdk_parser_py import ParserOptions

options = ParserOptions(parse_tool_uses=False)
parser = create_parser(options)
# parsed.tool_uses will always be empty
```

## Utility Functions

### Format Token Usage

```python
from lib.sdk_parser_py import format_token_usage

formatted = format_token_usage(response_usage)
# Output: "Input: 100, Output: 50, Cache Read: 25"
```

### Calculate Total Tokens

```python
from lib.sdk_parser_py import calculate_total_tokens

total = calculate_total_tokens(response_usage)
# Includes cache read tokens if present
```

### Format Stop Reason

```python
from lib.sdk_parser_py import format_stop_reason

readable = format_stop_reason("end_turn")
# Output: "Response completed naturally"
```

### Check for Content Types

```python
from lib.sdk_parser_py import has_text, has_tool_use

if has_text(response_content):
    # Response contains text

if has_tool_use(response_content):
    # Response contains tool calls
```

### Count Blocks by Type

```python
from lib.sdk_parser_py import count_blocks_by_type

counts = count_blocks_by_type(response_content)
# {"text": 1, "tool_use": 2}
```

### Filter Blocks by Type

```python
from lib.sdk_parser_py import filter_blocks_by_type

text_only = filter_blocks_by_type(response_content, "text")
tools_only = filter_blocks_by_type(response_content, "tool_use")
```

## Type-Safe Responses

### ParsedResponse Structure

```python
# After parsing, you get a ParsedResponse object with:
parsed.id              # str - Message/Response ID
parsed.model           # str - Model used
parsed.stop_reason     # str - Why response stopped
parsed.text            # str or None - Text content
parsed.tool_uses       # List[ToolUseBlock] - Tool calls
parsed.all_blocks      # List[ContentBlock] - All content blocks
parsed.usage           # UsageInfo - Token usage
parsed.raw             # Dict or None - Original response
```

### Error Structure

```python
error.code             # str - Error code (e.g., "INVALID_RESPONSE")
error.message          # str - Human-readable message
error.details          # Any - Additional context
```

## Extending the Parser

### Create a Custom Parser

```python
from lib.sdk_parser_py import SDKResponseParser

class MyCustomParser(SDKResponseParser):
    def parse_and_log(self, response):
        print("Parsing response...")
        result = self.parse(response)
        
        if result.get("success"):
            print(f"✓ Parsed: {result.get('data').id}")
        else:
            print(f"✗ Failed: {result.get('error').message}")
        
        return result

parser = MyCustomParser()
parser.parse_and_log(response)
```

## Performance Tips

1. **Reuse Parser Instances**: Create once, use many times
2. **Disable Unused Features**: Set `parse_tool_uses=False` if not needed
3. **Disable Raw Response**: Set `include_raw=False` to save memory
4. **Use Specific Methods**: Use `get_text()` or `get_tool_uses()` when you only need one thing

## Error Codes

- `INVALID_RESPONSE` - Response doesn't match expected structure
- `PARSE_ERROR` - General parsing error
- `UNKNOWN_ERROR` - Unexpected error occurred
- `BATCH_PARSE_ERROR` - Error during batch parsing
- `TRANSFORM_ERROR` - Custom formatter threw an error

## Examples

See `examples.py` for detailed examples of:
- Basic response parsing
- Tool use parsing
- Batch processing
- Error handling
- Custom transformations
- Token analysis
- Response logging and validation

## Best Practices

1. ✅ Always check `result.get("success")` before accessing data
2. ✅ Handle null text gracefully (responses can be tool-only)
3. ✅ Validate responses before parsing if dealing with untrusted input
4. ✅ Use type hints for better IDE support
5. ✅ Leverage custom transformations for domain-specific processing
6. ✅ Log parser errors for debugging

## Common Gotchas

❌ **Don't assume text is always present**
- Some responses only contain tool calls
- Always check if `text` is None

❌ **Don't miss cache tokens**
- Cache tokens affect cost calculations
- Use `calculate_total_tokens()` which includes cache read tokens

❌ **Don't recreate parser for each response**
- Reuse parser instances for performance
- Parser is stateless and thread-safe

❌ **Don't ignore stop_reason**
- Different stop reasons mean different things
- `tool_use` = tool called, `max_tokens` = truncated response

## Running Examples

```bash
# Run all examples
python -m lib.sdk_parser_py.examples

# Or import specific examples
python
>>> from lib.sdk_parser_py.examples import basic_parsing
>>> basic_parsing()
```

## See Also

- `README.md` - Full API documentation
- `types.py` - Type definitions
- `examples.py` - Working code examples
- `utils.py` - Utility functions reference
