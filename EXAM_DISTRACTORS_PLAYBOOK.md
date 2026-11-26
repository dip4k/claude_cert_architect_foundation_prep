# 🚫 CCAR-F Exam Distractors & Elimination Playbook

> **Goal:** Spot and cross out **wrong answers (distractors)** fast on the **Claude Certified Architect – Foundations (CCAR-F)** exam.
>
> **How to use this:** Most exam questions give you 1 right answer and 3 wrong answers that *sound* smart. Learn the patterns below so you can cross out the 3 wrong answers in under 30 seconds.

---

## 🎯 Part 1: Your 5 Personal Traps (From Your Practice Misses)

Watch out for these 5 habits that tripped you up in practice:

| What You Were Tempted By | Wrong Answer Example | Why It Fails (Plain English) | What to Pick Instead |
| :--- | :--- | :--- | :--- |
| **1. "Add a 2nd AI to clean up"** | Use a second Claude call to convert text replies into JSON. | Costs 2x money and time, and the 2nd AI can make new mistakes while rewriting. | Force JSON on the **1st call** using `tool_use` + `tool_choice` (**TS 4.3**). |
| **2. "Split one page into 2 calls"** | Run one API call for *shipper* and a second call for *consignee*. | Costs 2x money, and both names are still on the same page so Claude still mixes them up. | Keep **1 call** and add **2–4 examples** showing *why* each name belongs in its box (**TS 4.2**). |
| **3. "Expect Batch API to run live tools"** | Use `custom_id` to connect a Batch job to a live CRM lookup job. | Batch API runs offline (up to 24h) and cannot pause to run tools. `custom_id` is just a tracking label. | **Fetch CRM data first**, then put it right inside each Batch prompt (**TS 4.5**). |
| **4. "Let Claude decide who is telling the truth"** | Tell Claude to use its own knowledge to pick the truthful news site and drop the biased blog. | Claude shouldn't secretly censor sources or guess truth from training memory. | Use a helper step to **label source bias**, then make Claude **cite who said what** (**TS 5.6**). |
| **5. "Make fields optional & add extra labels"** | Make `pros`/`cons` optional, and add both `"neutral"` and `"unclear"` to sentiment. | Optional lists still get filled in or crash code; `"neutral"` isn't what you need for sarcasm. | Allow **empty lists (`[]`)** for `pros`/`cons`, and add **only `"unclear"`** for sarcasm (**TS 4.3**). |

---

## 🚩 Part 2: Red-Flag Phrases (Cross Out Immediately)

If an answer choice says any of these, it is **almost always wrong**:

| Red-Flag Phrase in an Answer | Domain / TS | Why It's Wrong |
| :--- | :---: | :--- |
| *"Write `CRITICAL: NEVER DO X` in bold in the prompt"* | D1 (`TS 1.4`) | Prompts are suggestions, not locks. Claude can still break rules on tricky inputs. Use **real code checks / `PreToolUse` hooks**. |
| *"Set `temperature: 0` so Claude always outputs JSON"* | D4 (`TS 4.3`) | `temperature: 0` just makes Claude pick the top word—it does **not** force JSON format. |
| *"Increase `max_tokens` or use a bigger context window"* | D1 (`TS 1.6`) | Bigger context doesn't fix lost focus when reading 20 files at once. **Split the work into 2 passes or subagents.** |
| *"Ask the same Claude chat to review and fix its own code"* | D4 (`TS 4.6`) | Claude gets stuck defending its first mistake. Open a **fresh, separate Claude instance** to review it. |
| *"Ask Claude for a confidence score and filter out < 85%"* | D4 (`TS 4.1`)<br>D5 (`TS 5.5`) | Claude is often 99% confident even when it's wrong. Use **clear yes/no rules** and **spot-check random samples**. |
| *"Average two conflicting numbers ($1.2B & $1.4B → $1.3B)"* | D5 (`TS 5.6`) | That invents a fake number neither source said. Always **show both numbers side-by-side with sources**. |
| *"Use Batch API for pre-merge PR checks to save 50%"* | D4 (`TS 4.5`) | Batch API takes up to **24 hours** with no speed guarantee—developers would be stuck waiting to merge. |
| *"Return an empty list `[]` when an API times out"* | D2 (`TS 2.2`)<br>D5 (`TS 5.3`) | Hides a broken server so it looks like *"0 results found."* Return an **error flag** + **warning note**. |
| *"Train a separate ML model to pick the right tool"* | D2 (`TS 2.1`) | Way too complex. Fix wrong tool picks by **writing clearer tool descriptions** with examples. |
| *"Turn on `thinking` AND force a tool (`tool_choice: 'any'`) or `temperature: 0`"* | D2 (`TS 2.3`) | **Crashes with HTTP 400.** Extended thinking only works with `tool_choice: "auto"` or `"none"` and no temperature setting. |

