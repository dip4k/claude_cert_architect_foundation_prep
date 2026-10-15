# SDK Response Parser - TypeScript vs Python

Comprehensive guide showing how to use the SDK Parser in both TypeScript and Python. Both implementations provide identical functionality with language-appropriate conventions.

## Overview

| Aspect | TypeScript | Python |
|--------|-----------|--------|
| Location | `lib/sdk-parser/` | `lib/sdk_parser_py/` |
| Entry Point | `index.ts` | `__init__.py` |
| Core Class | `SDKResponseParser` | `SDKResponseParser` |
| Type System | TypeScript interfaces | Python dataclasses + type hints |
| Error Handling | Result pattern (default) | Result pattern (default) |
| Dependencies | None | None (stdlib only) |
| Lines of Code | ~1506 | ~2112 |
| Python Version | N/A | 3.8+ |

## Quick Start Comparison

### TypeScript

```typescript
import { createParser } from "./lib/sdk-parser";

const parser = createParser();
const result = parser.parse(apiResponse);

if (result.success) {
  console.log(result.data.text);
  console.log(result.data.toolUses);
} else {
  console.error(result.error.message);
}
```

### Python

```python
from lib.sdk_parser_py import create_parser

parser = create_parser()
result = parser.parse(api_response)

if result.get("success"):
    data = result.get("data")
    print(data.text)
    print(data.tool_uses)
else:
    error = result.get("error")
    print(error.message)
```

## API Comparison

### Creating Parser Instances

#### TypeScript
```typescript
import { createParser, SDKResponseParser } from "./lib/sdk-parser";

// Using factory function
const parser1 = createParser();

// Using class constructor
const parser2 = new SDKResponseParser();

// With options
const parser3 = createParser({
  includeRaw: false,
  throwOnError: true,
  parseToolUses: true,
});
```

#### Python
```python
from lib.sdk_parser_py import create_parser, SDKResponseParser, ParserOptions

# Using factory function
parser1 = create_parser()

# Using class constructor
parser2 = SDKResponseParser()

# With options
options = ParserOptions(
    include_raw=False,
    throw_on_error=True,
    parse_tool_uses=True,
)
parser3 = create_parser(options)
```

### Parsing Responses

#### TypeScript
```typescript
const result = parser.parse(response);

if (result.success) {
  const { id, model, text, toolUses, usage } = result.data;
  console.log(`${model}: ${text}`);
} else {
  console.error(`Error: ${result.error.code} - ${result.error.message}`);
}
```

#### Python
```python
result = parser.parse(response)

if result.get("success"):
    data = result.get("data")
    print(f"{data.model}: {data.text}")
else:
    error = result.get("error")
    print(f"Error: {error.code} - {error.message}")
```

### Extracting Data

#### TypeScript - Get Text Only
```typescript
const result = parser.getText(response);
if (result.success) {
  const text = result.data;
}
```

#### Python - Get Text Only
```python
result = parser.get_text(response)
if result.get("success"):
    text = result.get("data")
```

#### TypeScript - Get Tool Uses
```typescript
const result = parser.getToolUses(response);
if (result.success) {
  result.data.forEach((tool) => {
    console.log(tool.name, tool.input);
  });
}
```

#### Python - Get Tool Uses
```python
result = parser.get_tool_uses(response)
if result.get("success"):
    for tool in result.get("data"):
        print(tool.name, tool.input)
```

### Batch Processing

#### TypeScript
```typescript
const result = parser.parseMany([response1, response2, response3]);
if (result.success) {
  result.data.forEach((parsed) => {
    console.log(parsed.text);
  });
}
```

#### Python
```python
result = parser.parse_many([response1, response2, response3])
if result.get("success"):
    for parsed in result.get("data"):
        print(parsed.text)
```

### Custom Transformations

#### TypeScript
```typescript
const result = parser.transform(response, (parsed) => ({
  message: parsed.text,
  toolCount: parsed.toolUses.length,
  tokensUsed: parsed.usage.input_tokens + parsed.usage.output_tokens,
}));

if (result.success) {
  console.log(result.data);
}
```

#### Python
```python
def formatter(parsed):
    return {
        "message": parsed.text,
        "tool_count": len(parsed.tool_uses),
        "tokens_used": parsed.usage.input_tokens + parsed.usage.output_tokens,
    }

result = parser.transform(response, formatter)
if result.get("success"):
    print(result.get("data"))
```

### Token Usage

