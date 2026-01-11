"""Translation modules for converting English to Indian languages."""

import re
from typing import Dict, Optional
from abc import ABC, abstractmethod


class BaseTranslator(ABC):
    """Abstract base class for translators."""
    
    def __init__(self, target_language: str = "hi"):
        """
        Initialize translator.
        
        Args:
            target_language: Target language code (hi=Hindi, mr=Marathi, etc.)
        """
        self.target_language = target_language
    
    @abstractmethod
    def translate(self, text: str) -> str:
        """Translate text to target language."""
        pass
    
    def validate_constraints(self, original: str, translated: str) -> bool:
        """Verify that bracketed terms are preserved."""
        original_terms = sorted(re.findall(r'\[([^\]]+)\]', original))
        translated_terms = sorted(re.findall(r'\[([^\]]+)\]', translated))
        return original_terms == translated_terms


class BaselineTranslator(BaseTranslator):
    """
    Simple rule-based translator (baseline approach).
    
    This is the simplest, crudest algorithm - uses direct word-to-word mapping
    with basic grammar rules for Hindi.
    """
    
    def __init__(self, target_language: str = "hi"):
        super().__init__(target_language)
        
        # Simple English to Hindi word mappings
        self.word_map = {
            # Articles
            'the': '',
            'a': 'ek',
            'an': 'ek',
            
            # Pronouns
            'this': 'yeh',
            'that': 'voh',
            'these': 'ye',
            'those': 've',
            'it': 'yeh',
            'he': 'voh',
            'she': 'voh',
            
            # Prepositions
            'in': 'mein',
            'on': 'par',
            'at': 'par',
            'to': 'ko',
            'of': 'ka',
            'from': 'se',
            'with': 'ke saath',
            'over': 'ke upar',
            
            # Verbs (basic forms)
            'is': 'hai',
            'are': 'hain',
            'was': 'tha',
            'were': 'the',
            'has': 'hai',
            'have': 'hain',
            'had': 'tha',
            'be': 'ho',
            'been': 'gaya',
            
            # Common verbs
            'create': 'banao',
            'creates': 'banata hai',
            'created': 'banaya',
            'use': 'upyog karo',
            'uses': 'upyog karta hai',
            'used': 'upyog kiya',
            'assign': 'assign karo',
            'assigned': 'assign kiya',
            'iterate': 'iterate karo',
            'iterates': 'iterate karta hai',
            'iterated': 'iterate kiya',
            'increment': 'badhao',
            'incremented': 'badhaya',
            'decrement': 'ghatao',
            
            # Common adjectives
            'each': 'har',
            'every': 'har',
            'all': 'sabhi',
            'first': 'pehla',
            'last': 'aakhri',
            'next': 'agla',
            'previous': 'pichla',
            
            # Conjunctions
            'and': 'aur',
            'or': 'ya',
            'but': 'lekin',
            'then': 'phir',
            'after': 'baad',
            'before': 'pehle',
            
            # Common nouns (non-technical)
            'value': 'value',
            'number': 'number',
            'name': 'naam',
            'time': 'samay',
            'way': 'tarika',
        }
        
        # Simple grammar rules
        self.grammar_rules = [
            # "X of Y" -> "Y ka X"
            (r'\[([^\]]+)\] of \[([^\]]+)\]', r'[\2] ka [\1]'),
            # "X in Y" -> "Y mein X"
            (r'\[([^\]]+)\] in \[([^\]]+)\]', r'[\2] mein [\1]'),
        ]
    
    def translate(self, text: str) -> str:
        """
        Simple rule-based translation.
        
        Strategy:
        1. Split into words
        2. Translate each word using dictionary
        3. Keep bracketed terms unchanged
        4. Apply simple grammar rules
        """
        # Protect bracketed terms
        bracketed_pattern = r'\[([^\]]+)\]'
        protected_terms = {}
        
        def protect_term(match):
            idx = len(protected_terms)
            placeholder = f"__PROTECTED_{idx}__"
            protected_terms[placeholder] = match.group(0)
            return placeholder
        
        protected_text = re.sub(bracketed_pattern, protect_term, text)
        
        # Translate word by word
        words = protected_text.split()
        translated_words = []
        
        for word in words:
            # Check if it's a protected term
            if word in protected_terms:
                translated_words.append(word)
                continue
            
            # Clean word (remove punctuation for lookup)
            clean_word = word.lower().strip('.,!?;:()')
            
            # Translate using dictionary
            if clean_word in self.word_map:
                translation = self.word_map[clean_word]
                if translation:  # Skip empty translations (like 'the')
                    translated_words.append(translation)
            else:
                # Keep unknown words as-is (might be technical terms)
                translated_words.append(word)
        
        # Join translated words
        result = ' '.join(translated_words)
        
        # Apply grammar rules
        for pattern, replacement in self.grammar_rules:
            result = re.sub(pattern, replacement, result)
        
        # Restore protected terms
        for placeholder, term in protected_terms.items():
            result = result.replace(placeholder, term)
        
        # Clean up extra spaces
        result = re.sub(r'\s+', ' ', result).strip()
        
        return result


class LLMTranslator(BaseTranslator):
    """
    LLM-based translator using OpenAI or Anthropic APIs.
    """
    
    def __init__(self, target_language: str = "hi", model: str = "gpt-3.5-turbo", 
                 api_key: Optional[str] = None):
        super().__init__(target_language)
        self.model = model
        self.api_key = api_key
        self.temperature = 0.3
        
        # Language name mapping
        self.lang_names = {
            'hi': 'Hindi',
            'mr': 'Marathi',
            'te': 'Telugu',
            'ta': 'Tamil',
            'bn': 'Bengali',
        }
    
    def translate(self, text: str) -> str:
        """
        Translate using LLM with constraint prompting.
        
        Note: This requires API keys to be set. Falls back to baseline if not available.
        """
        try:
            import openai
            
            if not self.api_key:
                print("Warning: No API key provided. Falling back to baseline translation.")
                baseline = BaselineTranslator(self.target_language)
                return baseline.translate(text)
            
            openai.api_key = self.api_key
            
            lang_name = self.lang_names.get(self.target_language, 'Hindi')
            
            system_prompt = f"""You are an expert technical translator to {lang_name}.

CRITICAL RULES:
1. Keep all text within [square brackets] EXACTLY unchanged
2. Do NOT translate, transliterate, or modify bracketed content
3. Do NOT add or remove brackets
4. Translate only non-bracketed text naturally to {lang_name}
5. Output in Devanagari script
6. Maintain technical tone
7. Use natural {lang_name} grammar

Example:
Input: "The [for loop] iterates over the [array]."
Output: "[for loop] [array] के ऊपर iterate करता है।"
"""
            
            user_prompt = f"""Translate to {lang_name}:
"{text}"

Remember: Keep all [bracketed] content exactly as-is."""
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=len(text.split()) * 3
            )
            
            return response.choices[0].message.content.strip()
            
        except ImportError:
            print("Warning: OpenAI package not installed. Falling back to baseline.")
            baseline = BaselineTranslator(self.target_language)
            return baseline.translate(text)
        except Exception as e:
            print(f"Warning: LLM translation failed ({e}). Falling back to baseline.")
            baseline = BaselineTranslator(self.target_language)
            return baseline.translate(text)