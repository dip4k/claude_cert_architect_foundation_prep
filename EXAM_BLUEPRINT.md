# Claude Certified Architect – Foundations Exam Blueprint

**Credential**: Claude Certified Architect – Foundations  
**Passing Score**: 720 / 1000 (Scaled score) | **Time Limit**: 120 minutes | **Questions**: 60 multiple choice  
**Format**: 4 realistic scenarios chosen at random from 6 production contexts.

---

## Content Domains & Task Statements Matrix (1:1 Dedicated Practice Mapping)

### 🔷 Domain 1: Agentic Architecture & Orchestration (27%)
| Task Statement | Title | Key Architectural Principles | Dedicated Practice Location |
|---|---|---|---|
| **TS 1.1** | Agentic loops for autonomous execution | `stop_reason` control (`tool_use` vs `end_turn`), tool result appending, avoiding NLP text parsing for loop exit | [domain1/ts_1_1_multi_tool_agent_loop](domain1/ts_1_1_multi_tool_agent_loop/main.py) |
| **TS 1.2** | Multi-agent coordinator-subagent patterns | Hub-and-spoke topology, context isolation, dynamic routing by query complexity, synthesis gap evaluation | [domain1/ts_1_2_coordinator_subagents](domain1/ts_1_2_coordinator_subagents/main.py) |
| **TS 1.3** | Subagent invocation & spawning | `Task` tool in `allowedTools`, parallel subagent spawning in single turn, structured context + metadata | [domain1/ts_1_3_subagent_invocation_spawning](domain1/ts_1_3_subagent_invocation_spawning/main.py) |
| **TS 1.4** | Multi-step workflows & handoffs | Programmatic prerequisite gates (deterministic guarantees), structured handoff protocols for human escalation | [domain1/ts_1_4_prerequisite_enforcement](domain1/ts_1_4_prerequisite_enforcement/main.py) |
| **TS 1.5** | Agent SDK hooks | `PostToolUse` data normalization, tool call interception (blocking financial operations > $500) | [domain1/ts_1_5_sdk_hooks](domain1/ts_1_5_sdk_hooks/main.py) |
| **TS 1.6** | Task decomposition strategies | Prompt chaining for predictable reviews, dynamic decomposition for open-ended investigations | [domain1/ts_1_6_task_decomposition](domain1/ts_1_6_task_decomposition/main.py) |
| **TS 1.7** | Session state, resumption & forking | `--resume <session-name>`, `fork_session` for divergent exploration, injected summaries over stale context | [domain1/ts_1_7_session_management](domain1/ts_1_7_session_management/main.py) |

---

### 🔷 Domain 2: Tool Design & MCP Integration (18%)
| Task Statement | Title | Key Architectural Principles | Dedicated Practice Location |
|---|---|---|---|
| **TS 2.1** | Tool interfaces & boundaries | Differentiated descriptions, input formats, edge cases, boundaries between similar tools | [domain2/ts_2_1_tool_interface_design](domain2/ts_2_1_tool_interface_design/main.py) |
| **TS 2.2** | Structured error responses for MCP | `isError` flag, error categories (`transient`, `validation`, `business`, `permission`), `isRetryable: bool` | [domain2/ts_2_2_mcp_structured_errors](domain2/ts_2_2_mcp_structured_errors/main.py) |
| **TS 2.3** | Tool distribution & tool choice | Principle of least privilege (4-5 tools per agent), `tool_choice` (`auto`, `any`, forced `{"type": "tool"}`) | [domain2/ts_2_3_tool_distribution_and_choice](domain2/ts_2_3_tool_distribution_and_choice/main.py) |
| **TS 2.4** | MCP server integration | Project `.mcp.json` vs user `~/.claude.json`, `${ENV_VAR}` expansion, MCP resources for catalogs | [domain2/ts_2_4_mcp_server_integration](domain2/ts_2_4_mcp_server_integration/main.py) |
| **TS 2.5** | Built-in tools selection | `Grep` (pattern search), `Glob` (file paths), `Read`/`Write` (full files), `Edit` (anchor text), fallback `Read`+`Write` | [domain2/ts_2_5_builtin_tools_usage](domain2/ts_2_5_builtin_tools_usage/main.py) |

---