#### TypeScript
```typescript
import { calculateTotalTokens, formatTokenUsage } from "./lib/sdk-parser";

const result = parser.getUsage(response);
if (result.success) {
  console.log(formatTokenUsage(result.data));
  console.log(`Total: ${calculateTotalTokens(result.data)}`);
}
```

#### Python
```python
from lib.sdk_parser_py import calculate_total_tokens, format_token_usage

result = parser.get_usage(response)
if result.get("success"):
    usage = result.get("data")
    print(format_token_usage(usage))
    print(f"Total: {calculate_total_tokens(usage)}")
```

## Error Handling Comparison

### TypeScript - Result Pattern (Default)
```typescript
const result = parser.parse(response);
if (result.success) {
  // result.data is available
} else {
  // result.error is available
  console.error(result.error.code, result.error.message);
}
```

### Python - Result Pattern (Default)
```python
result = parser.parse(response)
if result.get("success"):
    # result["data"] is available
    data = result.get("data")
else:
    # result["error"] is available
    error = result.get("error")
    print(error.code, error.message)
```

### TypeScript - Exception Handling
```typescript
const parser = createParser({ throwOnError: true });
try {
  const parsed = parser.parse(response);
  // Handle parsed.data
} catch (error) {
  // Handle error
}
```

### Python - Exception Handling
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

## Type Definitions Comparison

### TypeScript Types
```typescript
interface ParsedResponse {
  id: string;
  model: string;
  stopReason: string;
  text: string | null;
  toolUses: ToolUseBlock[];
  allBlocks: ContentBlock[];
  usage: UsageInfo;
  raw: SDKResponse;
}

interface UsageInfo {
  input_tokens: number;
  output_tokens: number;
  cache_creation_input_tokens?: number;
  cache_read_input_tokens?: number;
}
```

### Python Types (Dataclasses)
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

@dataclass
class UsageInfo:
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: Optional[int] = None
    cache_read_input_tokens: Optional[int] = None
```

## Method Reference Comparison

| Operation | TypeScript | Python |
|-----------|-----------|--------|
| Parse single | `parse(response)` | `parse(response)` |
| Parse many | `parseMany(responses)` | `parse_many(responses)` |
| Get text | `getText(response)` | `get_text(response)` |
| Get tools | `getToolUses(response)` | `get_tool_uses(response)` |
| Get usage | `getUsage(response)` | `get_usage(response)` |
| Check tools | `usesTools(response)` | `uses_tools(response)` |
| Get metadata | `getMetadata(response)` | `get_metadata(response)` |
| Transform | `transform(response, fn)` | `transform(response, fn)` |
| Set options | `setOptions(opts)` | `set_options(opts)` |
| Get options | `getOptions()` | `get_options()` |

## Utility Functions Comparison

| Function | TypeScript | Python |
|----------|-----------|--------|
| Extract text | `extractText(blocks)` | `extract_text(blocks)` |
| Extract tools | `extractToolUses(blocks)` | `extract_tool_uses(blocks)` |
| Validate | `validateResponse(resp)` | `validate_response(resp)` |
| Format usage | `formatTokenUsage(usage)` | `format_token_usage(usage)` |
| Total tokens | `calculateTotalTokens(usage)` | `calculate_total_tokens(usage)` |
| Has tools | `hasToolUse(blocks)` | `has_tool_use(blocks)` |
| Has text | `hasText(blocks)` | `has_text(blocks)` |
| Format reason | `formatStopReason(reason)` | `format_stop_reason(reason)` |

## Naming Convention Differences

### TypeScript (camelCase)
- `stopReason`
- `toolUses`
- `allBlocks`
- `getText()`
- `getToolUses()`

### Python (snake_case)
- `stop_reason`
- `tool_uses`
- `all_blocks`
- `get_text()`
- `get_tool_uses()`

Both follow language-standard naming conventions.

## Practical Examples

### Building a Response Logger

#### TypeScript
```typescript
import { createParser, formatTokenUsage } from "./lib/sdk-parser";

class ResponseLogger {
  private parser = createParser();

  log(response: unknown): void {
    const result = this.parser.parse(response);
    if (!result.success) {
      console.error(result.error);
      return;
    }

    const { id, model, text, usage } = result.data;
    console.log(`[${new Date().toISOString()}] ${model}`);
    console.log(`  ${text}`);
    console.log(`  ${formatTokenUsage(usage)}`);
  }
}

const logger = new ResponseLogger();
logger.log(response);
```

#### Python
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
        print(f"[{timestamp}] {data.model}")
        print(f"  {data.text}")
        print(f"  {format_token_usage(data.usage)}")

logger = ResponseLogger()
logger.log(response)
```

