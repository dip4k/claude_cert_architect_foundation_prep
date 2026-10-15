"""
Generic SDK Response Parser
Parses Claude API and similar SDK responses
"""

from typing import Any, Callable, Dict, List, Optional, TypeVar

from .types import (
    ContentBlock,
    ParsedResponse,
    ParserError,
    ParserOptions,
    ToolUseBlock,
    UsageInfo,
    error_result,
    success_result,
)
from .utils import (
    extract_content_blocks,
    extract_text,
    extract_tool_uses,
    has_tool_use,
    validate_response,
)

T = TypeVar("T")


class SDKResponseParser:
    """Generic SDK Response Parser"""

    def __init__(self, options: Optional[ParserOptions] = None):
        """
        Initialize parser with options

        Args:
            options: Parser options
        """
        if options is None:
            options = ParserOptions()
        self.options = options

    def parse(self, response: Any) -> Dict[str, Any]:
        """
        Parse an SDK response

        Args:
            response: Response to parse

        Returns:
            Result dict with success/error
        """
        try:
            # Validate response structure
            if not validate_response(response):
                raise self._create_error(
                    "INVALID_RESPONSE",
                    "Response does not match expected structure",
                )

            # Extract content blocks
            content_blocks = extract_content_blocks(response.get("content", []))

            # Extract text and tool uses
            text = extract_text(content_blocks)
            tool_uses = (
                extract_tool_uses(content_blocks)
                if self.options.parse_tool_uses
                else []
            )

            # Create usage info
            usage = UsageInfo.from_dict(response.get("usage", {}))

            # Build parsed response
            parsed = ParsedResponse(
                id=response.get("id", ""),
                model=response.get("model", ""),
                stop_reason=response.get("stop_reason", ""),
                text=text,
                tool_uses=tool_uses,
                all_blocks=content_blocks,
                usage=usage,
                raw=response if self.options.include_raw else None,
            )

            return success_result(parsed)

        except ParserError as e:
            if self.options.throw_on_error:
                raise
            return error_result(e)
        except Exception as e:
            error = self._create_error("PARSE_ERROR", str(e))
            if self.options.throw_on_error:
                raise error
            return error_result(error)

    def parse_many(self, responses: List[Any]) -> Dict[str, Any]:
        """
        Parse multiple responses

        Args:
            responses: List of responses to parse

        Returns:
            Result dict with list of parsed responses or error
        """
        try:
            results = []
            for response in responses:
                result = self.parse(response)
                if not result.get("success"):
                    raise result.get("error")
                results.append(result.get("data"))

            return success_result(results)

        except ParserError as e:
            if self.options.throw_on_error:
                raise
            return error_result(e)
        except Exception as e:
            error = self._create_error("BATCH_PARSE_ERROR", str(e))
            if self.options.throw_on_error:
                raise error
            return error_result(error)

    def get_text(self, response: Any) -> Dict[str, Any]:
        """
        Extract only text content from response

        Args:
            response: Response to parse

        Returns:
            Result dict with text or error
        """
        result = self.parse(response)
        if not result.get("success"):
            return result

        parsed: ParsedResponse = result.get("data")
        return success_result(parsed.text)

    def get_tool_uses(self, response: Any) -> Dict[str, Any]:
        """
        Extract only tool uses from response

        Args:
            response: Response to parse

        Returns:
            Result dict with tool uses or error
        """
        result = self.parse(response)
        if not result.get("success"):
            return result

        parsed: ParsedResponse = result.get("data")
        return success_result(parsed.tool_uses)

    def get_usage(self, response: Any) -> Dict[str, Any]:
        """
        Get usage information from response

        Args:
            response: Response to parse

        Returns:
            Result dict with usage info or error
        """
        result = self.parse(response)
        if not result.get("success"):
            return result

        parsed: ParsedResponse = result.get("data")
        return success_result(parsed.usage)

    def uses_tools(self, response: Any) -> Dict[str, Any]:
        """
        Check if response uses tools

        Args:
            response: Response to parse

        Returns:
            Result dict with boolean or error
        """
        result = self.parse(response)
        if not result.get("success"):
            return result

        parsed: ParsedResponse = result.get("data")
        return success_result(has_tool_use(parsed.all_blocks))

    def get_metadata(self, response: Any) -> Dict[str, Any]:
        """
        Get response metadata

        Args:
            response: Response to parse

        Returns:
            Result dict with metadata or error
        """
        result = self.parse(response)
        if not result.get("success"):
            return result

        parsed: ParsedResponse = result.get("data")
        metadata = {
            "id": parsed.id,
            "model": parsed.model,
            "stop_reason": parsed.stop_reason,
            "has_text": parsed.text is not None,
            "has_tool_use": len(parsed.tool_uses) > 0,
        }
        return success_result(metadata)

    def transform(self, response: Any, formatter: Callable[[ParsedResponse], T]) -> Dict[str, Any]:
        """
        Transform response with custom formatter

        Args:
            response: Response to parse
            formatter: Function to transform parsed response

        Returns:
            Result dict with transformed data or error
        """
        parsed_result = self.parse(response)
        if not parsed_result.get("success"):
            return parsed_result

        try:
            parsed: ParsedResponse = parsed_result.get("data")
            transformed = formatter(parsed)
            return success_result(transformed)
        except Exception as e:
            error = self._create_error("TRANSFORM_ERROR", str(e))
            if self.options.throw_on_error:
                raise error
            return error_result(error)

    def set_options(self, options: ParserOptions) -> None:
        """
        Update parser options

        Args:
            options: New options
        """
        self.options = options

    def get_options(self) -> ParserOptions:
        """
        Get current options

        Returns:
            Current parser options
        """
        return ParserOptions(
            include_raw=self.options.include_raw,
            throw_on_error=self.options.throw_on_error,
            parse_tool_uses=self.options.parse_tool_uses,
        )

    @staticmethod
    def _create_error(code: str, message: str, details: Optional[Any] = None) -> ParserError:
        """
        Create a parser error

        Args:
            code: Error code
            message: Error message
            details: Additional details

        Returns:
            ParserError instance
        """
        return ParserError(code=code, message=message, details=details)


def create_parser(options: Optional[ParserOptions] = None) -> SDKResponseParser:
    """
    Create a parser instance with default options

    Args:
        options: Parser options

    Returns:
        SDKResponseParser instance
    """
    return SDKResponseParser(options)


def parse(response: Any, options: Optional[ParserOptions] = None) -> Dict[str, Any]:
    """
    Parse a response with a one-off parser

    Args:
        response: Response to parse
        options: Parser options

    Returns:
        Result dict with parsed response or error
    """
    parser = create_parser(options)
    return parser.parse(response)
