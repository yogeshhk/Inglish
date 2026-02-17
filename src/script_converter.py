# -*- coding: utf-8 -*-
"""Script conversion module for Roman and Devanagari output."""

import re
from typing import Dict, List, Optional

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate


class ScriptConverter:
    """Convert between Roman and Devanagari scripts using indic-transliteration."""

    SCHEMES = {
        "itrans": sanscript.ITRANS,
        "hk": sanscript.HK,
        "velthuis": sanscript.VELTHUIS,
        "iast": sanscript.IAST,
    }

    def __init__(self, target_language: str = "hi"):
        self.target_language = target_language

    # ------------------------------------------------------------------
    # Core methods
    # ------------------------------------------------------------------

    def roman_to_devanagari(self, text: str, scheme: str = "itrans") -> str:
        """ITRANS Roman → Devanagari (for pure Hindi words)."""
        src = self.SCHEMES.get(scheme, sanscript.ITRANS)
        return transliterate(text, src, sanscript.DEVANAGARI)

    def devanagari_to_roman(self, text: str, scheme: str = "itrans") -> str:
        """Devanagari → ITRANS Roman."""
        src = self.SCHEMES.get(scheme, sanscript.ITRANS)
        return transliterate(text, sanscript.DEVANAGARI, src)

    # ------------------------------------------------------------------
    # Pipeline-facing methods
    # ------------------------------------------------------------------

    def convert_mixed_text(self, text: str, to_format: str = "roman",
                           term_devanagari_map: Optional[Dict[str, str]] = None) -> str:
        """
        Convert Roman Hinglish text to the desired script.

        For 'devanagari':
          - English technical terms are replaced with their phonetic Devanagari
            form from term_devanagari_map (sourced from the glossary).
          - Remaining Hindi Roman words are ITRANS-transliterated.
          Result: fully Devanagari output with correct loanword rendering.

        For 'roman':
          - Devanagari spans (if any) are converted back to ITRANS Roman.
          - Latin/English spans are left unchanged.

        Args:
            text: Roman Hinglish string from the translator.
            to_format: 'roman' or 'devanagari'.
            term_devanagari_map: {english_term_lower: phonetic_devanagari}
                e.g. {"for loop": "फ़ॉर लूप", "array": "ऐरे", "integers": "इंटीजर्स"}
        """
        if to_format == "roman":
            return self._transliterate_devanagari_spans(text)
        elif to_format == "devanagari":
            return self._to_full_devanagari(text, term_devanagari_map or {})
        return text

    def generate_bilingual_output(self, english_input: str,
                                  translated_text: str,
                                  term_devanagari_map: Optional[Dict[str, str]] = None
                                  ) -> Dict[str, str]:
        """Generate both Roman and Devanagari outputs."""
        has_devanagari = bool(re.search(r'[\u0900-\u097F]', translated_text))
        if has_devanagari:
            devanagari = translated_text
            roman = self._transliterate_devanagari_spans(translated_text)
        else:
            roman = translated_text
            devanagari = self._to_full_devanagari(translated_text,
                                                   term_devanagari_map or {})
        return {
            "original_english": english_input,
            "hinglish_roman": roman,
            "hinglish_devanagari": devanagari,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _to_full_devanagari(self, text: str,
                             term_devanagari_map: Dict[str, str]) -> str:
        """
        Convert Roman Hinglish to fully Devanagari.

        Pass 1 — substitute English terms with their glossary Devanagari form,
                  stashing them behind null-byte sentinels so ITRANS won't touch them.
        Pass 2 — ITRANS-transliterate the remaining (Hindi Roman) words.
        Pass 3 — restore the Devanagari substitutions.

        Example:
          Input:  "for loop iterate karta hai ke upar array ka integers."
          Map:    {"for loop": "फ़ॉर लूप", "array": "ऐरे", "integers": "इंटीजर्स"}
          Output: "फ़ॉर लूप इटरेट करता है के ऊपर ऐरे का इंटीजर्स।"
        """
        placeholders: Dict[str, str] = {}

        def stash(devanagari_form: str) -> str:
            key = f"\x00{len(placeholders)}\x00"
            placeholders[key] = devanagari_form
            return key

        # Pass 1: longest terms first to avoid partial matches
        # ("for loop" must match before "loop")
        result = text
        for term, deva_form in sorted(term_devanagari_map.items(),
                                      key=lambda x: len(x[0]), reverse=True):
            pattern = re.compile(
                r'(?<![^\s\x00])' + re.escape(term) + r'(?![^\s\x00.,!?;:])',
                re.IGNORECASE
            )
            result = pattern.sub(lambda _m, d=deva_form: stash(d), result)

        # Pass 2: ITRANS-transliterate remaining Hindi Roman words
        result = self.roman_to_devanagari(result)

        # Pass 3: restore the Devanagari phonetic forms
        for key, deva_form in placeholders.items():
            result = result.replace(key, deva_form)

        return result

    def _transliterate_devanagari_spans(self, text: str) -> str:
        """
        Convert only Devanagari runs in a mixed string to ITRANS Roman,
        leaving Latin tokens untouched.
        """
        parts = re.split(r'([\u0900-\u097F]+)', text)
        return ''.join(
            self.devanagari_to_roman(p) if re.search(r'[\u0900-\u097F]', p) else p
            for p in parts
        )
