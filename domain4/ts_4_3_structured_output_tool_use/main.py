"""
Domain 4: Prompt Engineering & Structured Output
Task Statement 4.3: Enforce structured output using tool use and JSON schemas
Exam Scenario 6: Structured Data Extraction

Intent: a tool with a JSON schema removes JSON SYNTAX errors, but not SEMANTIC errors (line
items that do not add up). So the schema stays honest about missing data (nullable fields, an
"unclear" enum value, "other" + detail) and Python validates the meaning afterwards.

Key ideas:
1. Nullable / optional fields so the model returns null instead of fabricating.
2. Enum with "unclear" and "other" + detail string.
3. calculated_total, stated_total, conflict_detected.
4. tool_choice: auto, any (several extraction tools, type unknown) or a forced named tool.
5. Extended thinking only allows tool_choice auto/none, so a forced tool call must NOT carry
   `thinking`. Never send temperature with thinking.
6. Absent in source (null, do not retry) vs format error (retry with feedback).

Manual live run (WSL Ubuntu, costs tokens, never automated):
    uv run domain4/ts_4_3_structured_output_tool_use/main.py
"""

import json
import os
import re
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lib.response_logger import ResponseTrail, get_agent_trail_path  # noqa: E402

EXTRACTION_MODEL = "claude-haiku-4-5"  # workers / extraction
REASONING_MODEL = "claude-sonnet-4-5"  # reasoning / generator
TOOL_NAME = "extract_invoice"
MAX_TOKENS = 4000
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TOTAL_TOLERANCE = 0.01

CATEGORIES = ["software_subscription", "hardware", "consulting", "logistics", "unclear", "other"]

NORMALISATION_RULES = (
    "Rules: dates as YYYY-MM-DD; amounts as plain numbers (no currency symbols or commas); "
    "if a value is not stated in the document return null, never guess or calculate it; "
    "use purchase_category 'unclear' when the document gives no category signal, and 'other' "
    "(plus other_category_detail) when it clearly fits none of the listed categories."
)

# ==============================================================================
# 1. Extraction tool schema
# ==============================================================================

EXTRACTION_TOOL: Dict[str, Any] = {
    "name": TOOL_NAME,
    "description": "Extracts structured invoice records from unstructured text.",
    "input_schema": {
        "type": "object",
        "properties": {
            "invoice_number": {
                "type": ["string", "null"],
                "description": "Invoice identifier, or null if the document has none.",
            },
            "vendor_name": {
                "type": ["string", "null"],
                "description": "Vendor legal name, or null if not stated.",
            },
            "issue_date": {
                "type": ["string", "null"],
                "description": "Invoice date as YYYY-MM-DD, or null if not stated.",
            },
            "due_date": {
                "type": ["string", "null"],
                "description": "Due date as YYYY-MM-DD, or null if not stated in the source.",
            },
            "purchase_category": {
                "type": "string",
                "enum": CATEGORIES,
                "description": "Primary expense category. Use 'unclear' if you cannot tell.",
            },
            "other_category_detail": {
                "type": ["string", "null"],
                "description": "Required text when purchase_category is 'other', else null.",
            },
            "line_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "quantity": {"type": "number"},
                        "unit_price": {"type": "number"},
                        "total": {"type": "number"},
                    },
                    "required": ["description", "quantity", "unit_price", "total"],
                },
            },
            "stated_total": {
                "type": ["number", "null"],
                "description": "Grand total printed on the invoice, or null if not printed.",
            },
            "calculated_total": {
                "type": ["number", "null"],
                "description": "Sum of line_items totals as you computed it.",
            },
            "conflict_detected": {
                "type": "boolean",
                "description": "True when calculated_total and stated_total disagree.",
            },
        },
        # Only fields that always exist stay required; the rest may be absent in the source.
        "required": ["purchase_category", "line_items"],
    },
}


# ==============================================================================
# 2. Request builder (tool_choice vs extended thinking)
# ==============================================================================


def build_tool_choice(mode: str, tool_name: Optional[str] = None) -> Dict[str, str]:
    """Return a tool_choice value: auto, any, or a forced named tool."""
    if mode == "tool":
        if not tool_name:
            raise ValueError("A forced tool_choice needs a tool name.")
        return {"type": "tool", "name": tool_name}
    if mode in ("auto", "any", "none"):
        return {"type": mode}
    raise ValueError(f"Unknown tool_choice mode: {mode}")


