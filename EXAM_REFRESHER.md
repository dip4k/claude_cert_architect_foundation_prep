# Claude Certified Architect – Foundations Exam Refresher Cheat Sheet

**Exam Format**: 60 Multiple-Choice Questions | **Time**: 120 Minutes | **Passing Scaled Score**: 720 / 1000  
**Scenarios**: 4 scenarios chosen from 6 official customer cases.

---

## ⚡ The 10 Golden Architectural Rules

| # | Topic | The Golden Rule | Anti-Pattern to Reject |
|---|---|---|---|
| **1** | **Loop Control** | `response.stop_reason == "end_turn"` is the **sole deterministic signal** for completion. | Parsing assistant text (e.g. `"I am done"`) or using turn caps as primary exit. |
| **2** | **Compliance Gates** | Critical rules (identity verification, finance) require **programmatic prerequisite gates or SDK hooks**. | System prompt instructions alone have a non-zero failure rate under ambiguity. |
| **3** | **Multi-Agent** | Subagents have **100% isolated context**. Pass findings explicitly in the prompt; no shared memory. | Assuming subagents inherit parent conversation history or memory. |
| **4** | **Subagent Spawning**| Emit **multiple `Task` calls in a single coordinator response** for concurrent parallel execution. | Sequential round-trips over separate turns (adds 40%+ latency). |
| **5** | **Tool Routing** | Refine **tool descriptions with input formats, edge cases, and boundary statements**. | Minimal 1-line descriptions cause 50% misrouting; routing classifiers are over-engineered. |
| **6** | **MCP Errors** | Return structured metadata: `isError: true`, `errorCategory`, and `isRetryable: bool`. | Throwing raw exceptions or returning generic `"Operation failed"` strings. |
| **7** | **Empty vs. Error** | A successful query returning 0 records is a **valid empty result** (`isError: false`, `count: 0`). | Flagging zero records as `isError: true` triggers wasteful retries. |
| **8** | **Headless CI** | Automated pipelines **must pass the `-p` (or `--print`) flag** to prevent terminal stdin hangs. | Running `claude "prompt"` without `-p` hangs CI/CD runners indefinitely. |
| **9** | **Structured JSON** | Guaranteed valid schema compliance is achieved via **`tool_use`** with JSON schemas. | Generating markdown text and parsing with regex/json.loads causes syntax errors. |
| **10**| **Batches API** | Message Batches API gives **50% cost savings for 24h non-blocking jobs** (overnight audits). | Never use Batches API for blocking pre-merge CI checks (up to 24h latency). |

---

## 🎯 Domain-by-Domain Pre-Exam Decision Matrix

### 🔷 Domain 1: Agentic Architecture & Orchestration (27%)
* **Loop Termination**: Continue when `stop_reason == "tool_use"`; terminate when `stop_reason == "end_turn"`.
* **Subagent Invocation**: Coordinator must have `"Task"` in `allowedTools`.
* **Large PR Reviews**: Use **prompt chaining** (Pass 1: per-file local checks; Pass 2: cross-file integration) to prevent **attention dilution**.
* **Stale Code Resumption**: If source code was edited, discard raw conversation history and start a **fresh session with an injected structured summary**.

### 🔷 Domain 2: Tool Design & MCP Integration (18%)
* **Tool Assignment**: Restrict agents to **4–5 tools** (principle of least privilege) rather than over-provisioning 15+ tools.
* **`tool_choice` Modes**: Use `"auto"` for conversational exploration; `"any"` to guarantee any tool execution; `{"type": "tool", "name": "..."}` for mandatory step 1.
* **MCP Scoping**: Project-level in `.mcp.json` with `${ENV_VAR}` expansion; user-level in `~/.claude.json`.
* **Resources vs. Tools**: Expose read-only catalogs (database schemas, API indexes) as **MCP Resources**.
* **Edit Fallback**: When `Edit` fails due to non-unique anchor text, fallback is **`Read` followed by `Write`**.

### 🔷 Domain 3: Claude Code Configuration & Workflows (20%)
* **Scoping Resolution**: User (`~/.claude/CLAUDE.md`) -> Project (`.claude/CLAUDE.md`) -> Subdirectory -> Path-scoped rules.
* **Skills with `context: fork`**: Use `context: fork` whenever an agent skill generates verbose discovery logs to protect main conversation context.
* **Path-Scoped Rules**: Use `.claude/rules/*.md` with YAML glob paths (`paths: ["**/*.test.*"]`) for conventions that span multiple directories.
* **Plan Mode vs. Direct**: Use **Plan Mode** for microservice extraction, architectural shifts, and multi-file migrations (40+ files); use **Direct Execution** for single-file, well-scoped fixes.
* **Self-Review Bias**: Never use the generating Claude session to review its own code; use an independent review instance.

### 🔷 Domain 4: Prompt Engineering & Structured Output (20%)
* **False Positives**: Concrete categorical criteria with code examples outperform vague instructions (*"be conservative"*).
* **Missing Data / Hallucinations**: Set missing-prone fields as **nullable** (`type: ["string", "null"]`) so Claude returns `null` instead of fabricating values.
* **Extensible Categories**: Use enum + `"other"` with a companion string (`other_description`).
* **Validation-Retry Limits**: Retries fix format and structural errors; **retries fail when data is fundamentally absent** from source documents.
* **Batches Failure Handling**: Use `custom_id` to correlate responses and resubmit only failed items.

### 🔷 Domain 5: Context Management & Reliability (15%)
* **Persistent Case Facts Layer**: Extract dates, amounts, and order IDs into an immutable "Case Facts" block outside summarized history to prevent fact degradation.
* **Tool Trimming**: Strip 40+ raw database/carrier fields down to the 4 essential fields before adding to context.
* **Immediate Escalation**: If a customer explicitly demands a human representative, **escalate immediately** without further questions.
* **Ambiguity Resolution**: When lookups return multiple hits, **ask for clarifying identifiers**, never guess heuristically.
* **Conflicting Statistics**: Never pick one number arbitrarily; report both values with source citations and collection timestamps.
* **Stratified Sampling**: High aggregate accuracy (97%) can mask a 40% error rate on rare forms; validate accuracy segment by segment.
