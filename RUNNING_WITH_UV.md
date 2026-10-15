# Running Scripts with UV - Import Fix Guide

> **Terminal Environment**: All commands in this guide must be run inside **WSL Ubuntu** (`wsl -d Ubuntu`). The repository path in WSL is `<repo-root>`.

## Problem

When running scripts with `uv`, you might get:
```
ModuleNotFoundError: No module named 'lib.response_logger'
```

This happens because the Python path doesn't include the repo root.

## Solution 1: Run from Repo Root (Recommended)

**Always run scripts from the repository root directory:**

```bash
# From repository root:
source .venv/bin/activate
python stop_reason/main.py
```

NOT from a subdirectory:
```bash
❌ cd stop_reason
❌ python main.py
```

## Solution 2: Use UV Run (Alternative)

UV can handle this automatically:

```bash
# From repository root:
uv run stop_reason/main.py
```

## Solution 3: Add Path Setup to Script (If Needed)

If you must run from a subdirectory, add this to the top of your script:

```python
import sys
import os

# Add repo root to Python path for imports
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Now imports will work
from lib.response_logger import ResponseTrail, get_agent_trail_path
```

## What Was Fixed

Created missing `__init__.py` files to make directories proper Python packages:

```
✅ lib/__init__.py                   - Makes lib a package
✅ stop_reason/__init__.py           - Already existed
✅ hello-world/__init__.py           - Makes hello-world a package
```

## Verification

Test the import:

```bash
# From repository root:
python3 -c "from lib.response_logger import ResponseTrail; print('✅ Works!')"
```

## Best Practices

### ✅ DO

```bash
# Run from repo root
$ python stop_reason/main.py

# Or use uv run
$ uv run stop_reason/main.py

# Or activate venv and run from root
$ source .venv/bin/activate
$ python stop_reason/main.py
```

### ❌ DON'T

```bash
# Don't change into subdirectory and run
❌ cd stop_reason
❌ python main.py

# Don't run without repo root in path
❌ python <repo-root>/stop_reason/main.py
```

## Full Working Example

```bash
# Setup
# From repository root:
source .venv/bin/activate

# Verify env
cat .env          # Check ANTHROPIC_API_KEY is set

# Run from repo root
python stop_reason/main.py

# Trails will be created at:
# <repo-root>/stop_reason/trails/agent_trail.jsonl

# Check results
ls -la stop_reason/trails/
cat stop_reason/trails/agent_trail.jsonl | head -20
```

## Python Path Resolution

When you run `python stop_reason/main.py` from the repo root:

```
Current Directory: <repo-root>
Python Path includes: ['.', '<repo-root>', ...]
                           ↑     ↑
                    Current dir (repo root)

Import: from lib.response_logger import ...
        ↓
        Looks in: <repo-root>/lib/response_logger/
        ✅ Found!
```

When you run `python main.py` from `stop_reason/`:

```
Current Directory: <repo-root>/stop_reason
Python Path includes: ['.', '<repo-root>/stop_reason', ...]
                           ↑     ↑
                    Current dir (stop_reason)

Import: from lib.response_logger import ...
        ↓
        Looks in: <repo-root>/stop_reason/lib/response_logger/
        ❌ Not found!
```

## Environment Variables

Make sure `.env` is in the repo root:

```bash
# Good - .env in repo root
<repo-root>/.env

# Script can find it when running from root
python stop_reason/main.py  # Finds ../../../.env
```

The `load_dotenv()` call in scripts looks for `.env` in the current working directory and parent directories.

## Summary

| Method | Command | Status |
|--------|---------|--------|
| **From Repo Root** | `python stop_reason/main.py` | ✅ Works |
| **UV Run** | `uv run stop_reason/main.py` | ✅ Works |
| **From Subdirectory** | `cd stop_reason && python main.py` | ❌ Fails |
| **Absolute Path** | `python /path/to/stop_reason/main.py` | ❌ Fails |

**Always run from repo root!** 🎯

---

If you still get import errors after these fixes:

1. Verify `lib/__init__.py` exists
2. Check you're running from repo root: `pwd`
3. Check Python path: `python3 -c "import sys; print(sys.path)"`
4. Try: `python3 -c "from lib.response_logger import ResponseTrail; print('OK')"`
