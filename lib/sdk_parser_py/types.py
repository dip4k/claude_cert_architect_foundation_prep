"""
Type definitions for SDK Response Parser
Supports parsing Claude API and similar SDK responses
"""

from typing import Any, Dict, List, Optional, TypedDict, Union
from dataclasses import dataclass, field


class ContentBlockDict(TypedDict, total=False):
    """Content block as dictionary"""
    type: str
    text: str
    id: str
    name: str
    input: Dict[str, Any]


class ToolUseBlockDict(TypedDict):
    """Tool use block structure"""
    type: str  # "tool_use"
    id: str
    name: str
    input: Dict[str, Any]


class TextBlockDict(TypedDict):
    """Text block structure"""
    type: str  # "text"
    text: str


class UsageInfoDict(TypedDict, total=False):
    """Token usage information"""
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int
    cache_read_input_tokens: int


class SDKResponseDict(TypedDict, total=False):
    """SDK Response structure"""
    id: str
    type: str
    role: str
    content: List[ContentBlockDict]
    model: str
    stop_reason: str
    stop_sequence: str
    usage: UsageInfoDict


# Dataclasses for easier type handling


@dataclass
class ContentBlock:
    """Content block"""
    type: str
    text: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None
    input: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContentBlock":
        """Create from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            k: v for k, v in self.__dict__.items()
            if v is not None
        }


@dataclass
class ToolUseBlock(ContentBlock):
    """Tool use block"""
    type: str = "tool_use"
    id: str = ""
    name: str = ""
    input: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolUseBlock":
        """Create from dictionary"""
        return cls(
            type=data.get("type", "tool_use"),
            id=data.get("id", ""),
            name=data.get("name", ""),
            input=data.get("input", {}),
        )


@dataclass
class TextBlock(ContentBlock):
    """Text block"""
    type: str = "text"
    text: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TextBlock":
        """Create from dictionary"""
        return cls(
            type=data.get("type", "text"),
            text=data.get("text", ""),
        )


@dataclass
class UsageInfo:
    """Token usage information"""
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: Optional[int] = None
    cache_read_input_tokens: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UsageInfo":
        """Create from dictionary"""
        return cls(
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
            cache_creation_input_tokens=data.get("cache_creation_input_tokens"),
            cache_read_input_tokens=data.get("cache_read_input_tokens"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            **({"cache_creation_input_tokens": self.cache_creation_input_tokens}
               if self.cache_creation_input_tokens else {}),
            **({"cache_read_input_tokens": self.cache_read_input_tokens}
               if self.cache_read_input_tokens else {}),
        }


@dataclass
class ParsedResponse:
    """Parsed SDK response"""
    id: str
    model: str
    stop_reason: str
    text: Optional[str]
    tool_uses: List[ToolUseBlock]
    all_blocks: List[ContentBlock]
    usage: UsageInfo
    raw: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "model": self.model,
            "stop_reason": self.stop_reason,
            "text": self.text,
            "tool_uses": [t.to_dict() for t in self.tool_uses],
            "all_blocks": [b.to_dict() for b in self.all_blocks],
            "usage": self.usage.to_dict(),
            "raw": self.raw,
        }


@dataclass
class ParserError(Exception):
    """Parser error"""
    code: str
    message: str
    details: Optional[Any] = None

    def __str__(self) -> str:
        """String representation"""
        if self.details:
            return f"{self.code}: {self.message} ({self.details})"
        return f"{self.code}: {self.message}"


@dataclass
class ParserOptions:
    """Parser options"""
    include_raw: bool = True
    throw_on_error: bool = False
    parse_tool_uses: bool = True


# Result type using Union for explicit success/failure handling
class ParserResult(Union[Dict[str, Any], Dict[str, Any]]):
    """Parser result - either success with data or failure with error"""
    pass


def success_result(data: Any) -> Dict[str, Any]:
    """Create a success result"""
    return {"success": True, "data": data}


def error_result(error: ParserError) -> Dict[str, Any]:
    """Create an error result"""
    return {"success": False, "error": error}


def is_success(result: Dict[str, Any]) -> bool:
    """Check if result is successful"""
    return result.get("success", False)


def is_error(result: Dict[str, Any]) -> bool:
    """Check if result is an error"""
    return not result.get("success", False)