---

## 📚 Part 3: All 5 Domains — Distractor Cheat Sheet (All 27 Topics)

### 🏗️ Domain 1: Agentic Architecture & Orchestration (27%)

| TS | Topic | 🎯 What the System Needs | ❌ Tempting Wrong Answer | 💥 Why It Breaks | ✅ Right Answer |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **1.1** | **Loop Control** | Know exactly when Claude is done running tools. | Check if Claude's text says `"I am done"`, or stop after 5 tries. | Claude talks before calling tools, and 5 tries cuts off real tasks early. | Check **`response.stop_reason`** (`"tool_use"` = keep going, `"end_turn"` = stop). |
| **1.2** | **Team Structure** | Pass tasks to helper agents cleanly without leaks or loops. | Let helper agents chat directly with each other, or assume they see the main chat. | Helpers get stuck in endless loops; actually, helpers start with a **blank memory**. | Use **1 Boss (Coordinator)** that sends clear instructions to each isolated helper. |
| **1.3** | **Running Helpers Fast** | Run 3 independent subtasks quickly at the same time. | Call helpers one-by-one across 3 turns, or forget `"Agent"` in `allowedTools`. | One-by-one is slow (+40% wait); missing `"Agent"` means helpers can't start. | Allow `"Agent"` in `allowedTools` and send **all 3 helper calls in 1 turn**. |
| **1.4** | **Safety Rules** | Make sure risky actions (refunds > $500) never skip ID checks. | Put *"ALWAYS check ID first"* in bold in the system prompt. | Tricky users can still talk Claude into skipping a prompt rule. | Block the refund in **real Python/app code** until the ID check passes. |
| **1.5** | **SDK Hooks** | Block bad actions before they run, and clean up messy tool data. | Tell Claude in the prompt to clean up messy dates/currency after each tool call. | Wastes tokens and Claude can still make formatting mistakes. | Use **`PreToolUse`** to block unsafe calls; **`PostToolUse`** to trim/clean data. |
| **1.6** | **Splitting Big Jobs** | Review 15+ files without missing bugs across files. | Paste all 15 files into one huge prompt, or run it 3 times and vote. | Too much text at once causes missed bugs ("lost focus"). | **Two passes**: Pass 1 checks each file alone → Pass 2 checks how files connect. |
| **1.7** | **Old Sessions** | Keep working safely after a big `git rebase` or file rewrite. | Run `claude --resume` right after rebasing 40 commits. | Claude remembers old line numbers that don't exist anymore. | Save key facts in a **short summary**, then start a **fresh session**. |

---

### 🔧 Domain 2: Tool Design & MCP Integration (18%)

| TS | Topic | 🎯 What the System Needs | ❌ Tempting Wrong Answer | 💥 Why It Breaks | ✅ Right Answer |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **2.1** | **Picking the Right Tool** | Stop Claude from mixing up `get_customer` and `lookup_order`. | Combine them into one giant tool, or train an ML classifier to pick. | Giant tools confuse parameters; ML routers are slow and hard to maintain. | Write **clear tool descriptions** with input formats, examples, and *"Do NOT use for..."* notes. |
| **2.2** | **Tool Errors** | Tell Claude if a tool failed temporarily, got bad input, or found 0 matches. | Return `"Failed"` text, crash with an exception, or mark 0 search hits as an error. | Claude retries unfixable errors or quits when a search simply has 0 matches. | Return `isError: true` + error type + `isRetryable`. **0 matches = `isError: false`**. |
| **2.3** | **Tool Limits & Thinking** | Keep tool picks accurate and avoid crashes when thinking is on. | Give every agent all 18+ tools, or force a tool while `thinking` is on. | Too many tools confuse Claude; forcing a tool with `thinking` throws **HTTP 400**. | Give each agent **4–5 tools max**; use `tool_choice: "auto"`/`"none"` with `thinking`. |
| **2.4** | **Sharing MCP Tools** | Share MCP tools safely in Git and show DB schemas cheaply. | Paste API keys in `.mcp.json`, put team tools in `~/.claude.json`, or run bash to inspect DBs. | Leaks passwords to Git; teammates don't get `~/.claude.json`; bash wastes tokens. | Team tools in **`.mcp.json`** with **`${ENV_VAR}`**; personal in `~/.claude.json`; schemas as **MCP Resources**. |
| **2.5** | **Code Search & Edit** | Find and edit code in big repos without wasting tokens or looping. | Read 300 files upfront, or retry the exact same broken `Edit` call. | Fills up memory fast; identical `Edit` calls fail the same way forever. | Search step-by-step: **`Glob` → `Grep` → `Read`**. If `Edit` fails, add more context lines or use **`Read + Write`**. |

