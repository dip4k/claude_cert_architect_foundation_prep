"""
Domain 4: Prompt Engineering & Structured Output
Task Statement 4.5: Design efficient batch processing strategies (Message Batches API)
Exam Scenarios 5 (CI) and 6 (structured extraction)

Intent: an OFFLINE simulator that mirrors the shapes of the real Message Batches API without
importing `anthropic` or making any call:
- request list of {custom_id, params}
- batch object with processing_status and request_counts
- one result per custom_id, result.type in succeeded / errored / canceled / expired
Key facts: 50% cost saving, up to 24 hours (no latency SLA), correlate with custom_id, and no
multi-turn tool calling inside one batch request (the batch cannot run your tools mid-request).

Also here: SLA maths (submission frequency), chunk-and-resubmit of failed items, and a
sample-first helper. Real calls look like client.messages.batches.create(requests=[...]); run
them manually, never from automated runs.
"""

import math
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

EXTRACTION_MODEL = "claude-haiku-4-5"  # workers / extraction
REPORT_MODEL = "claude-sonnet-4-5"  # reasoning / reports
BATCH_DISCOUNT = 0.5
BATCH_WINDOW_HOURS = 24
MAX_DOC_TOKENS = 100_000  # simulator limit used to create "oversized document" failures
CUSTOM_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
SIM_ONLY_KEYS = ("token_estimate", "simulate")  # simulator hints, stripped from API payloads
FAILED_TYPES = ("errored", "expired")


@dataclass
class BatchRequest:
    custom_id: str
    params: Dict[str, Any]

    def __post_init__(self) -> None:
        if not CUSTOM_ID_PATTERN.match(self.custom_id):
            raise ValueError(f"custom_id must match {CUSTOM_ID_PATTERN.pattern}: {self.custom_id}")

    def to_api_dict(self) -> Dict[str, Any]:
        """The {custom_id, params} item the real API expects (simulator hints removed)."""
        params = {k: v for k, v in self.params.items() if k not in SIM_ONLY_KEYS}
        return {"custom_id": self.custom_id, "params": params}


@dataclass
class BatchResult:
    custom_id: str
    result: Dict[str, Any]  # {"type": "succeeded", "message": {...}} or {"type": "errored", ...}

    @property
    def type(self) -> str:
        return str(self.result["type"])


@dataclass
class _StoredBatch:
    batch: Dict[str, Any]
    requests: List[BatchRequest]
    results: List[BatchResult] = field(default_factory=list)


class MessageBatchesEngine:
    """Offline stand-in for client.messages.batches (create / retrieve / results)."""

    def __init__(self) -> None:
        self._store: Dict[str, _StoredBatch] = {}

    # -- API-shaped methods -------------------------------------------------
    def create_batch(
        self, requests: List[BatchRequest], auto_complete: bool = False
    ) -> Dict[str, Any]:
        ids = [r.custom_id for r in requests]
        if len(set(ids)) != len(ids):
            raise ValueError("custom_id values must be unique within a batch.")
        batch = {
            "id": f"msgbatch_{uuid.uuid4().hex[:10]}",
            "type": "message_batch",
            "processing_status": "in_progress",
            "request_counts": {
                "processing": len(requests),
                "succeeded": 0,
                "errored": 0,
                "canceled": 0,
                "expired": 0,
            },
        }
        self._store[batch["id"]] = _StoredBatch(batch=batch, requests=list(requests))
        if auto_complete:
            self.complete(batch["id"])
        return batch

    def retrieve(self, batch_id: str) -> Dict[str, Any]:
        return self._store[batch_id].batch

    def results(self, batch_id: str) -> List[BatchResult]:
        stored = self._store[batch_id]
        if stored.batch["processing_status"] != "ended":
            raise RuntimeError("Results are available only after processing_status == 'ended'.")
        return stored.results

    # -- simulator controls -------------------------------------------------
    def complete(self, batch_id: str) -> None:
        """Simulate the batch finishing (anywhere from minutes up to the 24 hour window)."""
        stored = self._store[batch_id]
        stored.results = [self._process(req) for req in stored.requests]
        counts = {"processing": 0, "succeeded": 0, "errored": 0, "canceled": 0, "expired": 0}
        for res in stored.results:
            counts[res.type] += 1
        stored.batch["request_counts"] = counts
        stored.batch["processing_status"] = "ended"

    @staticmethod
    def _process(req: BatchRequest) -> BatchResult:
        sim = req.params.get("simulate")
        if sim in ("expired", "canceled"):
            return BatchResult(req.custom_id, {"type": sim})
        if req.params.get("token_estimate", 0) > MAX_DOC_TOKENS:
            return BatchResult(
                req.custom_id,
                {
                    "type": "errored",
                    "error": {
                        "type": "invalid_request_error",
                        "message": "Document exceeds the maximum request length.",
                    },
                },
            )
        if req.params.get("tools"):
            # The model asks for a tool; nothing in the batch executes it or continues the turn.
            tool_name = req.params["tools"][0]["name"]
            content: List[Dict[str, Any]] = [
                {"type": "tool_use", "id": "toolu_sim", "name": tool_name, "input": {}}
            ]
            stop = "tool_use"
        else:
            content = [{"type": "text", "text": f"Processed {req.custom_id}"}]
            stop = "end_turn"
        message = {"role": "assistant", "content": content, "stop_reason": stop}
        return BatchResult(req.custom_id, {"type": "succeeded", "message": message})

    # -- convenience kept for earlier exercises -----------------------------
    def submit_batch(self, requests: List[BatchRequest]) -> str:
        return str(self.create_batch(requests, auto_complete=True)["id"])

    def get_batch_results(self, batch_id: str) -> List[BatchResult]:
        return self.results(batch_id)

    def filter_failed_for_resubmission(self, batch_id: str) -> List[str]:
        """custom_ids that errored or expired; succeeded items are never resubmitted."""
        return [r.custom_id for r in self.results(batch_id) if r.type in FAILED_TYPES]


