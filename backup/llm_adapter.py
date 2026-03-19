"""LLM abstraction layer — supports multiple providers with retry on 429."""

import os
import time
import random
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("MADS")

# Retry config for rate-limited providers (Groq free tier = 6000 TPM)
_MAX_RETRIES    = 6
_BASE_DELAY_S   = 5.0    # initial backoff seconds
_MAX_DELAY_S    = 60.0   # cap backoff at this
_JITTER_FACTOR  = 0.25   # ±25% jitter to avoid thundering herd


def _is_rate_limit_error(exc: Exception) -> bool:
    """Return True if the exception looks like an HTTP 429 rate-limit error."""
    msg = str(exc).lower()
    return "429" in msg or "rate_limit" in msg or "rate limit" in msg or "too many requests" in msg


class LLMAdapter:
    """Unified interface for different LLM providers."""

    def __init__(self, config: Dict[str, Any]):
        self.provider    = config.get("provider", "groq")
        self.model       = config.get("model",    "llama-3.3-70b-versatile")
        self.temperature = config.get("temperature", 0.1)
        self.max_tokens  = config.get("max_tokens",  800)   # keep low to save TPM
        self.base_url    = config.get("base_url", None)
        self._init_client()

    def _init_client(self):
        if self.provider == "ollama":
            try:
                import ollama
                self.client = ollama
            except ImportError:
                raise ImportError("pip install ollama")

        elif self.provider == "openai":
            try:
                from langchain_openai import ChatOpenAI
                self.client = ChatOpenAI(
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
            except ImportError:
                raise ImportError("pip install langchain-openai")

        elif self.provider == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
                self.client = ChatAnthropic(
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
            except ImportError:
                raise ImportError("pip install langchain-anthropic")

        elif self.provider == "groq":
            try:
                from langchain_groq import ChatGroq
                self.client = ChatGroq(
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
            except ImportError:
                raise ImportError("pip install langchain-groq")

        elif self.provider == "lmstudio":
            try:
                from langchain_openai import ChatOpenAI
                self.client = ChatOpenAI(
                    base_url=self.base_url or "http://localhost:1234/v1",
                    api_key="lm-studio",
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
            except ImportError:
                raise ImportError("pip install langchain-openai")

        elif self.provider == "openai_compatible":
            try:
                from langchain_openai import ChatOpenAI
                if not self.base_url:
                    raise ValueError("base_url required for openai_compatible provider")
                self.client = ChatOpenAI(
                    base_url=self.base_url,
                    api_key=os.getenv("OPENAI_API_KEY", "not-needed"),
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
            except ImportError:
                raise ImportError("pip install langchain-openai")

        else:
            raise ValueError(
                f"Unsupported provider: '{self.provider}'. "
                "Supported: ollama, openai, anthropic, groq, lmstudio, openai_compatible"
            )

    def generate(self, prompt: str) -> str:
        """
        Call the LLM and return the response string.

        For providers that hit rate limits (notably Groq free tier), retries
        automatically with exponential backoff + jitter up to _MAX_RETRIES times.
        Non-rate-limit errors are raised immediately.
        """
        if self.provider == "ollama":
            resp = self.client.generate(model=self.model, prompt=prompt)
            return resp["response"]

        # LangChain-based providers
        delay = _BASE_DELAY_S
        for attempt in range(_MAX_RETRIES + 1):
            try:
                return self.client.invoke(prompt).content
            except Exception as exc:
                if attempt == _MAX_RETRIES:
                    raise   # exhausted retries — propagate
                if not _is_rate_limit_error(exc):
                    raise   # non-429 error — propagate immediately

                # 429: wait with exponential backoff + jitter, then retry
                jitter  = delay * _JITTER_FACTOR * (2 * random.random() - 1)
                wait    = min(delay + jitter, _MAX_DELAY_S)
                logger.warning(
                    f"Rate limit (429) on attempt {attempt + 1}/{_MAX_RETRIES} — "
                    f"waiting {wait:.1f}s before retry"
                )
                time.sleep(wait)
                delay = min(delay * 2, _MAX_DELAY_S)   # exponential backoff

        # Should never reach here, but satisfy type checker
        raise RuntimeError("LLM generate() exhausted all retries without success")
