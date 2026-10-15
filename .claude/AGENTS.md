# Claude Code Agents - Execution Guidelines

## ⚠️ CRITICAL: No Automated API-Calling Code

This repository contains practice code that makes API calls to Claude. 

### The Rule
**DO NOT execute Python scripts that make API calls to the Anthropic API.**

These scripts must only be run manually by the user in their terminal:
- `1_stop_reason/main.py`, `1_hello-sdk/agent.py` - Agent examples with tool use
- Any script importing `anthropic` and calling the API
- Any `domain{N}/ts_{N}_{M}_*/main.py` certification practice script (exam prep exercises, one per task statement)

## Why This Restriction Exists

1. **Token Budget Protection** - Each API call consumes tokens and costs money
2. **User Control** - Users should be aware of and monitor their API costs
3. **Learning Purpose** - This is a practice repo; users should manually run examples
4. **Cost Prevention** - Automated execution can quickly exhaust token budgets

## What You Can Do

### ✅ Safe to Automate
These commands are SAFE to run automatically:
```bash
pytest tests/                                    # Run tests
pytest tests/test_parser.py -v                  # Specific tests
black lib/ tests/                                # Format code
flake8 lib/ tests/                               # Lint code
mypy lib/sdk_parser_py/                          # Type check
python lib/sdk_parser_py/examples.py             # Simulated examples (no API calls)
```

### ❌ NEVER Automate
These commands MUST ONLY be run manually by the user:
```
python stop_reason/main.py                       # Makes API calls
python practice/*/main.py                        # Likely makes API calls
Any custom script using anthropic package
```

## Detecting API-Calling Code

Before executing any Python script, check:

1. **Does it import `anthropic`?**
   ```python
   import anthropic              # ⚠️ RED FLAG
   from anthropic import Anthropic  # ⚠️ RED FLAG
   ```

2. **Does it call `client.messages.create()`?**
   ```python
   response = await client.messages.create(...)  # ⚠️ RED FLAG
   response = client.messages.create(...)        # ⚠️ RED FLAG
   ```

3. **Does it use `.env` for API key?**
   ```python
   load_dotenv()                  # Might need API key
   api_key = os.environ.get("ANTHROPIC_API_KEY")  # ⚠️ RED FLAG
   ```

If ANY of these are present, it's an API-calling script. DO NOT RUN IT AUTOMATICALLY.

## Policy for Agents

### When User Asks You To...

**"Run this script"** or **"Execute main.py"**
- ✅ If it's a test or linting command → Run it
- ✅ If it's SDK parser examples → Run it (uses simulated data)
- ❌ If it's stop_reason/main.py → Refuse and explain
- ❌ If it's any script with anthropic imports → Refuse and explain

**"Test this agent"** or **"Try this example"**
- Show the code first
- Check for API calls
- If it makes API calls, tell user to run it manually
- Offer to explain what the code does

**"Debug the agent example"**
- Review the code
- Suggest fixes
- Tell user to run manually to test
- Suggest using replay_trail() to analyze previous runs

## Example Responses

### ✅ Good Response
```
I can see this script uses the anthropic package to make API calls.
To protect your token budget and keep you in control, this must be 
run manually in your terminal:

  source .venv/bin/activate
  python stop_reason/main.py

After running, you can analyze the results using replay_trail():

  from lib.response_logger import replay_trail
  replay_trail("trails/agent_trail.jsonl")
```

### ❌ Bad Response
```
[automatically executes the script]
```

## Key Files

- **EXECUTION_POLICY.md** - Detailed policy document
- **CLAUDE.md** - Project documentation with safety notes
- **stop_reason/main.py** - Example that makes API calls (manual execution only)
- **lib/response_logger/** - Tools for analyzing previous runs

## Token Budget

Users should monitor their API usage at:
https://console.anthropic.com/account/usage

Each execution of `stop_reason/main.py` costs ~$0.001-0.01 depending on:
- Number of turns in the agentic loop
- Length of prompts and responses
- Number of tool calls
- Model used (Haiku vs Sonnet vs Opus)

## Questions?

If you're unsure whether a script makes API calls:
1. Read the imports at the top
2. Search for `anthropic` in the file
3. Search for `messages.create`
4. Ask the user to confirm before running

When in doubt, **refuse to run it automatically** and explain why.

## Summary

```
✅ DO:
  - Run tests, linting, type checking automatically
  - Run simulated examples automatically
  - Explain what API-calling code does
  - Direct user to run API code manually
  - Suggest analyzing previous runs with replay_trail()

❌ DON'T:
  - Run stop_reason/main.py automatically
  - Run any script with anthropic imports automatically
  - Execute API-calling code without user running it manually
  - Ignore the token budget implications
```

---

**Last Updated:** 2024-09-14
**Status:** Active & Enforced for All Agents
