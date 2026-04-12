"""Unit tests for the DocGen translation pipeline.

Uses llm_provider="none" so no API key is required to run the test suite.
Tier 1 (term extraction) is fully exercised; Tier 2 (LLM) is skipped.

Run from src/:
    pytest docgen/test_docgen.py -v
"""

import sys
from pathlib import Path

# Ensure src/ is on the path so shared/ and docgen/ are importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from docgen.pipeline import InglishtranslationPipeline, TranslationConfig
from docgen.term_extractor import TermExtractor
from shared.utils import resolve_overlapping_spans, spans_overlap


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
        terms = self.extractor.extract_terms("A for loop iterates.")
        term_texts = [t[0] for t in terms]
        assert "for loop" in term_texts
        assert "loop" not in term_texts

    def test_trailing_punctuation_not_included(self):
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


# ---------------------------------------------------------------------------
# preprocess_for_translation — structured text flattening
# ---------------------------------------------------------------------------

from shared.utils import preprocess_for_translation


class TestPreprocessForTranslation:
    def test_plain_prose_unchanged(self):
        text = "Python generators are memory-efficient functions."
        assert preprocess_for_translation(text) == text

    def test_labeled_bullets_flattened(self):
        text = (
            "Key Aspects:\n"
            "Lazy Evaluation: Generators compute values on demand.\n"
            "Memory Efficiency: Ideal for large datasets."
        )
        result = preprocess_for_translation(text)
        # Should be prose, not retain the "Label: content" structure as-is
        assert "means that" in result
        assert "Lazy Evaluation" in result
        assert "Memory Efficiency" in result

    def test_header_incorporated_in_prose(self):
        text = (
            "Key Aspects of Generators:\n"
            "Lazy Evaluation: Values computed on demand.\n"
            "State Management: State is preserved between yields."
        )
        result = preprocess_for_translation(text)
        assert "Here are the key aspects of" in result

    def test_numbered_list_flattened(self):
        text = "Steps:\n1. First step here.\n2. Second step here.\n3. Third step here."
        result = preprocess_for_translation(text)
        assert "First step here" in result
        assert "Second step here" in result
        # Should not contain the raw "1." prefix
        assert "1." not in result

    def test_bullet_list_flattened(self):
        text = "Notes:\n- First bullet point.\n- Second bullet point.\n- Third bullet point."
        result = preprocess_for_translation(text)
        assert "First bullet point" in result
        assert "- " not in result

    def test_multiple_paragraphs_preserved(self):
        text = "First prose paragraph.\n\nSecond prose paragraph."
        result = preprocess_for_translation(text)
        assert "\n\n" in result
        parts = result.split("\n\n")
        assert len(parts) == 2

    def test_mixed_content_prose_plus_list(self):
        prose = "Python generators are useful."
        structured = (
            "Key Points:\n"
            "Lazy Eval: Computes on demand.\n"
            "Memory: Holds one item."
        )
        text = f"{prose}\n\n{structured}"
        result = preprocess_for_translation(text)
        parts = result.split("\n\n")
        assert len(parts) == 2
        assert parts[0] == prose          # prose unchanged
        assert "means that" in parts[1]   # list flattened

    def test_single_labeled_line_not_flattened(self):
        # A single "Label: content" line should NOT be converted — not enough to be a list
        text = "Lazy Evaluation: Generators compute on demand."
        result = preprocess_for_translation(text)
        # Single line = not a list, pass through unchanged
        assert result == text

    def test_empty_string(self):
        assert preprocess_for_translation("") == ""

    def test_connectors_added_between_items(self):
        text = (
            "Features:\n"
            "Speed: Very fast processing.\n"
            "Safety: Thread-safe by design.\n"
            "Simplicity: Easy to use API.\n"
            "Flexibility: Works with any data."
        )
        result = preprocess_for_translation(text)
        assert "Also," in result or "Furthermore," in result or "In addition," in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
