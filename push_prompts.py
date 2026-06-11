"""
push_prompts.py
Pushes all agent prompts to LangSmith Hub for centralized prompt management.
Run this once after setting up your LANGSMITH_API_KEY.
"""

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from prompts.prompts import (
    INTENT_CLASSIFIER_PROMPT,
    ORDER_STATUS_PROMPT,
    PRODUCT_QUERY_PROMPT,
    RETURN_AGENT_PROMPT,
    RECOMMENDATION_PROMPT,
    FALLBACK_PROMPT,
    save_prompts_to_files,
)


def push_to_hub():
    """Push all prompts to LangSmith Hub."""
    api_key = os.environ.get("LANGSMITH_API_KEY", "")
    hub_user = os.environ.get("LANGSMITH_HUB_USER", "")

    if not api_key or api_key == "your_langsmith_api_key_here":
        print("⚠️  LANGSMITH_API_KEY not set. Saving prompts locally instead.")
        save_prompts_to_files()
        return

    if not hub_user or hub_user == "your_langsmith_username":
        print("⚠️  LANGSMITH_HUB_USER not set. Saving prompts locally instead.")
        save_prompts_to_files()
        return

    try:
        from langchain import hub
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    except ImportError:
        print("langchain not installed. Run: pip install langchain")
        sys.exit(1)

    prompts_to_push = [
        ("intent-classifier-prompt", INTENT_CLASSIFIER_PROMPT),
        ("order-status-agent-prompt", ORDER_STATUS_PROMPT),
        ("product-query-agent-prompt", PRODUCT_QUERY_PROMPT),
        ("return-agent-prompt", RETURN_AGENT_PROMPT),
        ("recommendation-agent-prompt", RECOMMENDATION_PROMPT),
        ("fallback-agent-prompt", FALLBACK_PROMPT),
    ]

    for name, prompt_text in prompts_to_push:
        full_name = f"{hub_user}/{name}"
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", prompt_text),
                MessagesPlaceholder(variable_name="messages"),
            ])
            hub.push(full_name, prompt, new_repo_is_public=False)
            print(f"✓ Pushed: {full_name}")
        except Exception as e:
            print(f"✗ Failed to push {full_name}: {e}")

    # Also save locally
    save_prompts_to_files()
    print("\n✅ All prompts pushed to LangSmith Hub and saved locally.")


if __name__ == "__main__":
    push_to_hub()