---

### 💻 Domain 3: Claude Code Configuration & Workflows (20%)

| TS | Topic | 🎯 What the System Needs | ❌ Tempting Wrong Answer | 💥 Why It Breaks | ✅ Right Answer |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **3.1** | **Team Rules (`CLAUDE.md`)** | Make sure every teammate and CI job automatically gets team rules. | Save rules in `~/.claude/CLAUDE.md`, or write a 600-line rule file. | Home folders aren't in Git; giant rule files get ignored by Claude. | Put rules in **project `./CLAUDE.md` or `.claude/CLAUDE.md`** (< 200 lines + `@import`). |
| **3.2** | **Skills & Shortcuts** | Run noisy log/test commands without cluttering the main chat. | Run big log-reading skills directly inside the main chat window. | Dumps 30k tokens of logs into chat and ruins Claude's focus. | Set **`context: fork`** and limit **`allowed-tools`** in `SKILL.md`. |
| **3.3** | **File-Specific Rules** | Apply test rules to `**/*.test.tsx` files across 30 folders. | Copy-paste `CLAUDE.md` into 30 folders, or load test rules for every file. | Hard to update 30 copies; loading everywhere wastes tokens. | Put rules in **`.claude/rules/*.md`** with **`paths: ["**/*.test.tsx"]`**. |
| **3.4** | **Plan vs. Edit Fast** | Pick the right workflow for big refactors vs. tiny bug fixes. | Use Plan Mode for a 1-line typo, or jump straight into editing 40 files. | Plan Mode wastes time on tiny fixes; jumping in breaks imports on 40 files. | **Plan Mode** for big/multi-file work; **Direct Edit** for clear 1-file fixes. |
| **3.5** | **Clear Instructions** | Get the exact code output you want on unclear tasks. | Write vague feedback like *"make it cleaner and handle edge cases."* | Claude guesses what you mean and writes the wrong thing. | Give **2–3 input/output examples**, tests, or use the **Interview Pattern** (ask questions first). |
| **3.6** | **Automated CI/CD** | Run Claude Code in GitHub Actions / CI scripts without hanging. | Run bare `claude`, or use fake flags like `--batch` or `CLAUDE_HEADLESS=true`. | Bare `claude` freezes waiting for someone to type on a keyboard. | Use **`claude -p` (`--print`)**, `--output-format json`, `--json-schema`, and a **fresh reviewer**. |

---

### 🎯 Domain 4: Prompt Engineering & Structured Output (20%)

