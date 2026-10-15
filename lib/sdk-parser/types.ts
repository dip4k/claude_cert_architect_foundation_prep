/**
 * Type definitions for SDK Response Parser
 * Supports parsing Claude API and similar SDK responses
 */

export interface ContentBlock {
  type: string;
  text?: string;
  id?: string;
  name?: string;
  input?: Record<string, unknown>;
}

export interface ToolUseBlock extends ContentBlock {
  type: "tool_use";
  id: string;
  name: string;
  input: Record<string, unknown>;
}

export interface TextBlock extends ContentBlock {
  type: "text";
  text: string;
}

export interface UsageInfo {
  input_tokens: number;
  output_tokens: number;
  cache_creation_input_tokens?: number;
  cache_read_input_tokens?: number;
}

export interface SDKResponse {
  id: string;
  type: string;
  role: string;
  content: ContentBlock[];
  model: string;
  stop_reason: string;
  stop_sequence?: string;
  usage: UsageInfo;
}

export interface ParsedResponse {
  id: string;
  model: string;
  stopReason: string;
  text: string | null;
  toolUses: ToolUseBlock[];
  allBlocks: ContentBlock[];
  usage: UsageInfo;
  raw: SDKResponse;
}

export interface ParserOptions {
  includeRaw?: boolean;
  throwOnError?: boolean;
  parseToolUses?: boolean;
}

export interface ParserError {
  code: string;
  message: string;
  details?: unknown;
}

export type ParserResult<T = ParsedResponse> =
  | { success: true; data: T }
  | { success: false; error: ParserError };
