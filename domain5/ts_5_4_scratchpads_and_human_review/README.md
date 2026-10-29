# Task Statement 5.4: Codebase Exploration Scratchpads & State Manifests

## 📌 Executive Overview: Goal, Scope & Exam Importance

### Domain & Exam Weight
- **Domain**: Domain 5 — Context Management & Reliability (18% of exam weighting)
- **Scenario Alignment**: Scenario 4 (Incident Remediation & Root Cause Analysis) & Scenario 6 (Automated Refactoring & Cross-Module Review)
- **Core Goal**: Architect context isolation and persistent state tracking during large codebase exploration: maintaining external scratchpads (`scratchpad.md`) to counteract context degradation, structuring state manifests for crash recovery, and delegating verbose grep/AST investigations to ephemeral subagents.

### Why This Matters in Production
When an autonomous coding or debugging agent investigates an enterprise repository spanning hundreds of thousands of lines of code:
1. **Context Window Exhaustion**: Running recursive file listings, greps, and AST dumps directly within the primary agent loop quickly burns through 100,000+ tokens of context, pushing the original task description and constraints out of the model's active attention.
2. **Context Degradation & Amnesia**: As context grows, Claude suffers from instruction decay—forgetting edge-case constraints specified in Turn 1, repeating searches it already ran, or abandoning its initial investigation hypothesis.
3. **Fragility & Process Interruption**: If the execution crashes or reaches rate limits after 20 tool calls, all in-memory discoveries are lost, forcing the developer to restart from zero.

Production architectures solve this using **External Scratchpads & Subagent Exploration Isolation**:
- **Persistent Scratchpad (`scratchpad.md`)**: A versioned markdown file stored on disk that checkpoints verified findings, hypotheses, and remaining tasks across context boundaries.
- **Explore Subagent Pattern**: Delegating deep, noisy codebase exploration (grepping 50 files) to an ephemeral, read-only subagent. The subagent processes thousands of lines of raw code and returns only a compact 10-line synthesis to the coordinator.
- **State Checkpointing**: Storing progress manifests for deterministic crash recovery.

---

## 📖 Deep Narrative: Why We Do What We Do

### The Naive Production Failure: In-Context Bloat & Investigation Amnesia
Consider an incident remediation agent tasked with investigating an intermittent database connection pool starvation bug across a microservices repository.
In a naive implementation:
- The coordinator agent executes `Bash(command="grep -rn 'pool_timeout' .")` returning 450 lines of search results.
- It then executes `ReadMultipleFiles(paths=[...])` reading 12 database connection files (65,000 tokens).
- It executes `Bash(command="git log -n 50 -p")` adding another 40,000 tokens of git history.

Now at 120,000 tokens:
1. **The Model Forgets the Primary Objective**: Claude begins focusing on cosmetic typing warnings in irrelevant modules read 5 turns ago.
2. **Loop Redundancy**: The agent runs the same grep command again because the original output was buried under massive file reads.
3. **Crash Vulnerability**: The connection drops or process times out. Since all findings existed only in ephemeral assistant messages, the entire investigation disappears.

### The Architectural Solution: Persistent Scratchpads & Explore Subagent Delegation
Production architectures decouple deep exploration from coordinator decision-making:

```mermaid
flowchart TD
    UserReq["Developer Objective:<br>'Investigate Connection Pool Starvation'"] --> Coordinator["Coordinator Agent<br>(Main Task Context)"]
    
    subgraph Storage["Persistent State Storage (Disk)"]
        ScratchpadFile["scratchpad.md<br>- Current Hypothesis<br>- Confirmed Findings<br>- Unexplored Paths"]
        StateManifest["manifest.json<br>- Checkpointed Stage<br>- Tool Call Counter<br>- Recovery Snapshot"]
    end
    
    Coordinator <--> Storage
    
    subgraph Delegation["Exploration Context Isolation"]
        ExploreSubagent["Ephemeral Explore Subagent<br>(Read-Only Sandbox)"]
        RawRepo["Enterprise Codebase<br>(Hundreds of Files)"]
    end
    
    Coordinator -->|"Spawns Task:<br>'Find all pool acquirers'| ExploreSubagent
    ExploreSubagent <-->|"Runs Grep, AST, Reads<br>(Burns 80,000 ephemeral tokens)"| RawRepo
    ExploreSubagent -->|"Returns Compact 8-Line Synthesis"| Coordinator
    
    Coordinator -->|"Appends Validated Finding"| ScratchpadFile
    Coordinator -->|"Updates Stage: 'Hypothesis Confirmed'"| StateManifest
    
    Coordinator --> FinalResolution["Deterministic Remediation Plan<br>(Clean Context, Zero Token Waste)"]
```

1. **Subagent Isolation Contract**: The coordinator never reads 12 raw files directly. It delegates the search to an Explore subagent with explicit instructions: *"Inspect the connection pool configurations and return ONLY a bulleted summary of timeout values and file locations."* The 80,000 tokens of raw file text exist solely in the ephemeral subagent context and are discarded upon completion.
2. **Persistent Scratchpad (`scratchpad.md`)**: The coordinator appends confirmed facts to `scratchpad.md` on disk:
   - *Confirmed*: `db_pool.py` sets max connections to 10.
   - *Confirmed*: `analytics_worker.py` does not release connections in its error handler (Line 84).
   - *Remaining*: Verify if `reporting_service.py` shares the same pool.
