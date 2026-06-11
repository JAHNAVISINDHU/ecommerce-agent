"""
utils/llm_factory.py - Creates LLM instances based on available API keys.
Supports Anthropic Claude, OpenAI, and Ollama (local, no key needed).
"""

import os


def get_llm(temperature: float = 0.1):
    """
    Returns an LLM based on available environment variables.
    Priority: Anthropic → OpenAI → Ollama (local)
    """
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    openai_key = os.environ.get("OPENAI_API_KEY", "")

    if anthropic_key and anthropic_key not in ("your_anthropic_api_key_here", ""):
        try:
            from langchain_anthropic import ChatAnthropic
            print("✓ Using Anthropic Claude (claude-3-haiku-20240307)")
            return ChatAnthropic(
                model="claude-3-haiku-20240307",
                temperature=temperature,
                anthropic_api_key=anthropic_key,
            )
        except ImportError:
            print("  langchain-anthropic not installed, trying OpenAI...")

    if openai_key and openai_key not in ("your_openai_api_key_here", ""):
        try:
            from langchain_openai import ChatOpenAI
            print("✓ Using OpenAI (gpt-4o-mini)")
            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=temperature,
                openai_api_key=openai_key,
            )
        except ImportError:
            print("  langchain-openai not installed, trying Ollama...")

    # Fallback: Ollama local model
    try:
        from langchain_ollama import ChatOllama
        print("✓ Using Ollama local model (llama3.2) — no API key required")
        return ChatOllama(model="llama3.2", temperature=temperature)
    except ImportError:
        pass

    try:
        from langchain_community.llms import Ollama
        print("✓ Using Ollama (community) local model (llama3.2)")
        return Ollama(model="llama3.2", temperature=temperature)
    except ImportError:
        pass

    raise RuntimeError(
        "No LLM backend available. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY, "
        "or install Ollama and run `ollama pull llama3.2`."
    )