### 🔷 Domain 3: Claude Code Configuration & Workflows (20%)
| Task Statement | Title | Key Architectural Principles | Dedicated Practice Location |
|---|---|---|---|
| **TS 3.1** | CLAUDE.md hierarchy & scoping | User (`~/.claude/CLAUDE.md`) -> Project (`.claude/CLAUDE.md`) -> Directory; `@import` syntax; `/memory` check | [domain3/ts_3_1_claude_code_workflows](domain3/ts_3_1_claude_code_workflows/main.py) |
| **TS 3.2** | Custom slash commands & skills | `.claude/commands/`, `.claude/skills/` with `SKILL.md` frontmatter (`context: fork`, `allowed-tools`, `argument-hint`) | [domain3/ts_3_2_slash_commands_and_skills](domain3/ts_3_2_slash_commands_and_skills/main.py) |
| **TS 3.3** | Path-specific rules | YAML frontmatter `paths: [...]` for conditional loading without polluting context | [domain3/ts_3_3_path_specific_rules](domain3/ts_3_3_path_specific_rules/main.py) |
| **TS 3.4** | Plan mode vs direct execution | Plan mode for architectural/multi-file/complex decisions; Direct execution for single-file, well-scoped fixes | [domain3/ts_3_4_plan_mode_and_refinement](domain3/ts_3_4_plan_mode_and_refinement/main.py) |
| **TS 3.5** | Iterative refinement | 2-3 concrete I/O examples, test-driven iteration, interview pattern, addressing interacting issues together | [domain3/ts_3_5_iterative_refinement_interview](domain3/ts_3_5_iterative_refinement_interview/main.py) |
| **TS 3.6** | CI/CD pipeline integration | `-p` / `--print` non-interactive flag, `--output-format json`, `--json-schema`, independent review sessions | [domain3/ts_3_6_cicd_pipeline_automation](domain3/ts_3_6_cicd_pipeline_automation/main.py) |

---

### 🔷 Domain 4: Prompt Engineering & Structured Output (20%)
| Task Statement | Title | Key Architectural Principles | Dedicated Practice Location |
|---|---|---|---|
| **TS 4.1** | Explicit criteria & false positives | Concrete categorical criteria over vague advice ("be conservative"), severity criteria with negative boundaries | [domain4/ts_4_1_explicit_criteria_classification](domain4/ts_4_1_explicit_criteria_classification/main.py) |
| **TS 4.2** | Few-shot prompting | 2-4 targeted examples with reasoning, formatting consistency, handling structural variations | [domain4/ts_4_2_few_shot_and_multi_instance](domain4/ts_4_2_few_shot_and_multi_instance/main.py) |
| **TS 4.3** | Structured output with JSON schemas | Guaranteed syntax via `tool_use`, nullable fields to prevent hallucinations, enum "other" + detail string | [domain4/ts_4_3_structured_output_tool_use](domain4/ts_4_3_structured_output_tool_use/main.py) |
| **TS 4.4** | Validation & retry feedback loops | Retry with specific validation errors; recognizing when retry won't work (missing information) | [domain4/ts_4_4_validation_retry_feedback](domain4/ts_4_4_validation_retry_feedback/main.py) |
| **TS 4.5** | Message Batches API | 50% discount, 24h window (no SLA), non-blocking overnight workloads only, `custom_id` correlation | [domain4/ts_4_5_message_batches_api](domain4/ts_4_5_message_batches_api/main.py) |
| **TS 4.6** | Multi-instance & multi-pass review | Independent Claude review instances (no author bias), per-file pass + cross-file integration pass | [domain4/ts_4_6_multi_pass_review](domain4/ts_4_6_multi_pass_review/main.py) |

---

### 🔷 Domain 5: Context Management & Reliability (15%)
| Task Statement | Title | Key Architectural Principles | Dedicated Practice Location |
|---|---|---|---|
| **TS 5.1** | Context window preservation | Persistent "Case Facts" block outside summarized history, trimming tool outputs, "lost in the middle" mitigation | [domain5/ts_5_1_context_preservation](domain5/ts_5_1_context_preservation/main.py) |
| **TS 5.2** | Escalation & ambiguity patterns | Explicit triggers (customer demand, policy gaps), immediate escalation upon demand, asking for clarification on ties | [domain5/ts_5_2_escalation_and_provenance](domain5/ts_5_2_escalation_and_provenance/main.py) |
| **TS 5.3** | Error propagation across multi-agent | Structured error context, distinguishing access failures vs valid empty matches, synthesis coverage annotations | [domain5/ts_5_3_error_propagation_coverage](domain5/ts_5_3_error_propagation_coverage/main.py) |
| **TS 5.4** | Large codebase exploration | Scratchpad files, Explore subagent, structured state manifests for crash recovery, `/compact` | [domain5/ts_5_4_scratchpads_and_human_review](domain5/ts_5_4_scratchpads_and_human_review/main.py) |
| **TS 5.5** | Human review & confidence calibration | Segmented accuracy validation, stratified random sampling (5-10%) of high-confidence results, calibrated routing | [domain5/ts_5_5_human_review_calibration](domain5/ts_5_5_human_review_calibration/main.py) |
| **TS 5.6** | Information provenance & uncertainty | Structured claim-source mappings with dates, preserving conflicting statistics with source attribution | [domain5/ts_5_6_provenance_and_uncertainty](domain5/ts_5_6_provenance_and_uncertainty/main.py) |

---

## 🎯 6 Real-World Exam Scenarios
1. **Scenario 1**: Customer Support Resolution Agent (Domain 1, 2, 5)
2. **Scenario 2**: Code Generation with Claude Code (Domain 3, 5)
3. **Scenario 3**: Multi-Agent Research System (Domain 1, 2, 5)
4. **Scenario 4**: Developer Productivity with Claude (Domain 2, 3, 1)
5. **Scenario 5**: Claude Code for Continuous Integration (Domain 3, 4)
6. **Scenario 6**: Structured Data Extraction (Domain 4, 5)

Detailed scenario notes are located in [scenarios/README.md](scenarios/README.md).
