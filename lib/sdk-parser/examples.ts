/**
 * Usage Examples for SDK Response Parser
 * Reference implementations for common scenarios
 */

import { createParser, SDKResponseParser, calculateTotalTokens, formatTokenUsage } from "./index";
import { ParsedResponse, ParserResult, ToolUseBlock } from "./types";

/**
 * Example 1: Basic response parsing
 */
export function basicParsing() {
  const parser = createParser();

  // Simulated API response
  const apiResponse = {
    id: "msg_123",
    type: "message",
    role: "assistant",
    content: [
      {
        type: "text",
        text: "Hello! How can I help you today?",
      },
    ],
    model: "claude-3-5-sonnet-20241022",
    stop_reason: "end_turn",
    usage: {
      input_tokens: 10,
      output_tokens: 15,
    },
  };

  const result = parser.parse(apiResponse);

  if (result.success) {
    console.log("Message ID:", result.data.id);
    console.log("Response text:", result.data.text);
    console.log("Stop reason:", result.data.stopReason);
  }
}

/**
 * Example 2: Tool use parsing
 */
export function toolUseParsing() {
  const parser = createParser();

  const toolResponse = {
    id: "msg_456",
    type: "message",
    role: "assistant",
    content: [
      {
        type: "text",
        text: "I'll help you with that. Let me call the appropriate tool.",
      },
      {
        type: "tool_use",
        id: "tool_call_1",
        name: "get_weather",
        input: {
          location: "San Francisco",
          unit: "celsius",
        },
      },
    ],
    model: "claude-3-5-sonnet-20241022",
    stop_reason: "tool_use",
    usage: {
      input_tokens: 50,
      output_tokens: 100,
    },
  };

  const result = parser.parse(toolResponse);

  if (result.success) {
    const data = result.data;
    console.log("Text response:", data.text);

    data.toolUses.forEach((tool) => {
      console.log(`Tool: ${tool.name}`);
      console.log("Input:", tool.input);
    });
  }
}

/**
 * Example 3: Batch processing multiple responses
 */
export function batchProcessing() {
  const parser = createParser();

  const responses = [
    {
      id: "msg_001",
      type: "message",
      role: "assistant",
      content: [{ type: "text", text: "First response" }],
      model: "claude-3-5-sonnet-20241022",
      stop_reason: "end_turn",
      usage: { input_tokens: 10, output_tokens: 20 },
    },
    {
      id: "msg_002",
      type: "message",
      role: "assistant",
      content: [{ type: "text", text: "Second response" }],
      model: "claude-3-5-sonnet-20241022",
      stop_reason: "end_turn",
      usage: { input_tokens: 15, output_tokens: 25 },
    },
  ];

  const result = parser.parseMany(responses);

  if (result.success) {
    result.data.forEach((parsed, index) => {
      console.log(`Response ${index + 1}: ${parsed.text}`);
      console.log(`Total tokens: ${calculateTotalTokens(parsed.usage)}`);
    });
  }
}

/**
 * Example 4: Error handling
 */
export function errorHandling() {
  const parser = createParser({ throwOnError: false });

  const invalidResponse = {
    // Missing required fields
    id: "msg_789",
  };

  const result = parser.parse(invalidResponse);

  if (!result.success) {
    console.error("Parse error:");
    console.error("Code:", result.error.code);
    console.error("Message:", result.error.message);
  }
}

/**
 * Example 5: Custom transformation
 */
export function customTransformation() {
  const parser = createParser();

  const response = {
    id: "msg_999",
    type: "message",
    role: "assistant",
    content: [
      { type: "text", text: "Hello, world!" },
      {
        type: "tool_use",
        id: "tool_1",
        name: "search",
        input: { query: "Claude API" },
      },
    ],
    model: "claude-3-5-sonnet-20241022",
    stop_reason: "tool_use",
    usage: { input_tokens: 50, output_tokens: 100 },
  };

  const result = parser.transform(response, (parsed) => ({
    summary: {
      messageId: parsed.id,
      model: parsed.model,
      hasText: parsed.text !== null,
      toolCount: parsed.toolUses.length,
    },
    content: {
      text: parsed.text || "No text response",
      tools: parsed.toolUses.map((t) => ({ name: t.name, input: t.input })),
    },
    efficiency: {
      inputTokens: parsed.usage.input_tokens,
      outputTokens: parsed.usage.output_tokens,
      totalTokens: calculateTotalTokens(parsed.usage),
    },
  }));

  if (result.success) {
    console.log(JSON.stringify(result.data, null, 2));
  }
}

/**
 * Example 6: Checking response characteristics
 */
export function checkResponseCharacteristics() {
  const parser = createParser();

  const response = {
    id: "msg_abc",
    type: "message",
    role: "assistant",
    content: [
      { type: "text", text: "Processing..." },
      {
        type: "tool_use",
        id: "tool_x",
        name: "analyze",
        input: { data: "sample" },
      },
    ],
    model: "claude-3-5-sonnet-20241022",
    stop_reason: "tool_use",
    usage: { input_tokens: 100, output_tokens: 50 },
  };

  const hasTools = parser.usesTools(response);
  const metadata = parser.getMetadata(response);

  if (hasTools.success && hasTools.data) {
    console.log("This response uses tools");
  }

  if (metadata.success) {
    const m = metadata.data;
    console.log(`Response characteristics:`);
    console.log(`- ID: ${m.id}`);
    console.log(`- Model: ${m.model}`);
    console.log(`- Has text: ${m.hasText}`);
    console.log(`- Has tool use: ${m.hasToolUse}`);
    console.log(`- Stop reason: ${m.stopReason}`);
  }
}