| TS | Topic | 🎯 What the System Needs | ❌ Tempting Wrong Answer | 💥 Why It Breaks | ✅ Right Answer |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **4.1** | **Stopping False Alarms** | Stop a code review bot from complaining about harmless style/mocks. | Prompt *"be conservative and only report high-confidence bugs."* | Claude still flags the same noisy things and is bad at judging its own confidence. | Give **clear "report vs. ignore" rules** with examples; turn off noisy categories. |
| **4.2** | **Disambiguating Fields** | Stop Claude from swapping lookalike fields (*shipper* vs. *consignee*) on one page. | Split into 2 separate API calls, or show 15 identical examples. | 2 calls cost double and still fail; 15 identical examples only work for one layout. | Keep **1 call** with **2–4 varied examples** (tables, text, missing) explaining *why* each field was picked. |
| **4.3** | **Guaranteed JSON** | Always get valid JSON without Claude inventing fake data for blanks. | Parse ` ```json ` text, use a 2nd AI to fix prose, or make every field required. | Text breaks JSON parsers; 2nd AI adds cost; required fields force Claude to make up data. | Use **`tool_use` + `strict: true`**, allow **`[]`** for empty lists, **`["string", "null"]`** for missing text, and **`"unclear"`** labels. |
| **4.4** | **Retries & Missing Info** | Fix formatting/math slips without forcing Claude to invent missing facts. | Retry 5 times when a detail isn't even in the document. | By try #3, Claude feels pressured and makes up a fake answer. | **Retry** fixable math/format mistakes with the exact error; **stop immediately** if the fact isn't in the doc. |
| **4.5** | **Bulk Nightly Jobs** | Save 50% on 50k nightly emails and handle CRM data & errors. | Batch live PR checks, re-run all 50k items on 20 errors, or use `custom_id` to trigger external jobs. | Batches take up to 24h (blocks PRs); re-running all wastes money; `custom_id` is just a label. | Batch **overnight/async jobs only**; **pre-fetch CRM data** into prompts; re-run **only failed `custom_id`s**. |
| **4.6** | **Catching Hard Bugs** | Fix regex/code edge cases when Claude keeps defending its first mistake. | Tell the same chat to try again, or split regex groups and check each alone. | Same chat stays biased; checking regex pieces alone misses how they interact. | Send **only the final code/regex + failed tests** to a **fresh, separate Claude instance** (no old reasoning). |

---

### 🛡️ Domain 5: Context Management & Reliability (15%)

| TS | Topic | 🎯 What the System Needs | ❌ Tempting Wrong Answer | 💥 Why It Breaks | ✅ Right Answer |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **5.1** | **Remembering Exact Details** | Keep exact order IDs and dollar amounts accurate in long chats. | Tell a summary prompt *"keep all IDs exact"*, or dump 50 raw CRM fields into chat. | Summaries still round `$149.99` to `~$150`; 50 raw fields flood memory. | Pin exact **Case Facts** at the **top** outside summaries; trim tool outputs with `PostToolUse`. |
| **5.2** | **Escalating to Humans** | Hand off angry/stuck users fast and avoid guessing duplicate accounts. | Quiz a user who asked for a human, or pick the newest `"John Smith"` account. | Frustrates users; guessing leaks or refunds the wrong person's account. | **Transfer right away** when asked or stuck; on duplicate names, **ask for email/order ID**. |
| **5.3** | **Handling Outages** | Finish a multi-source report even if 1 of 4 search APIs times out. | Crash the whole report, or return `[]` so the user thinks nothing was found. | Crashes waste completed work; `[]` lies about coverage. | Retry network blips locally; pass back structured error info; finish report with a **Coverage Note**. |
| **5.4** | **Long Coding Sessions** | Code for 90+ minutes without Claude forgetting project architecture. | Let raw file reads pile up in chat, or restart from scratch after a crash. | Chat fills up and Claude forgets rules; restarting loses hours of work. | Use **subagents** for noisy searches, save notes in **`scratchpad.md`**, and run **`/compact`**. |
| **5.5** | **Quality Spot-Checks** | Catch silent accuracy drops on rare forms (like handwritten notes). | Trust a `97%` overall score and only check answers with `< 80%` confidence. | A `97%` average can hide `58%` failure on rare forms, and confident hallucinations slip past. | Check accuracy **by document type**, and manually audit **5–10% random samples** (even high-confidence ones). |
| **5.6** | **Conflicting Sources** | Report biased or disagreeing sources honestly without making things up. | Average two numbers (`$1.2B` & `$1.4B` → `$1.3B`), or let Claude pick a winner from memory. | Averaging invents a fake number; picking a winner hides the other view. | Label source types, **show both claims side-by-side with dates/sources**, and show multi-year changes as a **timeline**. |

---

## 🎬 Part 4: All 6 Exam Scenarios — Scenario-Specific Traps

On the exam, **4 of these 6 real-world scenarios** are chosen. Always check the **speed/cost goal (SLA)** in the question!

### Scenario 1: Customer Support Bot
* **Goals:** Solve 80%+ issues, reply in **under 2.5 seconds** | **Tools:** `get_customer`, `lookup_order`, `process_refund`, `escalate_to_human`

| Problem in Question | ❌ Wrong Answer | 💥 Why It Fails Here | ✅ Right Answer |
| :--- | :--- | :--- | :--- |
| Skips ID check on refunds > $500 | Put *"NEVER refund without ID"* in bold in the prompt. | Users can trick Claude into skipping prompt rules. | Block `process_refund` in **app code / `PreToolUse` hook** until verified. |
| Calls `get_customer` instead of `lookup_order` | Train an ML router to pick the right tool. | Too slow for the `< 2.5s` speed goal and adds extra servers. | Write **clearer tool descriptions** with examples and boundaries. |
| User asks for a human agent | Ask 3 quick questions first to try solving it. | Annoys the user and breaks escalation rules. | **Transfer immediately** with a clean handoff summary. |
| 2 `"John Smith"` accounts found | Pick whichever account ordered most recently. | Risks refunding or exposing the wrong person's data. | **Ask the user** for an email, ZIP code, or order ID. |
| `get_customer` returns 55 raw fields | Keep all 55 fields in chat so nothing is lost. | Slows down replies and buries important details. | Trim to **4–5 fields** in `PostToolUse` and pin IDs in **Case Facts**. |

---

### Scenario 2: Writing Code with Claude Code
* **Goals:** Stay **under 40k tokens**, **0 guesswork** | **Tools:** `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`

| Problem in Question | ❌ Wrong Answer | 💥 Why It Fails Here | ✅ Right Answer |
| :--- | :--- | :--- | :--- |
| New devs don't have team rules | Put rules in `~/.claude/CLAUDE.md` and tell devs to copy it. | Home folders don't sync via Git. | Put rules in **project `./CLAUDE.md`** (`< 200` lines + `@import`). |
| Test rules needed for `**/*.test.tsx` in 30 folders | Copy `CLAUDE.md` into 30 folders, or put in root `CLAUDE.md`. | 30 copies get out of sync; root wastes tokens on non-test files. | Use **`.claude/rules/tests.md`** with **`paths: ["**/*.test.tsx"]`**. |
| Refactoring 25+ files across 4 services | Jump straight into editing files to save tokens. | Breaks imports across files and causes big rewrites. | Use **Plan Mode** first to map out the changes. *(Direct Edit is for 1-file fixes.)* |
| Task is vague (*"build auth service"*) | Tell Claude to *"assume standard industry practices."* | Breaks the `0 guesswork` rule and builds the wrong thing. | Use the **Interview Pattern** (ask multiple-choice questions) + **2–3 examples**. |
| Dependency skill dumps 30k tokens of logs | Run it in main chat and type `/clear` later. | Blows the `40k` token limit mid-task. | Set **`context: fork`** in `SKILL.md` so logs stay in a separate sandbox. |

