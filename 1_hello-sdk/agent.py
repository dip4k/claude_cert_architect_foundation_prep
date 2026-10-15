"""
Claude SDK Verification & Hello Agent Check

Verifies connectivity and authentication with Anthropic's Claude API client.
Equivalent to the following API curl request:

curl https://api.anthropic.com/v1/messages \
  --header "x-api-key: $ANTHROPIC_API_KEY" \
  --header "anthropic-version: 2023-06-01" \
  --header "content-type: application/json" \
  --data '{"model": "claude-haiku-4-5", "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello, world"}]}'
"""

import os
import sys
from dotenv import load_dotenv
import anthropic

# Load environment variables from .env if present
load_dotenv()


def verify_claude_client(model: str = "claude-haiku-4-5", prompt: str = "Hello, world") -> bool:
    """
    Sends a test message to Claude to verify API access and credentials.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[ERROR] ANTHROPIC_API_KEY is not set.")
        print("Please set ANTHROPIC_API_KEY in your environment or in a .env file.")
        return False

    print(f"Initializing Anthropic client (Key prefix: {api_key[:10]}...)...")
    client = anthropic.Anthropic(api_key=api_key)

    print(f"Sending verification request to Claude...")
    print(f" - Model: {model}")
    print(f" - Prompt: {prompt}")
    print(f" - Max Tokens: 1024")

    try:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        print("\n=== Verification Successful ===")
        print(f"Response ID  : {response.id}")
        print(f"Model Used   : {response.model}")
        print(f"Stop Reason  : {response.stop_reason}")
        print(f"Usage        : Input={response.usage.input_tokens} tokens, Output={response.usage.output_tokens} tokens")
        print("-" * 35 + " Response Text " + "-" * 35)

        for block in response.content:
            if block.type == "text":
                print(block.text)

        print("-" * 85)
        return True

    except anthropic.AuthenticationError as e:
        print(f"\n[FAILED] Authentication Error (401): Invalid API key.")
        print(f"Details: {e}")
        return False
    except anthropic.PermissionDeniedError as e:
        print(f"\n[FAILED] Permission Denied (403): Check model access permissions.")
        print(f"Details: {e}")
        return False
    except anthropic.NotFoundError as e:
        print(f"\n[FAILED] Resource Not Found (404): Model '{model}' may not be recognized or available.")
        print(f"Details: {e}")
        return False
    except anthropic.RateLimitError as e:
        print(f"\n[FAILED] Rate Limit Exceeded (429).")
        print(f"Details: {e}")
        return False
    except anthropic.APIConnectionError as e:
        print(f"\n[FAILED] Network Connection Error: Could not connect to Anthropic API.")
        print(f"Details: {e}")
        return False
    except anthropic.APIStatusError as e:
        print(f"\n[FAILED] API Status Error ({e.status_code}): {e.message}")
        return False
    except Exception as e:
        print(f"\n[FAILED] Unexpected error: {e}")
        return False


if __name__ == "__main__":
    # You can pass a custom model via CLI argument if desired: python agent.py [model_name]
    target_model = sys.argv[1] if len(sys.argv) > 1 else "claude-haiku-4-5"
    success = verify_claude_client(model=target_model)
    sys.exit(0 if success else 1)

