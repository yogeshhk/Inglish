"""Main translation pipeline."""

import os
from dataclasses import dataclass
from typing import Dict, Optional
from term_extractor import TermExtractor
from translator import LLMTranslator


@dataclass
class TranslationConfig:
    """Configuration for translation pipeline."""
    
    domain: str = "programming"
    target_language: str = "hi"
    llm_model: str = "llama-3.1-8b-instant"
    llm_api_key: Optional[str] = None
    temperature: float = 0.3


class InglishtranslationPipeline:
    """
    Main translation pipeline combining all components.
    
    Pipeline stages:
    1. Term Extraction - Identify technical terms from glossary
    2. Term Guarding - Add brackets around terms (intermediate output)
    3. LLM Translation - Translate non-bracketed text with grammar awareness
    4. Output - Return both Roman and Devanagari translations
    """
    
    def __init__(self, config: TranslationConfig):
        """
        Initialize translation pipeline.
        
        Args:
            config: Translation configuration
        """
        self.config = config
        
        self.term_extractor = TermExtractor(config.domain)
        
        api_key = config.llm_api_key or os.environ.get("GROQ_API_KEY")
        
        self.translator = LLMTranslator(
            target_language=config.target_language,
            api_key=api_key,
            model=config.llm_model,
            temperature=config.temperature,
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
        
        terms = self.term_extractor.extract_terms(text)
        if verbose:
            print(f"[2] Extracted {len(terms)} terms: {[t[0] for t in terms]}")
        
        guarded_text = self.term_extractor.guard_terms(text, terms)
        if verbose:
            print(f"[3] Guarded (intermediate): {guarded_text}")
        
        translated = self.translator.translate(guarded_text)
        if verbose:
            print(f"[4] Translated Roman: {translated['roman']}")
            print(f"[5] Translated Devanagari: {translated['devanagari']}")
        
        result = {
            "original_english": text,
            "intermediate_bracketed": guarded_text,
            "hinglish_roman": translated['roman'],
            "hinglish_devanagari": translated['devanagari'],
            "metadata": {
                "domain": self.config.domain,
                "target_language": self.config.target_language,
                "llm_model": self.config.llm_model,
                "terms_extracted": len(terms),
                "technical_terms": [t[0] for t in terms],
            },
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
