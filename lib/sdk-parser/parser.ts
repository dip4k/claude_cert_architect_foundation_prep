/**
 * Generic SDK Response Parser
 * Parses Claude API and similar SDK responses
 */

import {
  ContentBlock,
  ParsedResponse,
  ParserError,
  ParserOptions,
  ParserResult,
  SDKResponse,
  ToolUseBlock,
  UsageInfo,
} from "./types";
import {
  extractText,
  extractToolUses,
  validateResponse,
  hasToolUse,
} from "./utils";

export class SDKResponseParser {
  private options: Required<ParserOptions>;

  constructor(options: ParserOptions = {}) {
    this.options = {
      includeRaw: options.includeRaw ?? true,
      throwOnError: options.throwOnError ?? false,
      parseToolUses: options.parseToolUses ?? true,
    };
  }

  /**
   * Parse an SDK response
   */
  parse(response: unknown): ParserResult<ParsedResponse> {
    try {
      // Validate response structure
      if (!validateResponse(response)) {
        throw this.createError(
          "INVALID_RESPONSE",
          "Response does not match expected structure"
        );
      }

      const sdkResponse = response as SDKResponse;

      // Extract content
      const text = extractText(sdkResponse.content);
      const toolUses = this.options.parseToolUses
        ? extractToolUses(sdkResponse.content)
        : [];

      // Build parsed response
      const parsed: ParsedResponse = {
        id: sdkResponse.id,
        model: sdkResponse.model,
        stopReason: sdkResponse.stop_reason,
        text,
        toolUses,
        allBlocks: sdkResponse.content,
        usage: sdkResponse.usage,
        raw: this.options.includeRaw ? sdkResponse : ({} as SDKResponse),
      };

      return { success: true, data: parsed };
    } catch (error) {
      const parserError = error instanceof Error
        ? this.createError("PARSE_ERROR", error.message)
        : this.createError("UNKNOWN_ERROR", "An unknown error occurred");

      if (this.options.throwOnError) {
        throw parserError;
      }

      return { success: false, error: parserError };
    }
  }

  /**
   * Parse multiple responses
   */
  parseMany(responses: unknown[]): ParserResult<ParsedResponse[]> {
    try {
      const results = responses.map((response) => {
        const result = this.parse(response);
        if (!result.success) {
          throw result.error;
        }
        return result.data;
      });

      return { success: true, data: results };
    } catch (error) {
      const parserError = error instanceof Error
        ? this.createError("BATCH_PARSE_ERROR", error.message)
        : this.createError("BATCH_ERROR", "Failed to parse batch");

      if (this.options.throwOnError) {
        throw parserError;
      }

      return { success: false, error: parserError };
    }
  }

  /**
   * Extract only text content from response
   */
  getText(response: unknown): ParserResult<string | null> {
    const parsed = this.parse(response);
    if (!parsed.success) {
      return parsed;
    }

    return { success: true, data: parsed.data.text };
  }

  /**
   * Extract only tool uses from response
   */
  getToolUses(response: unknown): ParserResult<ToolUseBlock[]> {
    const parsed = this.parse(response);
    if (!parsed.success) {
      return parsed;
    }

    return { success: true, data: parsed.data.toolUses };
  }

  /**
   * Get usage information from response
   */
  getUsage(response: unknown): ParserResult<UsageInfo> {
    const parsed = this.parse(response);
    if (!parsed.success) {
      return parsed;
    }

    return { success: true, data: parsed.data.usage };
  }

  /**
   * Check if response uses tools
   */
  usesTools(response: unknown): ParserResult<boolean> {
    const parsed = this.parse(response);
    if (!parsed.success) {
      return parsed;
    }

    return { success: true, data: hasToolUse(parsed.data.allBlocks) };
  }

  /**
   * Get response metadata
   */
  getMetadata(response: unknown): ParserResult<{
    id: string;
    model: string;
    stopReason: string;
    hasText: boolean;
    hasToolUse: boolean;
  }> {
    const parsed = this.parse(response);
    if (!parsed.success) {
      return parsed;
    }

    return {
      success: true,
      data: {
        id: parsed.data.id,
        model: parsed.data.model,
        stopReason: parsed.data.stopReason,
        hasText: parsed.data.text !== null,
        hasToolUse: parsed.data.toolUses.length > 0,
      },
    };
  }

  /**
   * Transform response with custom formatter
   */
  transform<T>(
    response: unknown,
    formatter: (parsed: ParsedResponse) => T
  ): ParserResult<T> {
    const parsed = this.parse(response);
    if (!parsed.success) {
      return parsed;
    }

    try {
      const transformed = formatter(parsed.data);
      return { success: true, data: transformed };
    } catch (error) {
      const parserError = error instanceof Error
        ? this.createError("TRANSFORM_ERROR", error.message)
        : this.createError("TRANSFORM_ERROR", "Failed to transform response");

      if (this.options.throwOnError) {
        throw parserError;
      }

      return { success: false, error: parserError };
    }
  }

  /**
   * Create a parser error
   */
  private createError(code: string, message: string, details?: unknown): ParserError {
    return { code, message, details };
  }

  /**
   * Update parser options
   */
  setOptions(options: ParserOptions): void {
    this.options = { ...this.options, ...options };
  }

  /**
   * Get current options
   */
  getOptions(): ParserOptions {
    return { ...this.options };
  }
}

/**
 * Create a parser instance with default options
 */
export function createParser(options?: ParserOptions): SDKResponseParser {
  return new SDKResponseParser(options);
}

/**
 * Parse a response with a one-off parser
 */
export function parse(response: unknown, options?: ParserOptions): ParserResult<ParsedResponse> {
  return createParser(options).parse(response);
}
