# Task Statement 2.1: Design Effective Tool Interfaces with Clear Descriptions and Boundaries

> Scenario alignment: Scenario 1 (Customer Support)

## In One Minute

- **What**: Claude picks a tool by reading its **name, description and input schema**. Nothing else.
- **Why it matters**: Two tools with thin or overlapping descriptions get confused. The agent calls the wrong one.
- **The fix**: Write rich descriptions: purpose, input formats, example queries, edge cases, and boundaries ("do NOT use for X; use Y").
- **Also**: Rename or split vague tools by purpose. Keyword-heavy system prompts can override good descriptions.
- **Exam answer in one line**: When the agent misroutes between similar tools, **expand the tool descriptions first**.

---

## 🧒 Explain Like I'm 13

**The picture:** Labels on kitchen drawers. A drawer labelled "stuff" gets the wrong things. A drawer labelled "forks and spoons, for eating, NOT knives" gets used correctly. Claude picks tools by **reading the labels** (descriptions), so fix the labels first.

**In plain steps:**
1. For each tool write what it returns, what input looks like (with an example), when to use it, and when **not** to.
2. If two tools do the same thing, rename or split them by purpose.
3. If a tool is still over-used, look for the system prompt saying "always use X".

**Tiny example:** "Retrieves customer information" vs "Retrieves order details" gets mixed up. "Customer PROFILE by CUST-id or email. Not for order status, use lookup_order" does not.

---

## 📖 Concepts Explained

### 1. Why it matters
Tool descriptions are routing instructions for the model. They are not documentation for people. Short descriptions such as `"Retrieves order details"` and `"Retrieves customer details"` look the same to the model. The result is wrong calls, bad arguments and wasted turns.

### 2. How a good description works
A strong description has five parts:
1. **Purpose**: what data it returns, in one or two sentences.
2. **Input formats**: what the argument looks like (`ORD-` plus digits, an email, a `CUST-XXXX` ID).
3. **Example queries**: two or three real user requests that should trigger it.
4. **Edge cases**: what happens on no match, partial match, bad format.
5. **Boundaries**: what it must NOT be used for, and which tool to use instead.

### 3. Rename and split vague tools
Two tools called `analyze_content` and `analyze_document` overlap. The model cannot tell them apart. Split by **purpose** and rename:

| Before | After | One job |
|---|---|---|
| `analyze_document` | `extract_data_points` | Pull fields out of one document |
| `analyze_document` | `summarize_content` | Write a short summary |
| `analyze_document` | `verify_claim_against_source` | Check a claim against the text |

### 4. System prompts can override descriptions
If the system prompt says "always check the account first", the model may keep calling `get_customer` for every question. Keyword-style wording in a system prompt competes with the tool descriptions. Review the prompt for words that push toward one tool.

### 5. Where `tool_choice` fits
Use `tool_choice` to force a mandatory step (see [2.3](../ts_2_3_tool_distribution_and_choice/README.md)). It is **not** the first fix for misrouting. Better descriptions come first.

---

## 🔑 Key Terms

- **Tool description**: The authoritative markdown text within a tool's JSON schema that guides Claude's semantic routing by defining its exact purpose, trigger phrases, argument formats, and explicit negative boundaries.
- **Boundary statement**: An explicit negative constraint within a tool description (for example, "Do NOT use for tracking; use `lookup_order`") that steers the model away from near-neighbor tools.
- **Overlapping descriptions**: Semantic ambiguity between two or more tools with similar or generic summaries, which causes non-deterministic tool selection and frequent misrouting errors.
- **Input format**: The exact structural specification, pattern, or syntax expected for a tool parameter (such as `ORD-[0-9]{4}`), preventing Claude from passing invalid or hallucinated arguments.
- **Tool decomposition (split / rename)**: The architectural practice of replacing a broad, multi-purpose tool with focused, single-responsibility functions that each have distinct names and unambiguous scopes.

---

## 🏗️ Architecture

```mermaid
---
config:
  htmlLabels: false
---
flowchart TD
    Query["User asks:<br>Where is order ORD-9821?"] --> Router["Claude reads all<br>tool descriptions"]
    Router --> Check{"Which description<br>matches best?"}
    Check -->|"Order status, tracking, ORD- IDs"| Order["lookup_order<br>order_id: ORD-digits"]
    Check -->|"Identity, tier, CUST- IDs"| Cust["get_customer<br>identifier: email or CUST-XXXX"]
    Order --> Result["tool_result returned<br>to Claude"]
    Cust --> Result
```

