# Task Statement 4.4: Validation & Retry Feedback Loops

## 🎯 Exam Objective
Understand how to design closed-loop validation with targeted error feedback, bounded retries, and early termination on missing source data.

---

## 🏗️ Architecture: Closed-Loop Validation with Early Exit

```mermaid
flowchart TD
    Extracted["Claude Outputs Extracted Payload"] --> Validator{"Validator Check"}
    
    Validator -->|"Valid"| Success["Commit Extracted Data"]
    
    Validator -->|"Invalid (Schema / Constraint)"| ErrorType{"Is Error Fixable?"}
    
    ErrorType -->|"Missing source fact"| FastFail["Stop Retrying Immediately<br>Flag Missing / Nullable Field"]
    
    ErrorType -->|"Formatting / Math mismatch"| RetryCount{"Retry Count < 3?"}
    
    RetryCount -->|"Yes"| FeedBack["Inject Targeted Feedback<br>'Discount cannot exceed subtotal'"]
    FeedBack --> Extracted
    
    RetryCount -->|"No (Exhausted)"| Fallback["Escalate to Human Review"]
```

---

## ⚠️ The "Unfixable Error" Exam Trap

### Trap:
A question presents a document missing a Customer VAT Number. The schema marks `vat_number: str` as required. Claude fails validation. The system blindly retries 3 times.

### Correct Answer:
If the source document **genuinely lacks the data**, retrying will either:
1. Cause repeated failures (wasted tokens/latency), or
2. Force the model to hallucinate a fabricated number.

**Solution**: Stop immediately on missing source data and mark as unresolvable / escalate to human review.

---

## 🛠️ Production Code Reference
- Interactive Workbook: [`ts_4_4_validation_retry_feedback.ipynb`](ts_4_4_validation_retry_feedback.ipynb)
- Runnable Script: [`main.py`](main.py)
- Offline Verification: Run via `uv run pytest tests/test_domain4_full.py` in WSL.


### Exam Insight:
- Retrying **cannot invent data that is absent from the input document**.
- Retrying will either cause Claude to **hallucinate** a plausible-looking VAT number or repeatedly fail.
- **Correct Solution**:
  1. Schemas for extractions must mark non-guaranteed fields as **`Optional` / nullable**.
  2. The validation feedback loop must distinguish between **correctable syntax/logic errors** and **unrecoverable missing source facts**.