### Building a Response Validator

#### TypeScript
```typescript
import { createParser } from "./lib/sdk-parser";

class ResponseValidator {
  private parser = createParser();

  validate(response: unknown): {
    isValid: boolean;
    errors: string[];
  } {
    const result = this.parser.parse(response);
    if (!result.success) {
      return {
        isValid: false,
        errors: [result.error.message],
      };
    }

    const errors: string[] = [];

    if (!result.data.text && result.data.toolUses.length === 0) {
      errors.push("No content in response");
    }

    if (result.data.usage.output_tokens > 4000) {
      errors.push("Output exceeds limit");
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }
}

const validator = new ResponseValidator();
const { isValid, errors } = validator.validate(response);
```

#### Python
```python
from lib.sdk_parser_py import create_parser

class ResponseValidator:
    def __init__(self):
        self.parser = create_parser()
    
    def validate(self, response):
        result = self.parser.parse(response)
        if not result.get("success"):
            return {
                "is_valid": False,
                "errors": [result.get("error").message],
            }
        
        data = result.get("data")
        errors = []
        
        if not data.text and not data.tool_uses:
            errors.append("No content in response")
        
        if data.usage.output_tokens > 4000:
            errors.append("Output exceeds limit")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
        }

validator = ResponseValidator()
result = validator.validate(response)
```

## Documentation Structure

Both implementations provide:

- **README.md** - Complete API reference
  - Feature overview
  - Installation instructions
  - API documentation for all methods
  - Type definitions
  - Examples and use cases

- **USAGE.md** - Quick reference guide
  - Quick start
  - Common patterns
  - Utility functions
  - Error codes
  - Best practices
  - Common gotchas

- **examples.py/examples.ts** - Working examples
  - 11 practical examples
  - Runnable code
  - Various use cases

- **types.py/types.ts** - Type definitions
  - Dataclasses (Python) / Interfaces (TypeScript)
  - Comprehensive typing

- **utils.py/utils.ts** - Utility functions
  - Helper functions
  - Text/tool extraction
  - Token calculations
  - Response validation

- **parser.py/parser.ts** - Core parser
  - SDKResponseParser class
  - Parse methods
  - Result handling
  - Error management

## File Structure Comparison

### TypeScript
```
lib/sdk-parser/
├── types.ts        (69 lines)
├── parser.ts       (245 lines)
├── utils.ts        (98 lines)
├── index.ts        (11 lines)
├── examples.ts     (418 lines)
├── README.md       (383 lines)
└── USAGE.md        (282 lines)
Total: ~1,506 lines
```

### Python
```
lib/sdk_parser_py/
├── types.py        (213 lines)
├── parser.py       (309 lines)
├── utils.py        (209 lines)
├── __init__.py     (69 lines)
├── examples.py     (419 lines)
├── README.md       (577 lines)
└── USAGE.md        (316 lines)
Total: ~2,112 lines
```

## Choosing Between TypeScript and Python

### Use TypeScript When:
- Building Node.js/frontend applications
- Working with strict typing requirements
- Need to use the parser in a web environment
- Using an existing TypeScript codebase

### Use Python When:
- Building backend services
- Working with AI/ML frameworks
- Need to integrate with Python libraries
- Using an existing Python codebase

### Both implementations:
- Provide identical functionality
- Follow language-standard conventions
- Include comprehensive documentation
- Have no external dependencies
- Support the same error handling patterns

## Migration Guide

If you need to switch between languages:

1. **Logic remains identical** - Core parsing logic is the same
2. **Method names change** - Follow language conventions (`getText` → `get_text`)
3. **Error handling style** - Result pattern works the same way
4. **Type access differs** - TypeScript uses direct access, Python uses `.get()`
5. **Constructor patterns** - Both support `createParser()` factory function

## Performance Characteristics

Both implementations:
- Parse responses in O(n) time
- Memory efficient
- Stateless and reusable
- Thread-safe
- No external dependencies

## Dependencies

| Implementation | Runtime Deps | Dev Deps |
|---------------|-------------|----------|
| TypeScript | None | TypeScript compiler |
| Python | None | Python 3.8+ |

Both are zero-dependency libraries.

## Summary

The SDK Response Parser is available in both TypeScript and Python with:
- ✅ Identical functionality
- ✅ Language-appropriate conventions
- ✅ Comprehensive documentation
- ✅ Working examples
- ✅ Zero external dependencies
- ✅ Production-ready quality

Choose whichever fits your practice project better!
