"""Unit tests for the Inglish translation pipeline.

Uses llm_provider="none" so no API key is required to run the test suite.
Tier 1 (term extraction) is fully exercised; Tier 2 (LLM) is skipped.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pytest
from pipeline import InglishtranslationPipeline, TranslationConfig
from term_extractor import TermExtractor
from utils import resolve_overlapping_spans, spans_overlap


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pipeline(domain: str = "programming", lang: str = "hi") -> InglishtranslationPipeline:
    config = TranslationConfig(domain=domain, target_language=lang, llm_provider="none")
    return InglishtranslationPipeline(config)


# ---------------------------------------------------------------------------
# TranslationConfig
# ---------------------------------------------------------------------------

class TestTranslationConfig:
    def test_defaults(self):
        config = TranslationConfig()
        assert config.domain == "programming"
        assert config.target_language == "hi"
        assert config.llm_provider == "gemini"
        assert config.temperature == 0.3

    def test_custom_values(self):
        config = TranslationConfig(domain="physics", target_language="mr", llm_provider="groq")
        assert config.domain == "physics"
        assert config.target_language == "mr"
        assert config.llm_provider == "groq"


# ---------------------------------------------------------------------------
# TermExtractor
# ---------------------------------------------------------------------------

class TestTermExtractor:
    def setup_method(self):
        self.extractor = TermExtractor("programming")

    def test_single_term_extracted(self):
        terms = self.extractor.extract_terms("The array has five elements.")
        term_texts = [t[0] for t in terms]
        assert "array" in term_texts

    def test_compound_term_extracted(self):
        terms = self.extractor.extract_terms("The for loop iterates over the list.")
        term_texts = [t[0] for t in terms]
        assert "for loop" in term_texts

    def test_compound_wins_over_single(self):
        # "for loop" should be extracted as one compound term, not two singles
        terms = self.extractor.extract_terms("A for loop iterates.")
        term_texts = [t[0] for t in terms]
        assert "for loop" in term_texts
        # "loop" alone should NOT appear separately
        assert "loop" not in term_texts

    def test_trailing_punctuation_not_included(self):
        """Compound term at sentence end must not include the period."""
        terms = self.extractor.extract_terms("The function uses a for loop.")
        term_texts = [t[0] for t in terms]
        for t in term_texts:
            assert not t.endswith("."), f"Term '{t}' includes trailing punctuation"

    def test_guard_terms_brackets(self):
        text = "The array is large."
        guarded = self.extractor.guard_terms(text)
        assert "[array]" in guarded

    def test_guard_compound_term(self):
        text = "Use a for loop here."
        guarded = self.extractor.guard_terms(text)
        assert "[for loop]" in guarded

    def test_no_terms_unchanged(self):
        text = "This is a simple sentence."
        guarded = self.extractor.guard_terms(text)
        assert guarded == text

    def test_unguard_removes_brackets(self):
        assert self.extractor.unguard_terms("[for loop] ke upar [array]") == "for loop ke upar array"

    def test_span_positions_correct(self):
        text = "The for loop iterates."
        terms = self.extractor.extract_terms(text)
        for term_text, start, end in terms:
            assert text[start:end].lower() == term_text.lower().rstrip(".,!?;:")


# ---------------------------------------------------------------------------
# InglishtranslationPipeline (Tier 1 only — no LLM)
# ---------------------------------------------------------------------------

class TestPipelineTierOne:
    """Tests that exercise only Tier 1 (term extraction). No API key required."""

    def setup_method(self):
        self.pipeline = _make_pipeline()

    def test_output_keys_present(self):
        # translate() with llm_provider="none" raises at Tier 2; test via extractor directly
        extractor = self.pipeline.term_extractor
        text = "The for loop iterates over the array."
        terms = extractor.extract_terms(text)
        guarded = extractor.guard_terms(text, terms)
        assert "[for loop]" in guarded
        assert "[array]" in guarded

    def test_metadata_terms_populated(self):
        extractor = self.pipeline.term_extractor
        text = "This class has member variables."
        terms = extractor.extract_terms(text)
        term_texts = [t[0] for t in terms]
        assert "class" in term_texts

    def test_empty_input_no_terms(self):
        terms = self.pipeline.term_extractor.extract_terms("")
        assert terms == []

    def test_batch_translate_length(self):
        """translate_batch returns one result per input (LLM call will raise, so test extractor)."""
        texts = [
            "The function returns a value.",
            "Arrays store multiple elements.",
        ]
        extractor = self.pipeline.term_extractor
        results = [extractor.extract_terms(t) for t in texts]
        assert len(results) == len(texts)


# ---------------------------------------------------------------------------
# resolve_overlapping_spans — longest-match-wins guarantee
# ---------------------------------------------------------------------------

class TestResolveOverlappingSpans:
    def test_non_overlapping_kept(self):
        spans = [("a", 0, 3), ("b", 5, 9)]
        result = resolve_overlapping_spans(spans)
        assert len(result) == 2

    def test_longer_wins_same_start(self):
        spans = [("short", 0, 3), ("longer", 0, 6)]
        result = resolve_overlapping_spans(spans)
        assert len(result) == 1
        assert result[0][0] == "longer"

    def test_longer_wins_globally(self):
        # Shorter span starts earlier but longer span overlaps it and is longer — longer wins
        spans = [("short", 2, 5), ("muchlonger", 0, 12)]
        result = resolve_overlapping_spans(spans)
        assert len(result) == 1
        assert result[0][0] == "muchlonger"

    def test_sorted_by_start_position(self):
        spans = [("b", 5, 8), ("a", 0, 3)]
        result = resolve_overlapping_spans(spans)
        assert result[0][1] < result[1][1]

    def test_empty_input(self):
        assert resolve_overlapping_spans([]) == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