# ==============================================================================
# Helpers: tools, SLA, chunking, sample-first, workload fit
# ==============================================================================


def requests_needing_followup(results: List[BatchResult]) -> List[str]:
    """Succeeded items that stopped at tool_use. Run the tool yourself and send a NEW request."""
    return [
        r.custom_id
        for r in results
        if r.type == "succeeded" and r.result["message"]["stop_reason"] == "tool_use"
    ]


def worst_case_turnaround_hours(
    submit_interval_hours: float, window_hours: float = BATCH_WINDOW_HOURS, margin_hours: float = 0
) -> float:
    """A document can wait one full interval for the next submission, then the whole window."""
    return submit_interval_hours + window_hours + margin_hours


def max_submit_interval_hours(
    sla_hours: float, window_hours: float = BATCH_WINDOW_HOURS, margin_hours: float = 0
) -> float:
    """Longest gap between submissions that still meets the SLA. Example: 30 - 24 - 2 = 4."""
    interval = sla_hours - window_hours - margin_hours
    if interval <= 0:
        raise ValueError("SLA is too tight for batch processing: use the synchronous API.")
    return interval


def submissions_per_day(interval_hours: float) -> int:
    return math.ceil(24 / interval_hours)


def chunk_failed_requests(
    requests: List[BatchRequest], failed_ids: List[str], max_chunk_tokens: int = 50_000
) -> List[BatchRequest]:
    """Build the retry batch: only failed ids, oversized documents split into chunks."""
    by_id = {r.custom_id: r for r in requests}
    retry: List[BatchRequest] = []
    for cid in failed_ids:
        original = by_id[cid]
        base = {k: v for k, v in original.params.items() if k != "simulate"}
        tokens = int(base.get("token_estimate", 0))
        parts = max(1, math.ceil(tokens / max_chunk_tokens))
        if parts == 1:
            retry.append(BatchRequest(cid, base))
            continue
        for i in range(1, parts + 1):
            params = dict(base)
            params["token_estimate"] = math.ceil(tokens / parts)
            retry.append(BatchRequest(f"{cid}-chunk{i}of{parts}", params))
    return retry


def original_id(custom_id: str) -> str:
    """Map a chunk custom_id back to the source document id."""
    return custom_id.split("-chunk")[0]


def select_sample(requests: List[BatchRequest], sample_size: int) -> List[BatchRequest]:
    """Evenly spaced sample to refine the prompt before paying for the full batch."""
    if sample_size >= len(requests):
        return list(requests)
    step = len(requests) / sample_size
    return [requests[int(i * step)] for i in range(sample_size)]


def success_rate(results: List[BatchResult]) -> float:
    return sum(r.type == "succeeded" for r in results) / len(results) if results else 0.0


def is_batch_appropriate(blocking: bool, max_wait_hours: float) -> bool:
    """Batch only latency-tolerant work: nothing is waiting on the result, and >= 24h is fine."""
    return not blocking and max_wait_hours >= BATCH_WINDOW_HOURS


def batch_cost(standard_cost: float) -> float:
    return standard_cost * (1 - BATCH_DISCOUNT)


def main() -> None:
    engine = MessageBatchesEngine()
    requests = [
        BatchRequest("req_doc_01", {"model": EXTRACTION_MODEL, "token_estimate": 1200}),
        BatchRequest("req_doc_02", {"model": EXTRACTION_MODEL, "token_estimate": 150_000}),
        BatchRequest("req_doc_03", {"model": EXTRACTION_MODEL, "token_estimate": 3500}),
    ]
    batch = engine.create_batch(requests)
    print("Status:", batch["processing_status"], batch["request_counts"])
    engine.complete(batch["id"])
    print("Status:", engine.retrieve(batch["id"])["processing_status"])

    failed = engine.filter_failed_for_resubmission(batch["id"])
    retry = chunk_failed_requests(requests, failed)
    print("Resubmit only:", [r.custom_id for r in retry])
    print("Max submit interval for a 30h SLA (2h margin):", max_submit_interval_hours(30, 24, 2))


if __name__ == "__main__":
    main()
