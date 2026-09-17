"""
LLM provider abstraction — the only place that knows which concrete provider is in use.
`app/agent/graph.py`'s `explain` node calls only `get_llm()`, never a provider class
directly, so switching LLM_PROVIDER (local or remote) later is a config change here, not a
graph rewrite. See docs/specs/M5-langgraph-agent-orchestration.md.
"""
from __future__ import annotations

import os

from langchain_core.language_models.chat_models import BaseChatModel


def get_llm() -> BaseChatModel:
    provider = os.getenv("LLM_PROVIDER", "ollama")

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "llama3.1"),
            timeout=10,
        )

    raise ValueError(f"Unsupported LLM_PROVIDER: {provider!r}")
