---
name: claude-offline-tester
description: Guidance on writing and running zero-cost offline unit tests with mock Claude clients in WSL Ubuntu.
---

# Claude Offline Tester Guide

## Policy Compliance
- **Zero API Tokens**: Automated test runs MUST NOT call the Anthropic API.
- **Environment**: All commands run in WSL Ubuntu using `uv`.

## Mocking Anthropic Responses
Import the mock utilities from `lib.mock_claude`:
```python
from lib.mock_claude import (
    MockClaudeClient,
    AsyncMockClaudeClient,
    MockMessageResponse,
    MockContentBlock,
)
```

### Simulating Tool Calling Turn Followed by Final Text Turn
```python
resp_tool_turn = MockMessageResponse(
    content=[
        MockContentBlock(
            block_type="tool_use",
            name="get_customer",
            tool_id="call_001",
            input_data={"customer_id": "cust_123"},
        )
    ],
    stop_reason="tool_use",
)

resp_final_turn = MockMessageResponse(
    content=[
        MockContentBlock(
            block_type="text",
            text="Customer cust_123 has been verified.",
        )
    ],
    stop_reason="end_turn",
)

client = AsyncMockClaudeClient([resp_tool_turn, resp_final_turn])
```

## Running Tests in WSL Ubuntu
```bash
# From repository root:
uv run pytest tests/ -v
```
