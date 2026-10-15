"""
Domain 4: Prompt Engineering & Structured Output
Task Statement 4.1: Design prompts with explicit criteria to reduce false positives
Task Statement 4.5: Design efficient batch processing strategies (Message Batches API)
Exam Scenario 5 & 6: Continuous Integration & Structured Data Extraction

Key Exam Concepts Demonstrated:
1. Explicit categorical criteria vs vague directives: Defining unambiguous severity boundaries
   to avoid high false-positive rates that erode developer trust.
2. Message Batches API:
   - 50% discount on token pricing with up to 24-hour turnaround window.
   - Non-blocking vs blocking workflows (inappropriate for pre-merge CI; ideal for overnight jobs).
   - custom_id tracking for correlating requests and selectively retrying failed items.
"""

import json
import os
import sys
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent if "__file__" in locals() else None

# ==============================================================================
# 1. Message Batches Simulator (TS 4.5)
# ==============================================================================

@dataclass
class BatchRequest:
    custom_id: str
    params: Dict[str, Any]


@dataclass
class BatchResponse:
    custom_id: str
    status: str  # "succeeded" | "failed"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class MessageBatchesEngine:
    """Simulates the Anthropic Message Batches API lifecycle and partial failure recovery."""

    def __init__(self) -> None:
        self.batch_store: Dict[str, List[BatchResponse]] = {}

    def submit_batch(self, requests: List[BatchRequest]) -> str:
        batch_id = f"msgbatch_{uuid.uuid4().hex[:10]}"
        results = []
        for req in requests:
            # Simulate failure on oversized documents
            if req.params.get("token_estimate", 0) > 100_000:
                results.append(BatchResponse(
                    custom_id=req.custom_id,
                    status="failed",
                    error="ContextWindowExceeded: document exceeds maximum batch item length.",
                ))
            else:
                results.append(BatchResponse(
                    custom_id=req.custom_id,
                    status="succeeded",
                    result={"summary": f"Processed successfully for {req.custom_id}"},
                ))
        self.batch_store[batch_id] = results
        return batch_id

    def get_batch_results(self, batch_id: str) -> List[BatchResponse]:
        return self.batch_store.get(batch_id, [])

    def filter_failed_for_resubmission(self, batch_id: str) -> List[str]:
        """Identifies failed custom_ids to resubmit after chunking."""
        results = self.get_batch_results(batch_id)
        return [r.custom_id for r in results if r.status == "failed"]


def main() -> None:
    engine = MessageBatchesEngine()
    requests = [
        BatchRequest(custom_id="req_doc_01", params={"token_estimate": 1200}),
        BatchRequest(custom_id="req_doc_02", params={"token_estimate": 150_000}),  # Will fail
        BatchRequest(custom_id="req_doc_03", params={"token_estimate": 3500}),
    ]
    batch_id = engine.submit_batch(requests)
    print(f"Batch Submitted: {batch_id}")

    failed_ids = engine.filter_failed_for_resubmission(batch_id)
    print(f"Items Requiring Resubmission (Selective Retry by custom_id): {failed_ids}")


if __name__ == "__main__":
    main()
