#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of the Inglish Translation Pipeline.

Auto-detects which LLM provider to use from your environment variables.
Set one of: GROQ_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY
"""
import os
import sys
from pathlib import Path

# Fix console encoding on Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

sys.path.insert(0, str(Path(__file__).parent))

from docgen.pipeline import InglishtranslationPipeline, TranslationConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _separator(title: str = "") -> None:
    line = "=" * 60
    print(f"\n{line}")
    if title:
        print(title)
        print(line)


def _detect_provider() -> tuple:
    """Return (provider, model) based on whichever API key is set."""
    candidates = [
        ("groq",      "llama-3.1-8b-instant",    "GROQ_API_KEY"),
        ("gemini",    "gemini-2.0-flash",         "GEMINI_API_KEY"),
        ("gemini",    "gemini-2.0-flash",         "GOOGLE_API_KEY"),
        ("openai",    "gpt-4o-mini",              "OPENAI_API_KEY"),
        ("anthropic", "claude-3-5-haiku-20241022","ANTHROPIC_API_KEY"),
    ]
    for provider, model, env_var in candidates:
        if os.environ.get(env_var):
            return provider, model
    return "groq", "llama-3.1-8b-instant"   # fallback — will raise a clear error


# ---------------------------------------------------------------------------
# Examples
# ---------------------------------------------------------------------------

def example_simple_translation() -> None:
    """Single sentence with verbose pipeline trace."""
    _separator("Example 1: Simple Translation")

    provider, model = _detect_provider()
    print(f"Provider: {provider}   Model: {model}\n")

    config = TranslationConfig(
        domain="programming",
        target_language="hi",
        llm_provider=provider,
        llm_model=model,
    )
    pipeline = InglishtranslationPipeline(config)

    text = "The for loop iterates over the array of integers."
    try:
        result = pipeline.translate(text, verbose=True)
    except Exception as e:
        print(f"\n Translation failed: {e}")
        print("   Check that the correct API key environment variable is set.")
        return

    _separator("OUTPUT")
    print(f"Intermediate (bracketed): {result['intermediate_bracketed']}")
    print(f"Roman:                    {result['hinglish_roman']}")
    print(f"Devanagari:               {result['hinglish_devanagari']}")
    print(f"Terms preserved:          {result['metadata']['technical_terms']}")
    print("=" * 60)


def example_batch_translation() -> None:
    """Translate multiple sentences at once."""
    _separator("Example 2: Batch Translation")

    provider, model = _detect_provider()
    config = TranslationConfig(
        domain="programming",
        target_language="hi",
        llm_provider=provider,
        llm_model=model,
    )
    pipeline = InglishtranslationPipeline(config)

    texts = [
        "This class has four member variables.",
        "The function returns a boolean value.",
        "Each object has its own instance variables.",
    ]

    try:
        results = pipeline.translate_batch(texts, verbose=False)
    except Exception as e:
        print(f"\n Batch translation failed: {e}")
        return

    _separator("BATCH OUTPUT")
    for i, (text, result) in enumerate(zip(texts, results), 1):
        print(f"\n[{i}] English:   {text}")
        print(f"     Bracketed: {result['intermediate_bracketed']}")
        print(f"     Roman:     {result['hinglish_roman']}")
    print("=" * 60)


def example_provider_comparison() -> None:
    """Show available providers and which keys are set."""
    _separator("Example 3: Provider Overview")

    rows = [
        ("gemini",    "gemini-2.0-flash",          "GEMINI_API_KEY"),
        ("groq",      "llama-3.1-8b-instant",      "GROQ_API_KEY"),
        ("openai",    "gpt-4o-mini",               "OPENAI_API_KEY"),
        ("anthropic", "claude-3-5-haiku-20241022", "ANTHROPIC_API_KEY"),
        ("ollama",    "llama3.1",                  "(none)"),
        ("lmstudio",  "local-model",               "(none)"),
    ]

    print("\nAvailable LLM providers:\n")
    for provider, model, env_var in rows:
        key_set = "set" if os.environ.get(env_var) else "not set"
        print(f"  {provider:12s}  {model:38s}  {env_var}  [{key_set}]")

    print("\nTo switch provider, change TranslationConfig:")
    print("  config = TranslationConfig(llm_provider='groq', llm_model='llama-3.1-8b-instant')")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    _separator("INGLISH TRANSLATOR -- USAGE EXAMPLES")

    provider, model = _detect_provider()
    key_found = any(
        os.environ.get(k)
        for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY",
                  "OPENAI_API_KEY", "ANTHROPIC_API_KEY")
    )

    if not key_found:
        print("\n  No LLM API key found in environment.")
        print("   Set one of these before running:\n")
        print("     set GROQ_API_KEY=your_key        (free, fast -- recommended)")
        print("     set GEMINI_API_KEY=your_key      (Google Gemini)")
        print("     set OPENAI_API_KEY=your_key")
        print("     set ANTHROPIC_API_KEY=your_key\n")
        print("   Get a free Groq key at: https://console.groq.com\n")
    else:
        print(f"\n  Using provider: {provider}  (model: {model})\n")

    example_simple_translation()
    example_batch_translation()
    example_provider_comparison()

    print("\nAll examples complete.\n")


if __name__ == "__main__":
    main()