---

## 🧪 Worked Example

### ❌ Invalid Example (Anti-Pattern: Vague, Overlapping One-Line Tool Descriptions)
```python
# BROKEN: Minimal one-line descriptions with zero boundaries or format specifications
tools = [
    {
        "name": "lookup_order",
        "description": "Retrieves order details.",  # Vague! Doesn't mention tracking or delivery status
        "input_schema": {"type": "object", "properties": {"id": {"type": "string"}}}
    },
    {
        "name": "get_customer",
        "description": "Retrieves customer information.",  # Overlaps! Doesn't specify boundaries
        "input_schema": {"type": "object", "properties": {"id": {"type": "string"}}}
    }
]

# User prompt: "Where is my package? Order ORD-9821"
# What happens: Claude flips a coin and calls get_customer(id="ORD-9821").
# The customer lookup fails or returns the wrong data, derailing the support turn!
```

### ✅ Valid Example (Production Pattern: 5-Part Description with Negative Boundaries)
```python
# CORRECT: Rich description with purpose, input format, sample queries, edge cases, and boundaries
tools = [
    {
        "name": "lookup_order",
        "description": (
            "Lookup real-time order status, tracking numbers, shipping carriers, and return eligibility.\n"
            "Input: order_id formatted strictly as 'ORD-' followed by digits (e.g. 'ORD-9821').\n"
            "Sample queries: 'Where is order ORD-9821?', 'Has my shipment arrived?'.\n"
            "Edge cases: Returns found=false if the order ID is not in the database.\n"
            "Negative Boundary: Do NOT use for customer contact info or email lookups; use get_customer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "pattern": "^ORD-[0-9]+$"}},
            "required": ["order_id"]
        }
    },
    {
        "name": "get_customer",
        "description": (
            "Lookup customer account profile, loyalty tier, and registered contact email.\n"
            "Input: customer_id (e.g. 'CUST-101') or verified email address.\n"
            "Negative Boundary: Do NOT use for order tracking or shipping status; use lookup_order."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"identifier": {"type": "string"}},
            "required": ["identifier"]
        }
    }
]

# User prompt: "Where is my package? Order ORD-9821"
# Result: Claude deterministically selects lookup_order because the negative boundary explicitly rules out get_customer!
```

The code in [main.py](main.py) has both tools, `audit_tool()` to flag thin descriptions, and `description_overlap()` to measure similarity.

---

## ⚠️ Exam Traps and Correct Patterns

### Trap 1: Wrong tool picked because descriptions are thin

**Exam scenario**: The agent calls `get_customer` when the user asks "where is order #12345?". The two descriptions are "Retrieves customer information" and "Retrieves order details".

**Tempting answers**: (A) add few-shot examples to the prompt, (B) build a keyword or classifier routing layer, (C) merge both into one `lookup` tool.

**Why they tempt**: each treats the symptom (a wrong pick) with something concrete.

**Root cause**: the tool description is the **primary signal** the model uses to select a tool. Two vague descriptions give it nothing to separate them.

| Fix | Verdict |
|---|---|
| Few-shot in the prompt | Heavier, adds tokens on every request, leaves the unclear tool text in place |
| Routing layer | Extra brittle code that must be maintained next to the real cause |
| Merge into one tool | Bigger, more ambiguous schema. Selection gets harder, not easier |
| **Rewrite the descriptions** | Fixes the cause directly |

```json
// ANTI-PATTERN
{"name": "get_customer", "description": "Retrieves customer information"}

// PATTERN
{
  "name": "get_customer",
  "description": "Look up a customer PROFILE (name, email, tier, verified status) by customer ID (CUST-12345) or email. Use this to verify identity. Does NOT return orders: use lookup_order for order status, shipping, or items. Not for order numbers.",
  "input_schema": {"type": "object", "properties": {
    "customer_id": {"type": "string", "description": "Format CUST-12345"}}}
}
```

A good description states: what it returns, accepted input formats with an example, when to use it, and when **not** to use it (naming the sibling tool).

### Trap 2: Overlapping tools kept alive with a prompt rule

**Exam scenario**: `analyze_content` and `analyze_document` both "analyse text". The model alternates between them.

- Anti-pattern: keep both and add "use analyze_document for PDFs" to the system prompt. The prompt now competes with the tool text, and the two disagree over time.
- Pattern: remove the overlap. Rename or split by **purpose** (`extract_invoice_fields`, `summarize_web_page`), or drop one. A tool name should tell the model what it is for.

