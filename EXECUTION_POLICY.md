# ⚠️ EXECUTION POLICY - Manual Code Execution Only

## Important: No Automated Code Execution

This is a **practice/learning repository** with examples that make **API calls to Claude**.

### The Rule
```
🚫 DO NOT run Python code automatically via agents or automated tools
✅ DO run Python code manually in your terminal
```

## Why This Matters

### API Calls Are Expensive
- Scripts like `stop_reason/main.py` make multiple API calls to Claude
- Each API call consumes tokens and incurs costs
- Automated execution can quickly exhaust your token budget
- Without monitoring, you could run up unexpected costs

### Token Budget Protection
- This repo is for learning and practice
- Unmonitored automated execution defeats the purpose
- You should understand what each script does before running it
- Manual execution gives you visibility and control

## What You Should Do

### ✅ SAFE - Manual Execution in WSL Ubuntu Terminal
Run scripts manually inside your WSL Ubuntu terminal (`wsl -d Ubuntu`):
```bash
$ uv run stop_reason/main.py
$ uv run lib/sdk_parser_py/examples.py
$ uv run hello-sdk/agent.py
```

### ✅ SAFE - Automated Testing & Code Quality (WSL Ubuntu)
These are safe to run offline in WSL Ubuntu because they don't make Claude API calls:
```bash
$ uv run pytest tests/
$ uv run black lib/ tests/
$ uv run flake8 lib/ tests/
$ uv run mypy lib/sdk_parser_py/
```

### ❌ UNSAFE - Automated Agent Execution
Don't do these:
```
❌ "Run the agent example"
❌ "Execute stop_reason/main.py"
❌ "Use /run on stop_reason/main.py"
❌ "/run python stop_reason/main.py"
```

## Script Categories

### 📋 Simulated Data (No API Calls) - Safe to Run
- `lib/sdk_parser_py/examples.py` - Parse SDK responses (simulated)
- `lib/sdk_parser_py/utils.py` - Token counting, formatting
- Any test file in `tests/`

**Cost:** None (uses simulated data)
**Execution:** Manual or automated (safe either way)

### 🔴 API Calls (Makes Claude Requests) - Manual Only
- `stop_reason/main.py` - Async agent with Pokemon & fortune tools
- `practice/*/main.py` (if they use the Claude API)
- Any custom script using `anthropic.AsyncAnthropic` or `anthropic.Anthropic`

**Cost:** ~$0.001-0.01 per run (depends on prompts and turns)
**Execution:** Manual in terminal ONLY

## Before Running Any Script

1. **Read the code** - Understand what it does
2. **Check for API calls** - Look for `anthropic.` imports or `client.messages.create()`
3. **Review the prompts** - What will Claude be processing?
4. **Understand the tools** - What can Claude call via tool use?
5. **Run manually** - Execute in your terminal, not via agent
6. **Monitor output** - Watch what happens and what gets logged
7. **Check your usage** - Review API usage at https://console.anthropic.com/account/usage

## Environment Setup

Before running any script:

```bash
# 1. Setup virtual environment
# From repository root:
source .venv/bin/activate

# 2. Create .env file from template
cp .env.example .env

# 3. Add your API key to .env
# Edit .env and set:
#   ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

# 4. Run script manually
python stop_reason/main.py
```

## Monitoring Your API Usage

After running scripts, check your usage:
- Go to https://console.anthropic.com/account/usage
- Review tokens consumed and costs
- Keep track of spending

## API Pricing (as of knowledge cutoff)

| Model | Input | Output |
|-------|-------|--------|
| Claude Opus 5 | ~$15/M tokens | ~$45/M tokens |
| Claude Sonnet 5 | ~$3/M tokens | ~$15/M tokens |
| Claude Haiku 4.5 | ~$0.80/M tokens | ~$4/M tokens |

*Check https://www.anthropic.com/pricing for current pricing*

## What Happens If You Break This Rule

If you ask an agent to run API-calling code:

1. **Token consumption** - Potentially multiple API calls per execution
2. **Unexpected costs** - Bills on your API account
3. **Quota exhaustion** - Faster depletion of your token budget
4. **Poor learning experience** - You don't understand what's happening
5. **Debugging difficulty** - Hard to track issues when execution is automated

## Best Practices

### ✅ DO
- Run examples manually in terminal
- Read code before executing
- Monitor API usage
- Keep `.env` out of git (it's already in .gitignore)
- Review trail logs after running agents
- Use simulated examples for testing

### ❌ DON'T
- Ask agents to run code
- Run unknown scripts
- Ignore your API usage
- Commit `.env` to version control
- Run scripts without understanding them
- Automate API-calling code

## Questions?

Before running any script, ask yourself:
1. **Does this script call the Claude API?**
   - Look for `anthropic.` imports or `client.messages.create()`
2. **Can I run it manually first?**
   - Yes? Do that. No? Contact maintainer.
3. **Do I understand what it will do?**
   - Confused? Read the code and comments first.
4. **Am I ready for the API costs?**
   - Budget-aware? Proceed. Unsure? Ask first.

## Summary

```
This is a LEARNING repository for Claude SDK and API practices.
Manual execution keeps you in control and aware.
Automated execution for API-calling code is dangerous to your token budget.

🎯 Run scripts manually in your terminal.
🎯 Understand what each script does before running.
🎯 Monitor your API usage and costs.
🎯 Keep your .env file safe and local.
```

---

**Last Updated:** 2024-09-14
**Status:** Active & Enforced