---

### Scenario 3: Multi-Agent Research System
* **Goals:** Reply in **under 20 seconds**, **100% cited sources** | **Tools:** `Agent`, `search_web`, `analyze_doc`, `synthesize`

| Problem in Question | ❌ Wrong Answer | 💥 Why It Fails Here | ✅ Right Answer |
| :--- | :--- | :--- | :--- |
| 3 research topics take 45s total | Run helpers 1-by-1, or let helpers message each other. | 1-by-1 breaks the `< 20s` limit; helper-to-helper causes loops. | **1 Coordinator** launches **all 3 `Agent` calls in 1 turn** (allow `"Agent"`). |
| Helper agent forgets the user's goal | Assume helpers can read the main chat history. | Helpers start with an **empty memory (`[]`)**. | Coordinator must **copy all needed context** into each helper's prompt. |
| 1 of 4 search APIs times out | Return `[]`, OR crash the entire 4-source report. | `[]` pretends nothing exists; crashing wastes the other 3 sources. | Return structured error (`isError: true`), finish with the 3 sources + **Coverage Note**. |
| News site says `$1.2B`, blog says `$1.4B` | Let Claude pick the winner from memory, OR average to `$1.3B`. | Picking hides context; averaging invents a fake number. | Tag source types upstream; **show both side-by-side with citations**. |
| 2024 vs. 2026 numbers look different | Flag it as a contradiction between sources. | Different years show change over time, not a contradiction. | Keep **dates** on every claim and show them as a **timeline**. |

---

### Scenario 4: Developer Productivity Assistant
* **Goals:** Stay **under 15k search tokens**, **0 broken edits** | **Tools:** `Grep`, `Glob`, `Read`, `Edit`, `Write`

