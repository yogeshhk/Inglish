"""Main translation pipeline — orchestrates all three tiers."""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from term_extractor import TermExtractor
from translator import LLMTranslator


@dataclass
class TranslationConfig:
    """
    Configuration for the translation pipeline.

    llm_provider: LLM backend to use.
        Options: "gemini" (default) | "groq" | "openai" | "anthropic" | "ollama" | "lmstudio"
    llm_model: Model name. If None, uses the provider default.
    llm_api_key: API key. If None, read from environment variable
        (GEMINI_API_KEY, GROQ_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY).
    """
    domain:          str            = "programming"
    target_language: str            = "hi"           # "hi" = Hindi, "mr" = Marathi
    llm_provider:    str            = "gemini"        # default provider
    llm_model:       Optional[str]  = None            # None → provider default
    llm_api_key:     Optional[str]  = None            # None → read from env
    temperature:     float          = 0.3


class InglishtranslationPipeline:
    """
    Three-tier Inglish translation pipeline.

    Tier 1 — Term Extraction & Guarding  (TermExtractor)
    Tier 2 — LLM Translation             (LLMTranslator via LLMAdapter)
    Tier 3 — Script output               (handled inside LLMTranslator prompt)

    Output keys:
        original_english        — unchanged input
        intermediate_bracketed  — input with [guarded terms]
        hinglish_roman          — code-mixed Roman script output
        hinglish_devanagari     — code-mixed Devanagari script output
        metadata                — domain, model, extracted terms, etc.
    """

    def __init__(self, config: TranslationConfig):
        self.config = config

        # Tier 1
        self.term_extractor = TermExtractor(config.domain)

        # Tier 2 — inject API key into environment if provided explicitly
        if config.llm_api_key:
            _KEY_ENV = {
                "gemini":    "GEMINI_API_KEY",
                "groq":      "GROQ_API_KEY",
                "openai":    "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
            }
            env_var = _KEY_ENV.get(config.llm_provider)
            if env_var:
                os.environ.setdefault(env_var, config.llm_api_key)

        self.translator = LLMTranslator(
            target_language=config.target_language,
            llm_provider=config.llm_provider,
            llm_model=config.llm_model,
            temperature=config.temperature,
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def translate(self, text: str, verbose: bool = False) -> Dict:
        """
        Translate a single English sentence to Inglish.

        Args:
            text:    English input text.
            verbose: Print each pipeline stage to stdout.

        Returns:
            Translation result dictionary.
        """
        if verbose:
            print(f"[1] Input:       {text}")

        # Tier 1 — extract and guard terms
        terms = self.term_extractor.extract_terms(text)
        if verbose:
            print(f"[2] Terms ({len(terms)}): {[t[0] for t in terms]}")

        guarded = self.term_extractor.guard_terms(text, terms)
        if verbose:
            print(f"[3] Guarded:     {guarded}")

        # Tier 2 — LLM translation
        translated = self.translator.translate(guarded)
        if verbose:
            print(f"[4] Roman:       {translated['roman']}")
            print(f"[5] Devanagari:  {translated['devanagari']}")

        return {
            "original_english":       text,
            "intermediate_bracketed": guarded,
            "hinglish_roman":         translated["roman"],
            "hinglish_devanagari":    translated["devanagari"],
            "metadata": {
                "domain":          self.config.domain,
                "target_language": self.config.target_language,
                "llm_provider":    self.config.llm_provider,
                "llm_model":       self.config.llm_model,
                "terms_extracted": len(terms),
                "technical_terms": [t[0] for t in terms],
            },
        }

    def translate_batch(self, texts: List[str], verbose: bool = False) -> List[Dict]:
        """Translate a list of sentences."""
        results = []
        for i, text in enumerate(texts):
            if verbose:
                print(f"\n=== [{i+1}/{len(texts)}] ===")
            results.append(self.translate(text, verbose=verbose))
        return results