3. **Crash Recovery & Resume**: If the runner is terminated, the agent restarts by reading `scratchpad.md` and `manifest.json`, immediately resuming at Step 3 without repeating prior searches.

---

## 🔑 Key Technical Terminology Explained

- **Persistent Scratchpad (`scratchpad.md`)**: A structured markdown file maintained on disk throughout an agent's lifecycle that records verified facts, active hypotheses, and pending questions outside LLM context memory.
- **State Checkpointing / Crash Manifest**: A machine-readable JSON file (`manifest.json`) that records the current workflow phase, tool invocation index, and critical state variables for deterministic recovery after failure.
- **Explore Subagent Pattern**: Delegating verbose, low-signal exploratory tasks (code grepping, directory traversal, AST scanning) to a child agent whose large context is discarded after returning a concise summary to the parent.
- **Context Degradation / Instruction Decay**: The degradation in attention precision, adherence to negative constraints, and recall that occurs as conversation history approaches the model's effective context limit.
- **Context Compaction**: The intentional pruning and synthesis of historical context before crossing critical token thresholds (e.g., via `/compact` or external summarization).

---

## ⚠️ Critical Exam Distinctions & Distractor Teardown

| Codebase Exploration Pattern | Correct Implementation (Exam Standard) | Exam Trap / Distractor to Reject |
|---|---|---|
| **Managing Verbose Search Data** | **Explore Subagent Delegation**: Spawn an ephemeral subagent to run greps and file reads; return only a 10-line synthesis to parent context. | **TRAP: Direct Monolithic Ingestion**: Reading 20 full source files into the coordinator's context window, blowing the token budget and degrading reasoning. |
| **Preserving Progress Across Crashes** | **Persistent Scratchpad on Disk**: Write validated findings and hypotheses to `scratchpad.md` as files are analyzed. | **TRAP: In-Memory Message State**: Keeping investigation notes only in assistant chat messages. (Lost completely if session restarts or times out). |
| **Mitigating Instruction Decay** | Checkpoint state to disk, compact context periodically, and pin active objectives at the top of subsequent prompts. | **TRAP: Continuous History Accumulation**: Appending every command output into a single unbroken 200,000-token prompt. |
| **Codebase Exploration Scope** | Bound subagent tools to read-only capabilities (`Read`, `Grep`, `Glob`) to prevent unintended state mutations during research. | **TRAP: Full Write Permissions in Subagent**: Giving exploratory subagents write access, risking inadvertent file modifications before analysis is complete. |

---

## 💡 Architectural Decision Matrix: Rules of Thumb

| Task Magnitude | Exploration Strategy | State Persistence Mechanism | Context Boundary |
|---|---|---|---|
| **Single-File Bug (< 200 lines)** | Direct Coordinator Reading | In-context conversation history | Single session |
| **Multi-File Feature (3–10 files)** | Coordinator with Local Scratchpad | `scratchpad.md` on disk | Single session with periodic checkpoints |
| **Repository-Wide Audit (> 50 files)** | **Explore Subagent Delegation + Scratchpad** | `scratchpad.md` + `manifest.json` | Ephemeral subagent context discarded after each batch |
| **Long-Running CI/CD / Overnight Task** | Subagent Swarm with Persistent Manifests | Structured DB / File Manifests | Fully resumable sessions via `--resume` |

---

## 🧠 Claude 4.5 Extended Thinking & Parameter Standards

When configuring Claude 4.5 for codebase exploration and debugging:
- **Model Standard**: Use `claude-sonnet-4-5` for deep code reasoning and architectural tracing; use `claude-haiku-4-5` for fast grep pattern matching in explore subagents.
- **Thinking Configuration**: Allocate a thinking budget of 4,000 to 8,000 tokens for diagnosing root causes and tracing multi-file call stacks:
  ```python
  thinking = {"type": "enabled", "budget_tokens": 6000}
  ```
- **Temperature Omission**: **Do NOT provide `temperature`**, `top_p`, or `top_k`. Anthropic's Claude 4.5 API enforces default sampling parameters when thinking is active; supplying custom values results in an HTTP `400 Bad Request`.
- **Scratchpad Synchronization Tool**: Bind a tool `update_scratchpad(finding: str, status: str)` to enforce structured writes to disk after each discovery milestone.

---

## 🛠️ Hands-on Workbook Guide: Following the Code Step-by-Step

In the accompanying notebook [`ts_5_4_scratchpads_and_human_review.ipynb`](ts_5_4_scratchpads_and_human_review.ipynb), you will follow the step-by-step implementation:

- **Step 1: Scratchpad Manager Implementation**: Build the `CodebaseScratchpadManager` class for managing `scratchpad.md` persistence.
- **Step 2: Simulating Context Bloat vs Subagent Isolation**: Compare token consumption between direct file reading and explore subagent delegation.
- **Step 3: State Manifest Checkpointing**: Implement the JSON state manifest for tracking workflow stages and tool call history.
- **Step 4: Crash Recovery Simulation**: Simulate an unexpected crash and verify that the agent resumes seamlessly from the checkpoint.
- **Step 5: Automated Verification**: Execute tests verifying that scratchpad contents match the expected investigation milestones.

Verify your implementation anytime with offline unit tests in WSL Ubuntu-26.04:
```powershell
wsl -d Ubuntu-26.04 bash -c "~/.local/bin/uv run pytest tests/test_domain5_full.py"
```