def build_extraction_request(
    document_text: str,
    tool_choice_mode: str = "tool",
    thinking_budget: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build messages.create kwargs. Rejects the combination the API rejects (HTTP 400):
    thinking together with tool_choice any or a forced tool. temperature is never set.
    """
    if thinking_budget is not None and tool_choice_mode in ("any", "tool"):
        raise ValueError("Extended thinking allows only tool_choice auto/none; drop thinking.")
    prompt = f"Extract the invoice into the tool.\n\n<document>\n{document_text}\n</document>"
    kwargs: Dict[str, Any] = {
        "model": EXTRACTION_MODEL,
        "max_tokens": MAX_TOKENS,
        "system": NORMALISATION_RULES,
        "tools": [EXTRACTION_TOOL],
        "tool_choice": build_tool_choice(tool_choice_mode, TOOL_NAME),
        "messages": [{"role": "user", "content": prompt}],
    }
    if thinking_budget is not None:
        if not 1024 <= thinking_budget < MAX_TOKENS:
            raise ValueError("budget_tokens must be >= 1024 and < max_tokens.")
        kwargs["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
    return kwargs


# ==============================================================================
# 3. Validation: format/semantic errors vs fields absent from the source
# ==============================================================================


@dataclass
class ValidationResult:
    errors: List[str] = field(default_factory=list)  # retryable: send back as feedback
    absent_fields: List[str] = field(default_factory=list)  # null by design: do NOT retry
    calculated_total: Optional[float] = None
    conflict_detected: bool = False

    @property
    def is_valid(self) -> bool:
        return not self.errors


def reconcile_totals(data: Dict[str, Any]) -> Tuple[Optional[float], bool]:
    """Recompute calculated_total in code and flag a conflict with stated_total."""
    items = data.get("line_items") or []
    calculated = round(sum(float(item.get("total", 0.0)) for item in items), 2)
    stated = data.get("stated_total")
    conflict = stated is not None and abs(calculated - float(stated)) > TOTAL_TOLERANCE
    return calculated, conflict


def validate_extraction_detailed(data: Dict[str, Any]) -> ValidationResult:
    """Check meaning beyond JSON syntax. Null fields are reported as absent, not as errors."""
    result = ValidationResult()

    for name in ("invoice_number", "vendor_name", "issue_date", "due_date", "stated_total"):
        if data.get(name) is None:
            result.absent_fields.append(name)

    for name in ("issue_date", "due_date"):
        value = data.get(name)
        if value is not None and not DATE_PATTERN.match(str(value)):
            result.errors.append(f"'{name}' is '{value}'; expected format YYYY-MM-DD.")

    if data.get("purchase_category") not in CATEGORIES:
        result.errors.append(f"'purchase_category' must be one of {CATEGORIES}.")
    if data.get("purchase_category") == "other" and not data.get("other_category_detail"):
        result.errors.append(
            "When 'purchase_category' is 'other', 'other_category_detail' must be provided."
        )

    if not data.get("line_items"):
        result.errors.append("At least one line item is required.")
    else:
        calculated, conflict = reconcile_totals(data)
        result.calculated_total = calculated
        result.conflict_detected = conflict
        if conflict:
            result.errors.append(
                f"Line items total ({calculated:.2f}) does not match "
                f"stated invoice total ({float(data['stated_total']):.2f})."
            )
    return result


def validate_extraction(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Backward-compatible wrapper: (is_valid, retryable_errors)."""
    result = validate_extraction_detailed(data)
    return result.is_valid, result.errors


# ==============================================================================
# 4. Extraction loop (handles every stop_reason explicitly)
# ==============================================================================


def _first_tool_use(content: Any) -> Optional[Any]:
    for block in content:
        if getattr(block, "type", "") == "tool_use" and block.name == TOOL_NAME:
            return block
    return None


def extract_with_validation_retry(
    document_text: str,
    client: Any,
    trail: ResponseTrail,
    max_retries: int = 2,
) -> Optional[Dict[str, Any]]:
    """Forced-tool extraction with retry-with-error-feedback. Returns None on failure."""
    session_id = str(uuid.uuid4())
    trail.session_start(session_id, f"Extract invoice: {document_text[:50]}...", EXTRACTION_MODEL)
    request = build_extraction_request(document_text)
    messages: List[Dict[str, Any]] = list(request["messages"])
    attempt = 0
    pauses = 0

    while attempt <= max_retries:
        attempt += 1
        trail.api_request(session_id, attempt, messages)
        response = client.messages.create(**{**request, "messages": list(messages)})
        stop = response.stop_reason

        if stop == "pause_turn" and pauses < 3:
            pauses += 1
            attempt -= 1
            messages.append({"role": "assistant", "content": response.content})
            continue
        if stop != "tool_use":
            break  # end_turn (no tool call), max_tokens, refusal: same input will not fix it

        block = _first_tool_use(response.content)
        if block is None:
            break
        data: Dict[str, Any] = dict(block.input)
        trail.tool_call(session_id, attempt, TOOL_NAME, block.id, data)
        result = validate_extraction_detailed(data)

        if result.is_valid:
            data["calculated_total"] = result.calculated_total
            data["conflict_detected"] = result.conflict_detected
            trail.tool_result(session_id, attempt, TOOL_NAME, block.id, {"status": "valid"})
            trail.session_end(session_id, json.dumps(data), "valid_extraction")
            return data

        trail.tool_result(
            session_id, attempt, TOOL_NAME, block.id, {"status": "invalid", "errors": result.errors}
        )
        messages.append({"role": "assistant", "content": response.content})
        feedback = {
            "validation_errors": result.errors,
            "instruction": "Re-read the original document and fix only these errors. "
            "Keep null for values the document does not state.",
        }
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "is_error": True,
                        "content": json.dumps(feedback),
                    }
                ],
            }
        )

    trail.session_end(session_id, "", "validation_retries_exhausted")
    return None


def main() -> None:
    import anthropic  # imported lazily so the module stays importable offline
    from dotenv import load_dotenv

    load_dotenv()
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not set. Manual live run only; see the module docstring.")
        return

    client = anthropic.Anthropic(api_key=api_key)
    trail = ResponseTrail(path=get_agent_trail_path(__file__))
    sample_doc = (
        "ACME Cloud Solutions Inc.\nINVOICE #: INV-2026-8841\nDate: 2026-10-06\n"
        "1. Cloud Hosting Cluster - Qty 2 @ $120.00 = $240.00\n"
        "2. Premium Support - Qty 1 @ $60.00 = $60.00\nTotal Due: $300.00"
    )
    print(json.dumps(extract_with_validation_retry(sample_doc, client, trail), indent=2))


if __name__ == "__main__":
    main()
