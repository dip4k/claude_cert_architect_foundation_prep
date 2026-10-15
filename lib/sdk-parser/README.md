# SDK Response Parser

A generic, reusable parser for Claude API and similar SDK responses. Built for Claude Certified Architect Foundation practice projects.

## Features

- ✨ **Generic Design**: Works with any SDK response format following the standard structure
- 🛡️ **Type-Safe**: Full TypeScript support with comprehensive type definitions
- 🎯 **Flexible**: Support for text extraction, tool use parsing, and custom transformations
- 📊 **Utilities**: Helper functions for common operations like token counting and stop reason formatting
- 🔄 **Result Pattern**: Explicit error handling with `success`/`error` pattern (no exceptions by default)
- 🧩 **Modular**: Use individual utilities or the full parser class

## Installation

Copy the `lib/sdk-parser` folder into your project or import as needed.

## Quick Start

```typescript
import { createParser } from "./lib/sdk-parser";

const parser = createParser();
const result = parser.parse(sdkResponse);

if (result.success) {
  console.log(result.data.text);
  console.log(result.data.toolUses);
} else {
  console.error(result.error.message);
}
```

## API Reference

### SDKResponseParser Class

Main parser class for processing SDK responses.

#### Constructor Options

```typescript
interface ParserOptions {
  includeRaw?: boolean;        // Include raw response (default: true)
  throwOnError?: boolean;      // Throw exceptions instead of returning errors (default: false)
  parseToolUses?: boolean;     // Parse tool use blocks (default: true)
}
```

#### Methods

##### `parse(response: unknown): ParserResult<ParsedResponse>`

Parse a single SDK response.

```typescript
const result = parser.parse(response);
if (result.success) {
  const parsed = result.data;
  console.log(parsed.id, parsed.model, parsed.text);
}
```

##### `parseMany(responses: unknown[]): ParserResult<ParsedResponse[]>`

Parse multiple responses at once.

```typescript
const result = parser.parseMany([response1, response2, response3]);
```

##### `getText(response: unknown): ParserResult<string | null>`

Extract only text content from a response.

```typescript
const result = parser.getText(response);
if (result.success) {
  console.log(result.data);
}
```

##### `getToolUses(response: unknown): ParserResult<ToolUseBlock[]>`

Extract tool use blocks from a response.

```typescript
const result = parser.getToolUses(response);
if (result.success) {
  result.data.forEach((tool) => {
    console.log(tool.name, tool.input);
  });
}
```

##### `getUsage(response: unknown): ParserResult<UsageInfo>`

Get token usage information.

```typescript
const result = parser.getUsage(response);
if (result.success) {
  console.log(`Input: ${result.data.input_tokens}, Output: ${result.data.output_tokens}`);
}
```

##### `usesTools(response: unknown): ParserResult<boolean>`

Check if response uses tools.

```typescript
const result = parser.usesTools(response);
if (result.success && result.data) {
  console.log("Response uses tools");
}
```

##### `getMetadata(response: unknown): ParserResult<MetadataInfo>`

Get response metadata.

```typescript
const result = parser.getMetadata(response);
if (result.success) {
  console.log(result.data.id, result.data.model, result.data.stopReason);
}
```

##### `transform<T>(response: unknown, formatter: (parsed: ParsedResponse) => T): ParserResult<T>`

Transform a parsed response with a custom formatter.

```typescript
const result = parser.transform(response, (parsed) => ({
  message: parsed.text,
  toolCount: parsed.toolUses.length,
}));
```

### Utility Functions

#### `extractText(blocks: ContentBlock[]): string | null`

Extract text from content blocks.

```typescript
const text = extractText(response.content);
```

#### `extractToolUses(blocks: ContentBlock[]): ToolUseBlock[]`

Extract tool use blocks.

```typescript
const tools = extractToolUses(response.content);
```

#### `validateResponse(response: unknown): boolean`

Validate response structure.

```typescript
if (validateResponse(response)) {
  // Response is valid
}
```

#### `formatTokenUsage(usage: UsageInfo): string`

Format token usage as a readable string.

```typescript
const usage = formatTokenUsage(response.usage);
console.log(usage); // "Input: 100, Output: 50"
```