### Trap 3: The system prompt quietly overrides good descriptions

**Exam scenario**: Descriptions were fixed, but the agent still over-uses `search_web`. The system prompt contains "Always search before answering".

Keyword-style prompt wording like that acts as a strong rule and wins against tool descriptions. After rewriting descriptions, also grep the system prompt for "always", "never", and tool names. Tune descriptions **and** remove conflicting wording.

### Trap 4: No argument formats

```text
User: "Look up the order for jane@acme.com"
Tool arg description: "id: the identifier"
Model sends order_id="jane@acme.com"  -> validation error
```

Fix with explicit formats and examples in each parameter description (`order_id: ORD-2026-0001; not an email`).

---

## 🛠️ Hands-on Workbook Guide

Open [`ts_2_1_tool_interface_design.ipynb`](ts_2_1_tool_interface_design.ipynb). It runs offline.
1. **Load** the tools and the vague pair from [main.py](main.py).
2. **Audit** thin descriptions with `audit_tool()`.
3. **Measure** overlap with `description_overlap()`.
4. **Compare** the vague pair with the split tools.
5. **Dispatch** a request to `lookup_order` and check the result.

Run live API examples by hand only. See [EXECUTION_POLICY.md](../../EXECUTION_POLICY.md).

---

## 📝 Exam-Style Practice Questions

**Q1.** A support agent has `get_customer` ("Retrieves customer details") and `lookup_order` ("Retrieves order details"). It often calls `get_customer` for order questions. What is the best first step?
- A. Add few-shot examples of correct tool use to the system prompt.
- B. Expand each tool description with formats, example queries and boundaries.
- C. Add a keyword-based routing layer before the model.
- D. Merge both tools into one `get_info` tool.

**Q2.** A research agent has `analyze_content` and `analyze_document`. Both descriptions say "analyzes text". It alternates between them. What is the best fix?
- A. Rename and split by purpose: `extract_data_points`, `summarize_content`, `verify_claim_against_source`.
- B. Add a system prompt rule "prefer analyze_document".
- C. Set `tool_choice` to force `analyze_document` on every turn.
- D. Lower the temperature.

**Q3.** Tool descriptions are detailed, but the agent still calls `get_customer` first on every request. The system prompt says "Always check the customer account before doing anything". What is the most likely cause?
- A. The model cannot read long descriptions.
- B. `lookup_order` needs more parameters.
- C. The tool schemas are missing `additionalProperties`.
- D. The keyword-style system prompt instruction is overriding the tool descriptions.

### Answers

**Q1 → B.** Descriptions are the primary selection mechanism.
- A: Few-shot adds prompt weight and leaves the unclear tool text as is.
- C: A routing layer is brittle extra code for a cause that a description fix removes.
- D: Merging makes one larger, more ambiguous tool.

**Q2 → A.** Single-purpose names remove the overlap.
- B: A prompt rule competes with the tool text and hides the real problem.
- C: Forcing one tool means the other can never be used.
- D: Temperature does not change which description matches.

**Q3 → D.** Prompt wording can override descriptions. Remove or soften the keyword instruction.
- A: Long, detailed descriptions are the recommended practice.
- B: Parameters do not decide which tool is chosen first.
- C: `additionalProperties` affects validation, not selection.

---

## ✅ Self-Check Checklist

- [ ] I can name the five parts of a strong tool description.
- [ ] I can explain why overlapping descriptions cause misrouting.
- [ ] I know the first fix for misrouting: expand descriptions (not few-shot, routing layer or merging).
- [ ] I can split `analyze_document` into three single-purpose tools.
- [ ] I know a keyword-sensitive system prompt can override descriptions.

**Memory hook**: *"The description is the router. Fix the label before you fix the system."*

---

## 🧭 Navigation & Study Links
- ⬅️ **Previous Topic**: [TS 1.7: Session State & Lifecycle Management](../../domain1/ts_1_7_session_management/README.md)
- 📋 **Domain Overview**: [Domain 2: Tool Design & Model Context Protocol (MCP)](../README.md)
- ➡️ **Next Topic**: [TS 2.2: MCP Structured Errors & Self-Correction](../ts_2_2_mcp_structured_errors/README.md)
- 🎯 **Scenario Practice**: [Master Scenario Practice](../../scenarios/MASTER_SCENARIO_PRACTICE.md)
