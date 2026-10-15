# SDK Parser Quick Reference

## Installation & Setup

### 1. Import the Parser

```typescript
import { createParser } from "./lib/sdk-parser";
```

### 2. Create a Parser Instance

```typescript
const parser = createParser();
```

### 3. Parse a Response

```typescript
const result = parser.parse(apiResponse);

if (result.success) {
  // Use result.data
  console.log(result.data.text);
} else {
  // Handle error
  console.error(result.error.message);
}
```

## Common Patterns

### Extract Text Only

```typescript
const result = parser.getText(response);
if (result.success) {
  const text = result.data; // string | null
}
```

### Extract Tool Uses Only

```typescript
const result = parser.getToolUses(response);
if (result.success) {
  result.data.forEach((tool) => {
    console.log(tool.name, tool.input);
  });
}
```

### Get Token Usage

```typescript
const result = parser.getUsage(response);
if (result.success) {
  console.log(`Used ${result.data.input_tokens} input tokens`);
}
```

### Check if Response Uses Tools

```typescript
const result = parser.usesTools(response);
if (result.success && result.data) {
  console.log("This response triggered tool use");
}
```

### Get Response Metadata

```typescript
const result = parser.getMetadata(response);
if (result.success) {
  const { id, model, stopReason, hasText, hasToolUse } = result.data;
}
```

## Advanced Patterns

### Custom Transformation

```typescript
const result = parser.transform(response, (parsed) => ({
  message: parsed.text,
  toolsUsed: parsed.toolUses.map(t => t.name),
  tokensUsed: parsed.usage.input_tokens + parsed.usage.output_tokens,
}));
```

### Batch Processing

```typescript
const result = parser.parseMany([response1, response2, response3]);
if (result.success) {
  result.data.forEach((parsed) => {
    // Process each parsed response
  });
}
```

### Exception-Based Error Handling

```typescript
const parser = createParser({ throwOnError: true });
try {
  const parsed = parser.parse(response);
  // Use parsed.data
} catch (error) {
  // Handle error
}
```

### Disable Raw Response in Parsed Output

```typescript
const parser = createParser({ includeRaw: false });
// Raw response won't be included in result.data.raw
```

### Disable Tool Use Parsing

```typescript
const parser = createParser({ parseToolUses: false });
// result.data.toolUses will always be empty
```

## Utility Functions

### Format Token Usage

```typescript
import { formatTokenUsage } from "./lib/sdk-parser";

const formatted = formatTokenUsage(response.usage);
// Output: "Input: 100, Output: 50, Cache Read: 25"
```

### Calculate Total Tokens

```typescript
import { calculateTotalTokens } from "./lib/sdk-parser";

const total = calculateTotalTokens(response.usage);
// Includes cache read tokens if present
```

### Format Stop Reason

```typescript
import { formatStopReason } from "./lib/sdk-parser";

console.log(formatStopReason("end_turn"));
// Output: "Response completed naturally"
```

### Check for Content Types

```typescript
import { hasText, hasToolUse } from "./lib/sdk-parser";

if (hasText(response.content)) {
  // Response contains text
}

if (hasToolUse(response.content)) {
  // Response contains tool calls
}
```

## Type-Safe Responses

### ParsedResponse Structure

```typescript
interface ParsedResponse {
  id: string;                    // Message/Response ID
  model: string;                 // Model used
  stopReason: string;            // Why response stopped
  text: string | null;           // Text content, or null if none
  toolUses: ToolUseBlock[];       // Array of tool calls
  allBlocks: ContentBlock[];      // All content blocks
  usage: UsageInfo;              // Token usage info
  raw: SDKResponse;              // Original response (if includeRaw: true)
}
```

### Error Structure

```typescript
interface ParserError {
  code: string;                  // Error code (e.g., "INVALID_RESPONSE")
  message: string;               // Human-readable message
  details?: unknown;             // Additional context
}
```

## Extending the Parser

### Create a Custom Parser

```typescript
import { SDKResponseParser } from "./lib/sdk-parser";

class MyCustomParser extends SDKResponseParser {
  parseAndLog(response: unknown) {
    console.log("Parsing response...");
    const result = this.parse(response);
    
    if (result.success) {
      console.log(`✓ Parsed successfully: ${result.data.id}`);
    } else {
      console.log(`✗ Parse failed: ${result.error.message}`);
    }
    
    return result;
  }
}

const parser = new MyCustomParser();
parser.parseAndLog(response);
```

## Performance Tips

1. **Reuse Parser Instances**: Create a parser once and reuse it
2. **Disable Unused Features**: Set `parseToolUses: false` if you don't need tool parsing
3. **Disable Raw Response**: Set `includeRaw: false` to reduce memory usage with large responses
4. **Use Specific Methods**: Use `getText()` or `getToolUses()` directly when you only need one thing

## Error Codes

- `INVALID_RESPONSE` - Response doesn't match expected structure
- `PARSE_ERROR` - General parsing error
- `UNKNOWN_ERROR` - Unexpected error occurred
- `BATCH_PARSE_ERROR` - Error during batch parsing
- `TRANSFORM_ERROR` - Custom formatter threw an error

## Examples

See `examples.ts` for detailed examples of:
- Basic response parsing
- Tool use parsing
- Batch processing
- Error handling
- Custom transformations
- Token analysis
- Response logging and validation

## Best Practices

1. ✅ Always check `result.success` before accessing data
2. ✅ Handle null text gracefully (responses can be tool-only)
3. ✅ Validate responses before parsing if dealing with untrusted input
4. ✅ Use TypeScript types for type safety
5. ✅ Leverage custom transformations for domain-specific processing
6. ✅ Log parser errors for debugging

## Common Gotchas

❌ **Don't assume text is always present**
- Some responses only contain tool calls
- Always check if `text` is null

❌ **Don't miss cache tokens**
- Cache tokens affect cost calculations
- Use `calculateTotalTokens()` which includes cache read tokens

❌ **Don't recreate parser for each response**
- Reuse parser instances for performance
- Parser is stateless and thread-safe

❌ **Don't ignore stop_reason**
- Different stop reasons mean different things
- `tool_use` = tool called, `max_tokens` = truncated response

## See Also

- `README.md` - Full API documentation
- `types.ts` - Type definitions
- `examples.ts` - Working code examples
