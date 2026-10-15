"""
Domain 4: Prompt Engineering & Structured Output
Task Statement 4.3: Enforce structured output using tool use and JSON schemas
Task Statement 4.4: Implement validation, retry, and feedback loops
Exam Scenario 6: Structured Data Extraction

Key Exam Concepts Demonstrated:
1. Tool use with JSON schemas as the most reliable approach for guaranteed schema-compliant
   structured output, eliminating JSON syntax errors.
2. Nullable fields in schema to prevent the model from fabricating/hallucinating values when
   information is missing from source documents.
3. Extensible taxonomy: Enum with "other" + companion detail string.
4. Forced tool selection (tool_choice: {"type": "tool", "name": "extract_invoice"}).
5. Validation-retry loop: validating extracted data and reprompting with validation errors on failure.

Manual Execution (WSL Ubuntu):
    uv run domain4/ts_4_3_structured_output_tool_use/main.py
"""

import json
import os
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv
import anthropic

from lib.sdk_parser_py import create_parser
from lib.response_logger import ResponseTrail, get_agent_trail_path

load_dotenv()


# ==============================================================================
# 1. Extraction Tool Schema (Anthropic format with nullable & extensible fields)
# ==============================================================================

EXTRACTION_TOOL = {
    "name": "extract_invoice",
    "description": "Extracts validated, structured invoice records from unstructured text.",
    "input_schema": {
        "type": "object",
        "properties": {
            "invoice_number": {
                "type": "string",
                "description": "Unique invoice identifier (e.g. INV-2026-001).",
            },
            "vendor_name": {
                "type": "string",
                "description": "Legal entity name of the vendor/supplier.",
            },
            "issue_date": {
                "type": "string",
                "description": "Invoice date formatted as YYYY-MM-DD.",
            },
            "due_date": {
                # Nullable field to prevent hallucination when omitted from document
                "type": ["string", "null"],
                "description": "Due date formatted as YYYY-MM-DD, or null if not stated in source.",
            },
            "purchase_category": {
                # Extensible enum pattern
                "type": "string",
                "enum": ["software_subscription", "hardware", "consulting", "logistics", "other"],
                "description": "Primary expense category.",
            },
            "other_category_detail": {
                # Required detail string when purchase_category is 'other'
                "type": ["string", "null"],
                "description": "Specific detail string if purchase_category is 'other', otherwise null.",
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
                "type": "number",
                "description": "Grand total stated on the invoice.",
            },
        },
        "required": [
            "invoice_number",
            "vendor_name",
            "issue_date",
            "purchase_category",
            "line_items",
            "stated_total",
        ],
    },
}


# ==============================================================================
# 2. Semantic & Schema Validation Engine
# ==============================================================================

def validate_extraction(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates semantic correctness beyond basic JSON syntax:
    - Verifies line item sum equals stated_total
    - Verifies 'other_category_detail' is provided when category is 'other'
    """
    errors: List[str] = []

    # Category consistency check
    if data.get("purchase_category") == "other" and not data.get("other_category_detail"):
        errors.append("When 'purchase_category' is 'other', 'other_category_detail' must be provided.")

    # Arithmetic consistency check
    items = data.get("line_items", [])
    if not items:
        errors.append("At least one line item is required.")
    else:
        calculated_sum = sum(item.get("total", 0.0) for item in items)
        stated = data.get("stated_total", 0.0)
        if abs(calculated_sum - stated) > 0.01:
            errors.append(
                f"Line items total ({calculated_sum:.2f}) does not match stated invoice total ({stated:.2f})."
            )

    return len(errors) == 0, errors


# ==============================================================================
# 3. Extraction with Validation-Retry Loop
# ==============================================================================

def extract_with_validation_retry(
    document_text: str,
    client: Any,
    trail: ResponseTrail,
    max_retries: int = 2,
) -> Optional[Dict[str, Any]]:
    session_id = str(uuid.uuid4())
    trail.session_start(session_id, f"Extract invoice: {document_text[:50]}...", "claude-haiku-4-5")

    messages: List[Dict[str, Any]] = [
        {
            "role": "user",
            "content": f"Extract all invoice data from the following document into the structured tool:\n\n{document_text}",
        }
    ]

    for attempt in range(1, max_retries + 2):
        trail.api_request(session_id, attempt, messages)

        # Forced tool choice guarantees tool execution
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1500,
            tools=[EXTRACTION_TOOL],
            tool_choice={"type": "tool", "name": "extract_invoice"},
            messages=messages,
        )

        extracted_data: Optional[Dict[str, Any]] = None
        tool_call_id: Optional[str] = None

        for block in response.content:
            if getattr(block, "type", "") == "tool_use" and block.name == "extract_invoice":
                extracted_data = block.input
                tool_call_id = block.id
                break

        if not extracted_data:
            break

        trail.tool_call(session_id, attempt, "extract_invoice", tool_call_id or "", extracted_data)

        # Validate semantic correctness
        is_valid, validation_errors = validate_extraction(extracted_data)

        if is_valid:
            trail.tool_result(session_id, attempt, "extract_invoice", tool_call_id or "", {"status": "valid"})
            trail.session_end(session_id, json.dumps(extracted_data), "valid_extraction")
            return extracted_data

        # Failed semantic validation: Retry-with-error-feedback (TS 4.4)
        trail.tool_result(
            session_id,
            attempt,
            "extract_invoice",
            tool_call_id or "",
            {"status": "validation_failed", "errors": validation_errors},
        )

        # Add assistant message and feedback for the model to self-correct
        messages.append({"role": "assistant", "content": response.content})
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_call_id,
                    "content": json.dumps({
                        "validation_error": "Semantic validation failed",
                        "issues": validation_errors,
                        "instruction": "Please correct the extraction to resolve these specific validation issues.",
                    }),
                }
            ],
        })

    trail.session_end(session_id, "", "validation_retries_exhausted")
    return None


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment or .env. Please set it to run manually.")
        return

    client = anthropic.Anthropic(api_key=api_key)
    trail_path = get_agent_trail_path(__file__)
    trail = ResponseTrail(path=trail_path)

    sample_doc = """
    ACME Cloud Solutions Inc.
    INVOICE #: INV-2026-8841
    Date: October 6, 2026
    
    Items:
    1. Cloud Hosting Container Cluster - Qty: 2 @ $120.00 each = $240.00
    2. Premium Support Tier - Qty: 1 @ $60.00 = $60.00
    
    Total Due: $300.00
    (Payment terms: Due upon receipt)
    """

    print("Running Guaranteed Structured Output Extraction Exercise...")
    result = extract_with_validation_retry(sample_doc, client, trail)
    print("\nValidated Extraction Result:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