#### `calculateTotalTokens(usage: UsageInfo): number`

Calculate total tokens used.

```typescript
const total = calculateTotalTokens(response.usage);
```

#### `hasToolUse(blocks: ContentBlock[]): boolean`

Check if blocks contain tool use.

```typescript
if (hasToolUse(response.content)) {
  // Handle tool use
}
```

#### `hasText(blocks: ContentBlock[]): boolean`

Check if blocks contain text.

```typescript
if (hasText(response.content)) {
  // Handle text response
}
```

#### `formatStopReason(stopReason: string): string`

Format stop reason as human-readable string.

```typescript
console.log(formatStopReason("end_turn")); // "Response completed naturally"
```

## Type Definitions

### ParsedResponse

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
```

### SDKResponse

```typescript
interface SDKResponse {
  id: string;
  type: string;
  role: string;
  content: ContentBlock[];
  model: string;
  stop_reason: string;
  stop_sequence?: string;
  usage: UsageInfo;
}
```

### ParserResult

```typescript
type ParserResult<T = ParsedResponse> = 
  | { success: true; data: T }
  | { success: false; error: ParserError };
```

## Examples

### Basic Usage

```typescript
import { createParser } from "./lib/sdk-parser";

const parser = createParser();
const result = parser.parse(apiResponse);

if (result.success) {
  console.log("Response ID:", result.data.id);
  console.log("Model:", result.data.model);
  console.log("Text:", result.data.text);
  console.log("Stop Reason:", result.data.stopReason);
} else {
  console.error("Parse failed:", result.error.message);
}
```

### Error Handling with Exceptions

```typescript
const parser = createParser({ throwOnError: true });

try {
  const parsed = parser.parse(response);
  // Handle parsed.data
} catch (error) {
  // Handle error
}
```

### Custom Transformation

```typescript
const result = parser.transform(response, (parsed) => ({
  summary: parsed.text?.substring(0, 100),
  toolCount: parsed.toolUses.length,
  tokensUsed: parsed.usage.input_tokens + parsed.usage.output_tokens,
}));
```

### Processing Tool Calls

```typescript
const result = parser.getToolUses(response);

if (result.success) {
  result.data.forEach((tool) => {
    console.log(`Calling tool: ${tool.name}`);
    console.log(`With inputs:`, tool.input);
  });
}
```

### Batch Processing

```typescript
const responses = [...]; // Array of SDK responses

const result = parser.parseMany(responses);

if (result.success) {
  result.data.forEach((parsed) => {
    console.log(`Response from ${parsed.model}: ${parsed.text}`);
  });
}
```

### Token Usage Analysis

```typescript
import { calculateTotalTokens, formatTokenUsage } from "./lib/sdk-parser";

const response = apiResponse;
console.log(formatTokenUsage(response.usage));
const total = calculateTotalTokens(response.usage);
console.log(`Total tokens: ${total}`);
```

## Development

### Structure

- `types.ts` - TypeScript type definitions
- `parser.ts` - Main parser class and factory functions
- `utils.ts` - Utility functions
- `index.ts` - Main exports

### Testing

To add tests, create a `__tests__` or `tests` directory and import the parser:

```typescript
import { createParser } from "../lib/sdk-parser";

describe("SDKResponseParser", () => {
  it("should parse valid responses", () => {
    // Test implementation
  });
});
```

## Best Practices

1. **Reuse Parser Instance**: Create a parser once and reuse it for multiple responses
2. **Check Success Flag**: Always check `result.success` before accessing `result.data`
3. **Handle Edge Cases**: Tool responses may have null text; check before using
4. **Type Safety**: Use TypeScript types to ensure type safety
5. **Options Configuration**: Set appropriate parser options for your use case

## Extending the Parser

You can extend the `SDKResponseParser` class for domain-specific implementations:

```typescript
class CustomParser extends SDKResponseParser {
  parseAndValidate(response: unknown) {
    const result = this.parse(response);
    if (!result.success) return result;
    
    // Custom validation logic
    return result;
  }
}
```

## License

Part of Claude Certified Architect Foundation practice projects.
