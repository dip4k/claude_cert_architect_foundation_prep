# Task Statement 1.1: Design and Implement Agentic Loops

## 🎯 Exam Objective
Understand how to build autonomous agentic loops using the Claude API, inspect `response.stop_reason` deterministically, maintain conversational history with tool results, and avoid completion anti-patterns.

---

## 🏗️ Architecture: The Deterministic Loop Lifecycle

```mermaid
flowchart TD
    Start["User Prompt Injected"] --> SendRequest["Call Claude Messages API<br>(model: claude-sonnet-4-5)"]
    SendRequest --> CheckStop{"Inspect stop_reason"}
    
    CheckStop -- "tool_use" --> AppendAssistant["1. Append Assistant Turn<br>(Include thinking & tool_use blocks)"]
    AppendAssistant --> ExecLocal["2. Execute Requested Tools Locally"]
    ExecLocal --> AppendUser["3. Append User Turn<br>(type: tool_result blocks)"]
    AppendUser --> SendRequest
    
    CheckStop -- "end_turn" --> Terminate["4. Task Complete<br>Extract & Return Final Text"]
    CheckStop -- "max_tokens / error" --> HandleException["Safety Exception Handler"]
```

---

## ⚠️ Critical Exam Distinctions & Anti-Patterns

| Event / Strategy | Implementation | Exam Trap to Reject |
|---|---|---|
| **Loop Termination Signal** | `response.stop_reason == "end_turn"` | **TRAP**: Parsing text for words like `"Done"`, `"Completed"`, or using regex. |
| **Tool Execution Round-Trip** | Append assistant `tool_use` message, then append user `tool_result` message. | **TRAP**: Appending only the tool result without the assistant's preceding `tool_use` turn. |
| **Thinking Block Continuity** | Echo assistant `thinking` blocks back **unmodified with signatures** in subsequent turns. | **TRAP**: Stripping thinking blocks to save tokens (Anthropic API rejects with `400 Bad Request`). |
| **Safety Limits** | `MAX_ITERATIONS = 15` as an emergency runaway brake. | **TRAP**: Relying on turn count or iteration caps as normal termination logic. |

---

## 💡 Architectural Decision Matrix

| Question | Recommended Choice | Rationale |
|---|---|---|
| When should the agent stop calling tools? | Only when `stop_reason == "end_turn"`. | The model alone decides when it has accumulated sufficient evidence to answer. |
| How to handle sampling when thinking is on? | Omit `temperature` completely. | Custom temperature parameters trigger an HTTP `400 Bad Request` API error. |
| Which model to use for the orchestrator loop? | `claude-sonnet-4-5` | Best balance of deep multi-step reasoning, tool choice accuracy, and low latency. |

---

## 🛠️ Production Code Reference
- Interactive Workbook: [`ts_1_1_multi_tool_agent_loop.ipynb`](ts_1_1_multi_tool_agent_loop.ipynb)
- Runnable Script: [`main.py`](main.py)
- Offline Verification: Run via `uv run pytest tests/test_domain1_full.py` in WSL.