| Problem in Question | ❌ Wrong Answer | 💥 Why It Fails Here | ✅ Right Answer |
| :--- | :--- | :--- | :--- |
| Burns 60k tokens searching a big repo | Read all matching files upfront into memory. | Blows the `15k` budget immediately. | Search step-by-step: **`Glob` → `Grep` → `Read` (chunks)**. |
| `Edit` fails because code snippet appears 3 times | Retry the exact same `Edit` call 3 times. | Fails identically every time. | Include **more surrounding lines** to make it unique, or use **`Read + Write`**. |
| Wastes 12 turns probing internal APIs | Give Claude 20+ extra bash/curl tools. | Too many tools confuse Claude (keep **4–5 max**). | Expose static API docs as read-only **MCP Resources** (secrets in `${ENV_VAR}`). |
| Dev runs `git rebase` mid-session | Run `claude --resume` so Claude keeps old memory. | Old line numbers are wrong after rebase, causing broken edits. | Summarize verified facts and start a **fresh session**. |

---

### Scenario 5: Claude Code in CI/CD (GitHub Actions)
* **Goals:** Finish PR review in **under 3 minutes**, **0 frozen jobs** | **Tools:** `Bash`, Claude CLI (`-p`, `--output-format json`)

| Problem in Question | ❌ Wrong Answer | 💥 Why It Fails Here | ✅ Right Answer |
| :--- | :--- | :--- | :--- |
| CI job freezes until timeout | Run bare `claude`, or use fake flags (`--batch`, `CLAUDE_HEADLESS=true`). | Bare `claude` waits for keyboard input; fake flags fail. | Run **`claude -p` (`--print`)** + `--output-format json --json-schema`. |
| Want 50% cost savings on PR checks | Send blocking PR checks to the **Message Batches API**. | Batches take up to **24h**—developers can't wait 24h to merge! | Use **live API** for blocking PR checks; **Batches** for overnight audits only. |
| PR bot leaves annoying style nitpicks | Prompt *"be conservative and only report high-confidence bugs."* | Claude still flags noisy style issues. | Write **clear "report vs. skip" rules** and turn off noisy categories. |
| Single-pass 15-file review misses bugs | Use a bigger context window, or ask the same chat to self-review. | Bigger context still loses focus; same chat defends its own mistakes. | **Two-Pass Review** (per-file → cross-file) with a **fresh, separate reviewer**. |

---

### Scenario 6: Structured Data Extraction
* **Goals:** **85%+ auto-processed**, **0 made-up facts** | **Tools:** `tool_use`, `validate_schema`, Message Batches API

| Problem in Question | ❌ Wrong Answer | 💥 Why It Fails Here | ✅ Right Answer |
| :--- | :--- | :--- | :--- |
| Outputs plain text on weird medical notes | Add a 2nd AI to turn text into JSON, or set `temperature: 0`. | 2nd AI costs double and adds errors; `temp=0` doesn't force JSON. | Force JSON with **`tool_use` + `tool_choice` (`strict: true`)**. |
| Invents missing phone numbers / pros & cons | Make all fields `required`, OR make lists optional. | Required fields force fake guesses; optional lists skip `[]`. | Use **`["string", "null"]`** for text, **`[]`** for lists, **`"unclear"`** for ambiguous labels. |
| Retry loop spins on a missing doc page | Increase retries to 5 with *"Look harder!"* | Pressures Claude into making up a fake answer on try #3. | **Retry** format/math errors; **stop fast** if the fact isn't in the doc. |
| `97.5%` overall score hides `58%` failure on handwritten forms | Automate 100% and only review `< 80%` confidence. | Averages hide weak groups, and confident mistakes slip through. | Check accuracy **per doc type**, and audit **5–10% random samples** (even high-confidence). |
| 50k nightly emails need CRM lookup | Link Batch to CRM via `custom_id`, or re-run all 50k on 20 errors. | `custom_id` can't run jobs; re-running 50k wastes 99.9% money. | **Pre-fetch CRM data** into prompts; re-run **only failed `custom_id`s**. |

---

## ⚖️ Part 5: 50/50 Tie-Breakers (When Two Answers Both Look Good)

