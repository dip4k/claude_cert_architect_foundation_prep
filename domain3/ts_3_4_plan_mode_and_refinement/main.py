"""
Domain 3: Claude Code Configuration & Workflows
Task Statement 3.4: Determine when to use plan mode vs direct execution
Task Statement 3.5: Apply iterative refinement techniques for progressive improvement
Exam Scenario 2: Code Generation with Claude Code

Key Exam Concepts Demonstrated:
1. Plan mode decision criteria:
   - Plan Mode: Multi-file refactoring, microservice extraction, migrations (40+ files),
     evaluating multiple valid designs before making irreversible edits.
   - Direct Execution: Single-file well-scoped bug fixes with clear stack traces.
2. The Explore Subagent: Isolating verbose codebase discovery into summaries.
3. Iterative refinement:
   - Providing 2-3 concrete I/O examples to clarify ambiguous prose.
   - The Interview Pattern: Prompting Claude to surface considerations before writing code.
   - Reporting interacting issues together in one prompt vs independent issues sequentially.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class WorkflowStrategyDecision:
    mode: str  # "plan_mode" | "direct_execution"
    rationale: str
    recommended_tools: List[str]


def evaluate_execution_mode(
    file_count_affected: int,
    has_architectural_tradeoffs: bool,
    has_known_stack_trace: bool,
    is_single_function_fix: bool,
) -> WorkflowStrategyDecision:
    """
    Evaluates whether a software task warrants Plan Mode or Direct Execution.
    """
    if file_count_affected > 3 or has_architectural_tradeoffs:
        return WorkflowStrategyDecision(
            mode="plan_mode",
            rationale=(
                f"Task affects {file_count_affected} files with architectural trade-offs. "
                "Must enter Plan Mode to explore dependencies, design interfaces, and confirm approach."
            ),
            recommended_tools=["Explore", "Read", "Grep", "Glob"],
        )
    elif is_single_function_fix or has_known_stack_trace:
        return WorkflowStrategyDecision(
            mode="direct_execution",
            rationale="Well-scoped, isolated modification with clear root cause. Proceed directly with edits.",
            recommended_tools=["Read", "Edit"],
        )
    return WorkflowStrategyDecision(
        mode="plan_mode",
        rationale="Uncertain scope; explore safely before modifying files.",
        recommended_tools=["Explore", "Read"],
    )


def build_interview_pattern_prompt(domain_topic: str) -> str:
    """The Interview Pattern: Prompting Claude to interview the developer before implementing."""
    return (
        f"You are designing a solution for {domain_topic}. Before writing any code, "
        "interview me by asking 3-5 clarifying questions regarding cache invalidation, "
        "failure modes, throughput expectations, and backward compatibility."
    )


def format_few_shot_refinement(examples: List[Dict[str, str]]) -> str:
    """Iterative refinement via concrete input/output examples."""
    formatted = ["### CONCRETE TRANSFORMATION EXAMPLES:"]
    for i, ex in enumerate(examples, start=1):
        formatted.append(f"Example {i}:\n  Input: {ex['input']}\n  Expected Output: {ex['output']}")
    return "\n".join(formatted)


def main() -> None:
    # Example 1: Microservices migration affecting 45 files
    d1 = evaluate_execution_mode(
        file_count_affected=45,
        has_architectural_tradeoffs=True,
        has_known_stack_trace=False,
        is_single_function_fix=False,
    )
    print("Microservices Migration Decision:", d1.mode)
    print("Rationale:", d1.rationale, "\n")

    # Example 2: Single-file bug fix with stack trace
    d2 = evaluate_execution_mode(
        file_count_affected=1,
        has_architectural_tradeoffs=False,
        has_known_stack_trace=True,
        is_single_function_fix=True,
    )
    print("Bug Fix Decision:", d2.mode)
    print("Rationale:", d2.rationale)


if __name__ == "__main__":
    main()
