"""Unit tests for the translation pipeline."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from pipeline import InglishtranslationPipeline, TranslationConfig


class TestTranslationPipeline:
    """Test cases for translation pipeline."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = TranslationConfig(
            domain="programming",
            target_language="hi",
            translator_type="baseline",
            output_format="both"
        )
        self.pipeline = InglishtranslationPipeline(self.config)
    
    def test_simple_translation(self):
        """Test basic translation."""
        text = "The for loop iterates over the array."
        result = self.pipeline.translate(text)
        
        assert "hinglish_roman" in result
        assert "hinglish_devanagari" in result
        assert "metadata" in result
        
        # Check technical terms preserved
        assert "for loop" in result["hinglish_roman"].lower()
        assert "array" in result["hinglish_roman"].lower()
    
    def test_term_preservation(self):
        """Test that technical terms are preserved."""
        text = "This class has member variables."
        result = self.pipeline.translate(text)
        
        terms = result["metadata"]["technical_terms"]
        output = result["hinglish_roman"]
        
        # All extracted terms should appear in output
        for term in terms:
            assert term.lower() in output.lower(), f"Term '{term}' not preserved"
    
    def test_batch_translation(self):
        """Test batch translation."""
        texts = [
            "The function returns a value.",
            "Arrays store multiple elements.",
            "Objects have instance variables."
        ]
        
        results = self.pipeline.translate_batch(texts)
        
        assert len(results) == len(texts)
        for result in results:
            assert "hinglish_roman" in result
            assert "metadata" in result
    
    def test_empty_input(self):
        """Test handling of empty input."""
        result = self.pipeline.translate("")
        
        assert result["hinglish_roman"] == ""
        assert result["metadata"]["terms_extracted"] == 0
    
    def test_no_technical_terms(self):
        """Test text with no technical terms."""
        text = "This is a simple sentence."
        result = self.pipeline.translate(text)
        
        # Should still produce output
        assert result["hinglish_roman"]
        # May have zero terms extracted
        assert result["metadata"]["terms_extracted"] >= 0
    
    def test_quality_metrics(self):
        """Test quality evaluation."""
        original = "The loop iterates over items."
        translated = "loop items ke upar iterate karta hai"
        
        metrics = self.pipeline.evaluate_quality(original, translated)
        
        assert "terminology_preservation" in metrics
        assert "length_ratio" in metrics
        assert 0 <= metrics["terminology_preservation"] <= 1
        assert metrics["length_ratio"] > 0


class TestTranslationConfig:
    """Test configuration handling."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = TranslationConfig()
        
        assert config.domain == "programming"
        assert config.target_language == "hi"
        assert config.translator_type == "baseline"
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = TranslationConfig(
            domain="physics",
            target_language="mr",
            translator_type="llm",
            output_format="roman"
        )
        
        assert config.domain == "physics"
        assert config.target_language == "mr"
        assert config.translator_type == "llm"
        assert config.output_format == "roman"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])