| Stuck Between... | Pick This One... | When... |
| :--- | :--- | :--- |
| **`[]` (empty list)** vs. **optional / `null` list** | **Always pick `[]`** | You are extracting a **list** (`pros`, `tags`). It clearly means *"checked, 0 found"* and won't crash `.map()`. |
| **`"unclear"`** vs. **`"neutral" + "unclear"`** | **Pick `"unclear"` alone** | The problem is **sarcasm or ambiguity**. Don't add extra `"neutral"` labels unless asked. |
| **`PreToolUse`** vs. **`PostToolUse`** | **`PreToolUse`** = block before<br>**`PostToolUse`** = clean after | Checking ID / $500 limit before running (`Pre`), vs. trimming 55 CRM fields down to 4 after (`Post`). |
| **Fresh Reviewer** vs. **Extended Thinking Self-Check** | **Always pick Fresh Reviewer** | Fixing bad code/regex from an earlier turn—a fresh instance has zero bias toward the old mistake. |
| **Plan Mode** vs. **Direct Edit** | **Plan Mode** = big/unclear<br>**Direct Edit** = small/clear | Refactoring 10+ files (`Plan`), vs. fixing a clear 1-file bug (`Direct`). |
| **`context: fork` Skill** vs. **Coordinator `Agent`** | **`context: fork`** = slash skill<br>**`Agent`** = multi-worker pipeline | Running a noisy Claude Code `/skill` cleanly (`fork`), vs. launching parallel workers in code (`Agent`). |
| **Message Batches** vs. **Live API + Prompt Cache** | **Batches** = overnight (24h ok)<br>**Live** = someone is waiting | Nightly 50k email job (`Batches` = 50% off), vs. blocking PR check or live support chat (`Live`). |
| **Retry with Error** vs. **Stop & Escalate** | **Retry** = bad format/math<br>**Stop** = fact missing in doc | Wrong date format or math slip (`Retry`), vs. info not written anywhere in the doc (`Stop`). |

---

## 🧪 Part 6: Fake vs. Real Commands & Crash Traps

Exam writers love inventing fake flags or mixing incompatible settings that crash with **HTTP 400**:

| Topic | ❌ Fake or Crashes (Cross Out Immediately) | ✅ Real & Safe (What Actually Works) |
| :--- | :--- | :--- |
| **Claude Code CI Flags** | `--batch`, `CLAUDE_HEADLESS=true`, `--non-interactive`, bare `claude` in CI | `claude -p` (`--print`), `--output-format json`, `--json-schema`, `--resume`, `--fork-session` |
| **Batch API** | `batch_tool_choice`, mid-batch webhooks, `custom_id` running external jobs | `custom_id` (simple ID string for matching results), pre-fetched data in prompt, retry failed IDs only |
| **Tool Choice** | `tool_choice: "required"` (OpenAI word), forcing a tool with `thinking` (**HTTP 400**) | `tool_choice: {"type": "auto"}`, `{"type": "any"}`, `{"type": "tool", "name": "..."}` (use `"auto"`/`"none"` with `thinking`) |
| **Extended Thinking** | Setting `temperature: 0`, `top_p`, or `top_k` with `thinking` (**HTTP 400**); deleting `thinking` blocks in chat history (**HTTP 400**) | Leave `temperature`/`top_p`/`top_k` **unset** when `thinking` is on; keep `thinking` blocks + `signature` untouched |
| **MCP Config** | Putting API keys in `.mcp.json`; putting team tools in `~/.claude.json` | Team tools in **`.mcp.json`** with **`${ENV_VAR}`**; personal tools in `~/.claude.json`; static docs as **MCP Resources** |

---

## ⏱️ Part 7: 10-Second Exam-Day Checklist

Before clicking "Next" on any question, ask:

1. **Need 100% guarantee (money, auth, JSON)?** → Cross out prompt warnings & `temperature: 0`; pick **code checks, `PreToolUse`, or `tool_choice`**.
2. **Claude stuck repeating its own mistake?** → Cross out same-chat retries; pick a **fresh, separate Claude instance**.
3. **See a weird flag or `thinking` + `temperature`/`tool`?** → Cross out fake flags (`--batch`, `required`) and **HTTP 400** combos.
4. **Data missing, sarcastic, or conflicting?** → Cross out guessing, averaging, or hiding errors; pick **`null` / `[]` / `"unclear"`, side-by-side citations, and Coverage Notes**.
