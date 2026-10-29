"""
Domain 3: Claude Code Configuration & Workflows
Task Statement 3.4: Determine when to use plan mode vs direct execution
Task Statement 3.5 (helpers): iterative refinement prompts
Exam Scenario 2: Code Generation with Claude Code

Offline teaching heuristic (no API calls):
1. Plan mode: large, multi-file, architectural changes or several valid approaches
   (e.g. monolith -> microservices).
2. Direct execution: small, well-scoped changes (single-file fix with a stack trace,
   one added validation).
3. The Explore subagent isolates verbose discovery and returns a summary.
4. Combine them: plan mode for investigation, direct execution for the approved plan.
The file-count threshold below is a teaching heuristic, not an official limit.
"""

from dataclasses import dataclass, field

MULTI_FILE_THRESHOLD = 3  # Teaching heuristic: more files than this suggests plan mode.


@dataclass
class WorkflowStrategyDecision:
    mode: str  # "plan_mode" | "direct_execution"
    rationale: str
    recommended_tools: list[str]
    use_explore_subagent: bool = False
    phases: list[str] = field(default_factory=list)


def evaluate_execution_mode(
    file_count_affected: int,
    has_architectural_tradeoffs: bool,
    has_known_stack_trace: bool,
    is_single_function_fix: bool,
) -> WorkflowStrategyDecision:
    """Chooses plan mode or direct execution from simple scope signals."""
    if file_count_affected > MULTI_FILE_THRESHOLD or has_architectural_tradeoffs:
        return WorkflowStrategyDecision(
            mode="plan_mode",
            rationale=(
                f"Task affects {file_count_affected} files or has design trade-offs. "
                "Investigate and agree on an approach before editing."
            ),
            recommended_tools=["Explore", "Read", "Grep", "Glob"],
            use_explore_subagent=True,
            phases=["plan mode: investigate and propose", "direct execution: apply the plan"],
        )
    if is_single_function_fix or has_known_stack_trace:
        return WorkflowStrategyDecision(
            mode="direct_execution",
            rationale="Well-scoped change with a clear cause. Edit directly.",
            recommended_tools=["Read", "Edit"],
            phases=["direct execution: fix and run tests"],
        )
    return WorkflowStrategyDecision(
        mode="plan_mode",
        rationale="Scope is unclear; explore before modifying files.",
        recommended_tools=["Explore", "Read"],
        use_explore_subagent=True,
        phases=["plan mode: investigate and propose", "direct execution: apply the plan"],
    )


def build_interview_pattern_prompt(domain_topic: str) -> str:
    """Interview pattern: Claude asks questions first to surface hidden considerations."""
    return (
        f"You are designing a solution for {domain_topic}. Before writing any code, "
        "interview me by asking 3-5 clarifying questions regarding cache invalidation, "
        "failure modes, throughput expectations, and backward compatibility."
    )


def format_few_shot_refinement(examples: list[dict[str, str]]) -> str:
    """Iterative refinement via 2-3 concrete input/output examples."""
    formatted = ["### CONCRETE TRANSFORMATION EXAMPLES:"]
    for i, ex in enumerate(examples, start=1):
        formatted.append(f"Example {i}:\n  Input: {ex['input']}\n  Expected Output: {ex['output']}")
    return "\n".join(formatted)


def main() -> None:
    cases = {
        "Monolith -> microservices (45 files)": (45, True, False, False),
        "Single-file bug with stack trace": (1, False, True, True),
    }
    for name, (files, tradeoffs, trace, single) in cases.items():
        decision = evaluate_execution_mode(files, tradeoffs, trace, single)
        print(f"{name}: {decision.mode}")
        print(f"  rationale: {decision.rationale}")
        print(f"  phases: {decision.phases}")


if __name__ == "__main__":
    main()
