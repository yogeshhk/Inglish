"""Script conversion module for Roman and Devanagari output."""

import re
from typing import Dict


class ScriptConverter:
    """Convert between Roman and Devanagari scripts."""
    
    def __init__(self, target_language: str = "hi"):
        """
        Initialize script converter.
        
        Args:
            target_language: Target language code
        """
        self.target_language = target_language
        
        # Simple phonetic mapping (Devanagari to Roman)
        # For production, use indic-transliteration library
        self.devanagari_to_roman = {
            # Vowels
            'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ii', 'उ': 'u', 'ऊ': 'uu',
            'ऋ': 'ri', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
            
            # Consonants
            'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
            'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
            'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
            'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
            'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
            'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh',
            'ष': 'sh', 'स': 's', 'ह': 'h', 'क्ष': 'ksh', 'त्र': 'tra', 'ज्ञ': 'gya',
            
            # Vowel signs
            'ा': 'aa', 'ि': 'i', 'ी': 'ii', 'ु': 'u', 'ू': 'uu',
            'ृ': 'ri', 'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
            
            # Special
            '्': '', 'ं': 'm', 'ः': 'h', 'ँ': 'n',
            '।': '.', '॥': '..',
            
            # Numbers
            '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
            '५': '5', '६': '6', '७': '7', '८': '8', '९': '9',
        }
        
        # Reverse mapping for Roman to Devanagari (simplified)
        self.roman_to_devanagari = self._build_reverse_mapping()
    
    def _build_reverse_mapping(self) -> Dict[str, str]:
        """Build reverse mapping from Roman to Devanagari."""
        reverse = {}
        
        # For simplicity, we'll create basic mappings
        # In production, use a proper transliteration library
        mappings = {
            'aa': 'आ', 'a': 'अ',
            'ii': 'ई', 'i': 'इ',
            'uu': 'ऊ', 'u': 'उ',
            'ee': 'ई', 'e': 'ए',
            'oo': 'ऊ', 'o': 'ओ',
            'ai': 'ऐ', 'au': 'औ',
            
            'kh': 'ख', 'k': 'क',
            'gh': 'घ', 'g': 'ग',
            'chh': 'छ', 'ch': 'च',
            'jh': 'झ', 'j': 'ज',
            'th': 'थ', 't': 'त',
            'dh': 'ध', 'd': 'द',
            'ph': 'फ', 'p': 'प',
            'bh': 'भ', 'b': 'ब',
            
            'sh': 'श', 's': 'स',
            'h': 'ह', 'n': 'न', 'm': 'म',
            'y': 'य', 'r': 'र', 'l': 'ल',
            'v': 'व', 'w': 'व',
        }
        
        return mappings
    
    def devanagari_to_roman(self, text: str) -> str:
        """
        Convert Devanagari text to Roman script.
        
        Args:
            text: Text in Devanagari script
            
        Returns:
            Romanized text
        """
        result = []
        
        for char in text:
            if char in self.devanagari_to_roman:
                result.append(self.devanagari_to_roman[char])
            else:
                # Keep non-Devanagari characters (English, punctuation, etc.)
                result.append(char)
        
        return ''.join(result)
    
    def roman_to_devanagari_simple(self, text: str) -> str:
        """
        Convert Roman text to Devanagari (simplified).
        
        Note: This is a very basic implementation. For production,
        use indic-transliteration or AI4Bharat's Indic-Xlit.
        
        Args:
            text: Text in Roman script
            
        Returns:
            Devanagari text
        """
        # Protect English terms (typically in brackets or all-caps technical terms)
        protected_terms = {}
        
        def protect_english(match):
            idx = len(protected_terms)
            placeholder = f"__ENG_{idx}__"
            protected_terms[placeholder] = match.group(0)
            return placeholder
        
        # Protect bracketed terms and common English words
        text = re.sub(r'\[[^\]]+\]', protect_english, text)
        text = re.sub(r'\b[A-Z][a-z]+\b', protect_english, text)  # Capitalized words
        
        # Simple transliteration (this is very crude)
        result = text.lower()
        
        # Sort by length (descending) to match longer sequences first
        sorted_mappings = sorted(self.roman_to_devanagari.items(), 
                                key=lambda x: len(x[0]), reverse=True)
        
        for roman, devanagari in sorted_mappings:
            result = result.replace(roman, devanagari)
        
        # Restore protected terms
        for placeholder, term in protected_terms.items():
            result = result.replace(placeholder, term)
        
        return result
    
    def convert_mixed_text(self, text: str, to_format: str = "roman") -> str:
        """
        Convert mixed Hindi-English text to desired format.
        
        Args:
            text: Mixed language text
            to_format: 'roman' or 'devanagari'
            
        Returns:
            Converted text
        """
        if to_format == "roman":
            return self.devanagari_to_roman(text)
        elif to_format == "devanagari":
            return self.roman_to_devanagari_simple(text)
        else:
            return text
    
    def generate_bilingual_output(self, english_input: str, 
                                  translated_text: str) -> Dict[str, str]:
        """
        Generate output in multiple formats.
        
        Args:
            english_input: Original English text
            translated_text: Translated text (may be in Devanagari or Roman)
            
        Returns:
            Dictionary with different format outputs
        """
        # Detect if input is Devanagari
        has_devanagari = bool(re.search(r'[\u0900-\u097F]', translated_text))
        
        if has_devanagari:
            devanagari = translated_text
            roman = self.devanagari_to_roman(translated_text)
        else:
            roman = translated_text
            devanagari = self.roman_to_devanagari_simple(translated_text)
        
        return {
            "original_english": english_input,
            "hinglish_roman": roman,
            "hinglish_devanagari": devanagari,
        }
    
    def try_indic_transliteration(self, text: str, to_script: str = "roman") -> str:
        """
        Try to use the indic-transliteration library if available.
        Falls back to simple transliteration if not installed.
        
        Args:
            text: Input text
            to_script: Target script ('roman' or 'devanagari')
            
        Returns:
            Transliterated text
        """
        try:
            from indic_transliteration import sanscript
            from indic_transliteration.sanscript import transliterate
            
            if to_script == "roman":
                return transliterate(text, sanscript.DEVANAGARI, sanscript.ITRANS)
            else:
                return transliterate(text, sanscript.ITRANS, sanscript.DEVANAGARI)
                
        except ImportError:
            # Fall back to simple transliteration
            if to_script == "roman":
                return self.devanagari_to_roman(text)
            else:
                return self.roman_to_devanagari_simple(text)