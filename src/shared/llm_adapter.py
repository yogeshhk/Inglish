"""
LLM abstraction layer — uses native SDKs only, no LangChain dependency.

Supported providers:
  groq           — Groq native SDK  (pip install groq)
  gemini         — Google Gemini    (pip install google-generativeai)
  openai         — OpenAI native    (pip install openai)
  anthropic      — Anthropic native (pip install anthropic)
  ollama         — Local Ollama     (pip install ollama)
  lmstudio       — LM Studio local  (pip install openai)
  openai_compatible — Any OpenAI-compatible endpoint (pip install openai)

Rate-limit handling: exponential backoff with jitter for 429 errors.
"""

import os
import time
import random
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Retry config
# ---------------------------------------------------------------------------
_MAX_RETRIES   = 6
_BASE_DELAY_S  = 5.0
_MAX_DELAY_S   = 60.0
_JITTER_FACTOR = 0.25  # ±25% jitter


def _is_rate_limit(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(k in msg for k in ("429", "rate_limit", "rate limit", "too many requests"))


def _wait_with_backoff(attempt: int, delay: float) -> float:
    """Sleep with jitter and return next delay (doubled)."""
    jitter = delay * _JITTER_FACTOR * (2 * random.random() - 1)
    wait   = min(delay + jitter, _MAX_DELAY_S)
    logger.warning("Rate limit — attempt %d/%d, waiting %.1fs", attempt + 1, _MAX_RETRIES, wait)
    time.sleep(wait)
    return min(delay * 2, _MAX_DELAY_S)


# ---------------------------------------------------------------------------
# Default models per provider
# ---------------------------------------------------------------------------
_DEFAULT_MODELS: Dict[str, str] = {
    "groq":              "llama-3.1-8b-instant",
    "gemini":            "gemini-2.0-flash",
    "openai":            "gpt-4o-mini",
    "anthropic":         "claude-3-5-haiku-20241022",
    "ollama":            "llama3.1",
    "lmstudio":          "local-model",
    "openai_compatible": "local-model",
    "none":              "",   # no-op provider for baseline/rule-only mode
}

_SUPPORTED_PROVIDERS = set(_DEFAULT_MODELS)


class LLMAdapter:
    """
    Unified LLM interface using native provider SDKs (no LangChain).

    Usage:
        adapter = LLMAdapter({"provider": "groq"})
        text = adapter.generate("Translate this...")
    """

    def __init__(self, config: Dict[str, Any]):
        self.provider    = config.get("provider", "groq")
        self.model       = config.get("model") or _DEFAULT_MODELS.get(self.provider, "")
        self.temperature = config.get("temperature", 0.3)
        self.max_tokens  = config.get("max_tokens", 1024)
        self.base_url    = config.get("base_url")
        self._client     = None
        self._init_client()

    # ------------------------------------------------------------------
    # Initialisation — one method per provider, native SDK only
    # ------------------------------------------------------------------

    def _init_client(self) -> None:
        if self.provider == "none":
            return  # no-op — used for baseline/rule-only mode; generate() will raise if called
        elif self.provider == "groq":
            self._init_groq()
        elif self.provider == "gemini":
            self._init_gemini()
        elif self.provider in ("openai", "lmstudio", "openai_compatible"):
            self._init_openai_compatible()
        elif self.provider == "anthropic":
            self._init_anthropic()
        elif self.provider == "ollama":
            self._init_ollama()
        else:
            raise ValueError(
                f"Unsupported provider '{self.provider}'. "
                f"Choose from: {', '.join(sorted(_SUPPORTED_PROVIDERS))}"
            )

    def _init_groq(self) -> None:
        try:
            from groq import Groq  # type: ignore
        except ImportError:
            raise ImportError("pip install groq")
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY environment variable not set.")
        self._client = Groq(api_key=api_key)

    def _init_gemini(self) -> None:
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError:
            raise ImportError("pip install google-generativeai")
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)
        self._client = genai.GenerativeModel(
            model_name=self.model,
            generation_config=genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            ),
        )

    def _init_openai_compatible(self) -> None:
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            raise ImportError("pip install openai")

        if self.provider == "openai":
            api_key  = os.getenv("OPENAI_API_KEY", "")
            base_url = self.base_url  # None = use OpenAI default
        elif self.provider == "lmstudio":
            api_key  = "lm-studio"
            base_url = self.base_url or "http://localhost:1234/v1"
        else:  # openai_compatible
            if not self.base_url:
                raise ValueError("base_url required for 'openai_compatible' provider.")
            api_key  = os.getenv("OPENAI_API_KEY", "not-needed")
            base_url = self.base_url

        self._client = OpenAI(api_key=api_key, base_url=base_url)

    def _init_anthropic(self) -> None:
        try:
            import anthropic  # type: ignore
        except ImportError:
            raise ImportError("pip install anthropic")
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY environment variable not set.")
        self._client = anthropic.Anthropic(api_key=api_key)

    def _init_ollama(self) -> None:
        try:
            import ollama  # type: ignore
            self._client = ollama
        except ImportError:
            raise ImportError("pip install ollama")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate(self, prompt: str) -> str:
        """Call the LLM and return response text. Retries on 429."""
        if self.provider == "none":
            raise RuntimeError(
                "LLMAdapter was initialised with provider='none' (baseline/rule-only mode). "
                "Call translate() only when an LLM provider is configured."
            )
        if self.provider == "gemini":
            return self._generate_gemini(prompt)
        if self.provider == "ollama":
            return self._client.generate(model=self.model, prompt=prompt)["response"]
        if self.provider == "anthropic":
            return self._generate_anthropic(prompt)
        # groq, openai, lmstudio, openai_compatible — all use OpenAI-style chat API
        return self._generate_openai_style(prompt)

    # ------------------------------------------------------------------
    # Provider generate implementations
    # ------------------------------------------------------------------

    def _generate_openai_style(self, prompt: str) -> str:
        """Works for Groq, OpenAI, LM Studio, openai_compatible."""
        delay = _BASE_DELAY_S
        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = self._client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                return resp.choices[0].message.content
            except Exception as exc:
                if attempt == _MAX_RETRIES or not _is_rate_limit(exc):
                    raise
                delay = _wait_with_backoff(attempt, delay)
        raise RuntimeError("generate() exhausted retries")

    def _generate_gemini(self, prompt: str) -> str:
        delay = _BASE_DELAY_S
        for attempt in range(_MAX_RETRIES + 1):
            try:
                return self._client.generate_content(prompt).text
            except Exception as exc:
                if attempt == _MAX_RETRIES or not _is_rate_limit(exc):
                    raise
                delay = _wait_with_backoff(attempt, delay)
        raise RuntimeError("Gemini generate() exhausted retries")

    def _generate_anthropic(self, prompt: str) -> str:
        delay = _BASE_DELAY_S
        for attempt in range(_MAX_RETRIES + 1):
            try:
                msg = self._client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )
                return msg.content[0].text
            except Exception as exc:
                if attempt == _MAX_RETRIES or not _is_rate_limit(exc):
                    raise
                delay = _wait_with_backoff(attempt, delay)
        raise RuntimeError("Anthropic generate() exhausted retries")
