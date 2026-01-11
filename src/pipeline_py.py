"""Main translation pipeline."""

from dataclasses import dataclass
from typing import Dict, Optional
from .term_extractor import TermExtractor
from .translator import BaselineTranslator, LLMTranslator
from .script_converter import ScriptConverter


@dataclass
class TranslationConfig:
    """Configuration for translation pipeline."""
    
    domain: str = "programming"
    target_language: str = "hi"
    translator_type: str = "baseline"  # 'baseline' or 'llm'
    output_format: str = "both"  # 'roman', 'devanagari', or 'both'
    llm_model: Optional[str] = "gpt-3.5-turbo"
    llm_api_key: Optional[str] = None
    temperature: float = 0.3


class InglishtranslationPipeline:
    """
    Main translation pipeline combining all components.
    
    Pipeline stages:
    1. Term Extraction - Identify technical terms
    2. Term Guarding - Add brackets around terms
    3. Translation - Translate non-bracketed text
    4. Validation - Verify constraints preserved
    5. Script Conversion - Generate Roman/Devanagari outputs
    """
    
    def __init__(self, config: TranslationConfig):
        """
        Initialize translation pipeline.
        
        Args:
            config: Translation configuration
        """
        self.config = config
        
        # Initialize components
        self.term_extractor = TermExtractor(config.domain)
        
        if config.translator_type == "llm":
            self.translator = LLMTranslator(
                target_language=config.target_language,
                model=config.llm_model,
                api_key=config.llm_api_key
            )
        else:
            self.translator = BaselineTranslator(
                target_language=config.target_language
            )
        
        self.script_converter = ScriptConverter(
            target_language=config.target_language
        )
    
    def translate(self, text: str, verbose: bool = False) -> Dict[str, str]:
        """
        Translate English text to Inglish (code-mixed output).
        
        Args:
            text: English input text
            verbose: Print intermediate steps
            
        Returns:
            Dictionary with translation outputs in different formats
        """
        if verbose:
            print(f"[1] Input: {text}")
        
        # Step 1: Extract technical terms
        terms = self.term_extractor.extract_terms(text)
        if verbose:
            print(f"[2] Extracted {len(terms)} terms: {[t[0] for t in terms]}")
        
        # Step 2: Guard terms with brackets
        guarded_text = self.term_extractor.guard_terms(text, terms)
        if verbose:
            print(f"[3] Guarded: {guarded_text}")
        
        # Step 3: Translate with constraints
        translated = self.translator.translate(guarded_text)
        if verbose:
            print(f"[4] Translated: {translated}")
        
        # Step 4: Validate constraints
        if not self.translator.validate_constraints(guarded_text, translated):
            if verbose:
                print("[!] Warning: Constraint validation failed!")
            # Could retry here with stronger constraints
        
        # Step 5: Remove brackets for final output
        final_text = self.term_extractor.unguard_terms(translated)
        if verbose:
            print(f"[5] Final: {final_text}")
        
        # Step 6: Generate outputs in requested formats
        result = {"original_english": text}
        
        if self.config.output_format in ["roman", "both"]:
            # If translated text is in Devanagari, convert to Roman
            result["hinglish_roman"] = self.script_converter.convert_mixed_text(
                final_text, to_format="roman"
            )
        
        if self.config.output_format in ["devanagari", "both"]:
            # If translated text is in Roman, keep/convert to Devanagari
            result["hinglish_devanagari"] = self.script_converter.convert_mixed_text(
                final_text, to_format="devanagari"
            )
        
        # Add metadata
        result["metadata"] = {
            "domain": self.config.domain,
            "target_language": self.config.target_language,
            "translator_type": self.config.translator_type,
            "terms_extracted": len(terms),
            "technical_terms": [t[0] for t in terms],
        }
        
        return result
    
    def translate_batch(self, texts: list, verbose: bool = False) -> list:
        """
        Translate multiple texts.
        
        Args:
            texts: List of English texts
            verbose: Print progress
            
        Returns:
            List of translation results
        """
        results = []
        
        for i, text in enumerate(texts):
            if verbose:
                print(f"\n=== Translating {i+1}/{len(texts)} ===")
            
            result = self.translate(text, verbose=verbose)
            results.append(result)
        
        return results
    
    def evaluate_quality(self, original: str, translated: str, 
                        reference: Optional[str] = None) -> Dict[str, float]:
        """
        Evaluate translation quality.
        
        Args:
            original: Original English text
            translated: Translated text
            reference: Reference translation (optional)
            
        Returns:
            Dictionary of quality metrics
        """
        from .utils import extract_bracketed_terms
        
        metrics = {}
        
        # Constraint preservation
        original_terms = self.term_extractor.extract_terms(original)
        original_term_set = set(t[0].lower() for t in original_terms)
        
        # Check if technical terms are preserved in translation
        preserved_count = sum(
            1 for term in original_term_set 
            if term.lower() in translated.lower()
        )
        
        if original_terms:
            metrics["terminology_preservation"] = preserved_count / len(original_term_set)
        else:
            metrics["terminology_preservation"] = 1.0
        
        # Length ratio (should be reasonable)
        metrics["length_ratio"] = len(translated.split()) / max(len(original.split()), 1)
        
        # If reference is provided, calculate BLEU (simplified)
        if reference:
            # Simple word overlap as proxy for BLEU
            trans_words = set(translated.lower().split())
            ref_words = set(reference.lower().split())
            overlap = len(trans_words & ref_words)
            metrics["word_overlap"] = overlap / max(len(ref_words), 1)
        
        return metrics