/**
 * Example 7: Token analysis and reporting
 */
export function tokenAnalysis() {
  const parser = createParser();

  const responses = [
    {
      id: "msg_1",
      type: "message",
      role: "assistant",
      content: [{ type: "text", text: "Short response" }],
      model: "claude-3-5-sonnet-20241022",
      stop_reason: "end_turn",
      usage: { input_tokens: 50, output_tokens: 20 },
    },
    {
      id: "msg_2",
      type: "message",
      role: "assistant",
      content: [{ type: "text", text: "Much longer response with more details..." }],
      model: "claude-3-5-sonnet-20241022",
      stop_reason: "end_turn",
      usage: { input_tokens: 50, output_tokens: 200 },
    },
  ];

  const parseResult = parser.parseMany(responses);

  if (parseResult.success) {
    let totalInputTokens = 0;
    let totalOutputTokens = 0;

    parseResult.data.forEach((parsed, index) => {
      console.log(`\nResponse ${index + 1}:`);
      console.log(formatTokenUsage(parsed.usage));
      totalInputTokens += parsed.usage.input_tokens;
      totalOutputTokens += parsed.usage.output_tokens;
    });

    console.log(`\nBatch Summary:`);
    console.log(`Total input tokens: ${totalInputTokens}`);
    console.log(`Total output tokens: ${totalOutputTokens}`);
    console.log(`Total tokens: ${totalInputTokens + totalOutputTokens}`);
  }
}

/**
 * Example 8: Exception-based error handling
 */
export function exceptionHandling() {
  // Parser with throwOnError enabled
  const parser = createParser({ throwOnError: true });

  try {
    const invalidResponse = { id: "test" }; // Missing required fields
    const parsed = parser.parse(invalidResponse);
    console.log("Parsed successfully:", parsed);
  } catch (error) {
    console.error("Failed to parse response:", error);
  }
}

/**
 * Example 9: Working with cache tokens
 */
export function cacheTokenHandling() {
  const parser = createParser();

  const cachedResponse = {
    id: "msg_cache",
    type: "message",
    role: "assistant",
    content: [{ type: "text", text: "Using cached context..." }],
    model: "claude-3-5-sonnet-20241022",
    stop_reason: "end_turn",
    usage: {
      input_tokens: 50,
      output_tokens: 100,
      cache_creation_input_tokens: 1000,
      cache_read_input_tokens: 500,
    },
  };

  const result = parser.parse(cachedResponse);

  if (result.success) {
    console.log("Token usage with cache:");
    console.log(formatTokenUsage(result.data.usage));
    console.log(`Total tokens (including cache): ${calculateTotalTokens(result.data.usage)}`);
  }
}

/**
 * Example 10: Building a response logger
 */
export function buildResponseLogger() {
  const parser = createParser({ includeRaw: true });

  function logResponse(response: unknown): void {
    const result = parser.parse(response);

    if (!result.success) {
      console.error("Failed to parse response:", result.error);
      return;
    }

    const data = result.data;
    const timestamp = new Date().toISOString();

    console.log(`[${timestamp}] Response Log:`);
    console.log(`  ID: ${data.id}`);
    console.log(`  Model: ${data.model}`);
    console.log(`  Stop Reason: ${data.stopReason}`);
    console.log(`  Content: ${data.text || "(tool use only)"}`);
    console.log(`  Tools Called: ${data.toolUses.length}`);
    console.log(`  Token Usage: ${formatTokenUsage(data.usage)}`);
  }

  // Example usage
  const sampleResponse = {
    id: "msg_log_test",
    type: "message",
    role: "assistant",
    content: [{ type: "text", text: "Logging test response" }],
    model: "claude-3-5-sonnet-20241022",
    stop_reason: "end_turn",
    usage: { input_tokens: 10, output_tokens: 30 },
  };

  logResponse(sampleResponse);
}

/**
 * Example 11: Creating a response validator
 */
export function buildResponseValidator() {
  const parser = createParser();

  function validateApiResponse(response: unknown): {
    isValid: boolean;
    errors: string[];
  } {
    const result = parser.parse(response);

    if (!result.success) {
      return {
        isValid: false,
        errors: [result.error.message],
      };
    }

    const errors: string[] = [];
    const data = result.data;

    // Custom validation rules
    if (!data.text && data.toolUses.length === 0) {
      errors.push("Response contains neither text nor tool calls");
    }

    if (data.usage.output_tokens > 4000) {
      errors.push("Output tokens exceed expected limit");
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }

  // Example usage
  const response = {
    id: "msg_validate",
    type: "message",
    role: "assistant",
    content: [{ type: "text", text: "Valid response" }],
    model: "claude-3-5-sonnet-20241022",
    stop_reason: "end_turn",
    usage: { input_tokens: 20, output_tokens: 40 },
  };

  const validation = validateApiResponse(response);
  console.log("Validation result:", validation);
}
