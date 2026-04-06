"""
Inglish Translator: Technical English to Indian Languages Translation Framework
"""

__version__ = "0.1.0"

from .pipeline import InglishtranslationPipeline, TranslationConfig
from .term_extractor import TermExtractor
from .translator import BaseTranslator, LLMTranslator
from .script_converter import ScriptConverter

__all__ = [
    "InglishtranslationPipeline",
    "TranslationConfig",
    "TermExtractor",
    "BaseTranslator",
    "LLMTranslator",
    "ScriptConverter",
]