/**
 * Utility functions for SDK Response Parser
 */

import { ContentBlock, TextBlock, ToolUseBlock } from "./types";

/**
 * Extract text content from content blocks
 */
export function extractText(blocks: ContentBlock[]): string | null {
  const textBlocks = blocks.filter((block) => block.type === "text") as TextBlock[];
  if (textBlocks.length === 0) return null;
  return textBlocks.map((block) => block.text).join("\n");
}

/**
 * Extract tool use blocks from content
 */
export function extractToolUses(blocks: ContentBlock[]): ToolUseBlock[] {
  return blocks.filter((block) => block.type === "tool_use") as ToolUseBlock[];
}

/**
 * Validate required fields in response
 */
export function validateResponse(response: unknown): boolean {
  if (typeof response !== "object" || response === null) {
    return false;
  }

  const obj = response as Record<string, unknown>;
  const requiredFields = ["id", "content", "model", "stop_reason", "usage"];

  return requiredFields.every((field) => field in obj);
}

/**
 * Format token usage information
 */
export function formatTokenUsage(usage: {
  input_tokens: number;
  output_tokens: number;
  cache_creation_input_tokens?: number;
  cache_read_input_tokens?: number;
}): string {
  let result = `Input: ${usage.input_tokens}, Output: ${usage.output_tokens}`;

  if (usage.cache_creation_input_tokens) {
    result += `, Cache Creation: ${usage.cache_creation_input_tokens}`;
  }

  if (usage.cache_read_input_tokens) {
    result += `, Cache Read: ${usage.cache_read_input_tokens}`;
  }

  return result;
}

/**
 * Calculate total tokens used
 */
export function calculateTotalTokens(usage: {
  input_tokens: number;
  output_tokens: number;
  cache_read_input_tokens?: number;
}): number {
  return (
    usage.input_tokens + usage.output_tokens + (usage.cache_read_input_tokens || 0)
  );
}

/**
 * Check if response has tool use content
 */
export function hasToolUse(blocks: ContentBlock[]): boolean {
  return blocks.some((block) => block.type === "tool_use");
}

/**
 * Check if response has text content
 */
export function hasText(blocks: ContentBlock[]): boolean {
  return blocks.some((block) => block.type === "text");
}

/**
 * Get stop reason as human-readable string
 */
export function formatStopReason(stopReason: string): string {
  const reasonMap: Record<string, string> = {
    end_turn: "Response completed naturally",
    max_tokens: "Maximum token limit reached",
    stop_sequence: "Stop sequence encountered",
    tool_use: "Tool use initiated",
  };

  return reasonMap[stopReason] || stopReason;
}
