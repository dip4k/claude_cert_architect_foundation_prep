# MCP Chat

MCP Chat is a command-line interface application that enables interactive chat capabilities with AI models through the Anthropic API. The application supports document retrieval, command-based prompts, and extensible tool integrations via the MCP (Model Control Protocol) architecture.

## Prerequisites

- Python 3.9+
- Anthropic API Key

## Setup

### Step 1: Environment Variables
The application automatically inherits variables from the repository root `.env` file via `python-dotenv`:

```bash
ANTHROPIC_API_KEY="sk-ant-..."
CLAUDE_MODEL="claude-haiku-4-5"
USE_UV=1
```

### Step 2: Unified Workspace Execution
This project is configured as a member of the repository's root `uv` workspace. All dependencies are synchronized in the root `.venv`.

To run the application:

```bash
# From within this folder or repository root:
uv run main.py
```

Or using the shared root virtual environment directly:
```bash
# Windows
..\..\..\.venv\Scripts\python main.py

# Linux / WSL
../../../.venv/bin/python main.py
```

## Usage

### Basic Interaction

Simply type your message and press Enter to chat with the model.

### Document Retrieval

Use the @ symbol followed by a document ID to include document content in your query:

```
> Tell me about @deposition.md
```

### Commands

Use the / prefix to execute commands defined in the MCP server:

```
> /summarize deposition.md
```

Commands will auto-complete when you press Tab.

## Development

### Adding New Documents

Edit the `mcp_server.py` file to add new documents to the `docs` dictionary.

### Implementing MCP Features

To fully implement the MCP features:

1. Complete the TODOs in `mcp_server.py`
2. Implement the missing functionality in `mcp_client.py`

### Linting and Typing Check

There are no lint or type checks implemented.
