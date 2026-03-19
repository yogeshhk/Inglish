# -*- coding: utf-8 -*-
"""
Script conversion module — Tier 3 (post-processing) of the Inglish pipeline.

Converts Roman Hinglish ↔ Devanagari using a word-level lookup map.

Why a word-level map instead of ITRANS:
  ITRANS is designed for lossless Sanskrit encoding and behaves incorrectly
  for conversational Hindi:
    • It adds a virama at word boundaries: "karta" → कर्त (wrong) vs करता (right).
    • It converts digits: "0" → "०", which breaks sentinel keys used internally.

  The set of Hindi context words produced by the baseline translator is small
  and closed, so we map them directly. Unknown Latin tokens (English technical
  terms left by the hybrid pipeline) stay as Latin — correct code-mixing.

Roman → Devanagari (no external deps required):
  Pass 1 — stash glossary Devanagari behind sentinels (STX+index+ETX).
  Pass 2 — word-level Hindi/verb lookup via _ROMAN_TO_DEVA.
  Pass 3 — restore stashed Devanagari.

Devanagari → Roman (requires indic-transliteration):
  Devanagari spans are ITRANS-converted; Latin spans pass through unchanged.
"""

import re
from typing import Dict, Optional

try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate as _transliterate
    _INDIC_AVAILABLE = True
except ImportError:
    _INDIC_AVAILABLE = False
    sanscript      = None   # type: ignore[assignment]
    _transliterate = None   # type: ignore[assignment]


def _require_indic() -> None:
    if not _INDIC_AVAILABLE:
        raise ImportError(
            "The 'indic-transliteration' package is required for Devanagari→Roman "
            "conversion. Install it with:  pip install indic-transliteration"
        )


# ---------------------------------------------------------------------------
# Roman → Devanagari word map
# Sorted longest-first so multi-word phrases match before their components.
# ---------------------------------------------------------------------------

_ROMAN_TO_DEVA: Dict[str, str] = {
    # Numbers
    "ek": "एक", "do": "दो", "teen": "तीन", "chaar": "चार",
    "paanch": "पाँच", "chhe": "छह", "saat": "सात",
    "aath": "आठ", "nau": "नौ", "das": "दस", "shunya": "शून्य",

    # Pronouns — nominative
    "yeh": "यह", "voh": "वह", "ye": "ये", "ve": "वे",

    # Pronouns — oblique (longer phrases first)
    "iske khud ka": "इसके खुद का",
    "khud ka":      "खुद का",
    "iske":         "इसके",
    "is":           "इस",
    "us":           "उस",
    "in":           "इन",
    "un":           "उन",

    # Prepositions — multi-word
    "ke saath":   "के साथ",
    "ke upar":    "के ऊपर",
    "jab tak":    "जब तक",
    "kabhi nahi": "कभी नहीं",

    # Prepositions — single word
    "mein": "में", "par": "पर", "ko": "को", "ka": "का", "se": "से",

    # Linking verbs
    "hai": "है", "hain": "हैं", "tha": "था", "the": "थे",
    "ho": "हो", "gaya": "गया",

    # Auxiliary verb fragments
    "karta hai": "करता है",
    "karta tha": "करता था",
    "karo":      "करो",
    "kiya":      "किया",

    # Action verbs — multi-word
    "banata hai":        "बनाता है",
    "upyog karta hai":   "उपयोग करता है",
    "iterate karta hai": "iterate करता है",
    "jaari rehta hai":   "जारी रहता है",
    "ban jaata hai":     "बन जाता है",
    "upyog karo":        "उपयोग करो",
    "upyog kiya":        "उपयोग किया",
    "assign karo":       "असाइन करो",
    "assign kiya":       "असाइन किया",
    "iterate karo":      "iterate करो",
    "iterate kiya":      "iterate किया",

    # Action verbs — single
    "banao": "बनाओ", "banaya": "बनाया",
    "badhao": "बढ़ाओ", "badhaya": "बढ़ाया", "ghatao": "घटाओ",

    # Tech verb roots
    "return":  "रिटर्न",
    "store":   "स्टोर",
    "call":    "कॉल",
    "define":  "डिफाइन",
    "declare": "डिक्लेयर",
    "throw":   "थ्रो",
    "run":     "रन",
    "execute": "एग्जिक्यूट",

    # Adjectives
    "har": "हर", "sabhi": "सभी", "kai": "कई", "naya": "नया", "wahi": "वही",
    "pehla": "पहला", "aakhri": "आखिरी", "agla": "अगला", "pichla": "पिछला",

    # Conjunctions / adverbs
    "aur": "और", "ya": "या", "lekin": "लेकिन", "phir": "फिर",
    "baad": "बाद", "pehle": "पहले", "jab": "जब", "nahi": "नहीं",
    "bhi": "भी", "sirf": "सिर्फ", "hamesha": "हमेशा",

    # Common nouns
    "naam": "नाम", "samay": "समय", "tarika": "तरीका",
}

# Sorted by length descending so longer phrases match first
_ROMAN_SORTED = sorted(_ROMAN_TO_DEVA.items(), key=lambda x: len(x[0]), reverse=True)


class ScriptConverter:
    """
    Convert Roman Hinglish ↔ Devanagari.

    Roman → Devanagari  (no external package needed):
        Pass 1 — stash glossary Devanagari behind sentinels.
        Pass 2 — word-level lookup for Hindi / tech-verb tokens.
        Pass 3 — restore stashed Devanagari.
        Remaining Latin tokens stay as Latin (correct code-mixing).

    Devanagari → Roman  (requires indic-transliteration):
        Devanagari spans → ITRANS; Latin spans unchanged.
    """

    _SCHEME = {"itrans": "ITRANS", "hk": "HK", "velthuis": "VELTHUIS", "iast": "IAST"}

    def __init__(self, target_language: str = "hi"):
        self.target_language = target_language

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def devanagari_to_roman(self, text: str, scheme: str = "itrans") -> str:
        """Convert Devanagari → ITRANS Roman. Requires indic-transliteration."""
        _require_indic()
        src = getattr(sanscript, self._SCHEME.get(scheme, "ITRANS"))
        return _transliterate(text, sanscript.DEVANAGARI, src)

    def convert_mixed_text(
        self,
        text: str,
        to_format: str = "roman",
        term_devanagari_map: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        Convert Roman Hinglish to the requested script.

        Args:
            text:                Roman Hinglish string.
            to_format:           "roman" (default) or "devanagari".
            term_devanagari_map: {english_term: phonetic_devanagari} for guarded terms.
        """
        if to_format == "devanagari":
            return self._to_devanagari(text, term_devanagari_map or {})
        return self._to_roman(text)

    def generate_bilingual_output(
        self,
        english_input: str,
        translated_text: str,
        term_devanagari_map: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """Return both Roman and Devanagari from a single translated string."""
        has_deva = bool(re.search(r"[\u0900-\u097F]", translated_text))
        roman    = self._to_roman(translated_text) if has_deva else translated_text
        deva     = translated_text if has_deva else self._to_devanagari(
            translated_text, term_devanagari_map or {}
        )
        return {
            "original_english":    english_input,
            "hinglish_roman":      roman,
            "hinglish_devanagari": deva,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _to_devanagari(self, text: str, term_map: Dict[str, str]) -> str:
        """Three-pass Roman → Devanagari conversion."""
        placeholders: Dict[str, str] = {}

        def stash(deva: str) -> str:
            key = f"\x02{len(placeholders)}\x03"
            placeholders[key] = deva
            return key

        result = text

        # Pass 1: stash guarded tech-term Devanagari behind sentinels
        for term, deva in sorted(term_map.items(), key=lambda x: len(x[0]), reverse=True):
            pat = re.compile(
                r"(?<![^\s\x02\x03])" + re.escape(term) + r"(?![^\s\x02\x03.,!?;:])",
                re.IGNORECASE,
            )
            result = pat.sub(lambda _, d=deva: stash(d), result)

        # Pass 2: word-level Hindi / built-in tech-verb lookup
        for roman, deva in _ROMAN_SORTED:
            pat = re.compile(
                r"(?<![^\s\x02\x03])" + re.escape(roman) + r"(?=[.,!?;:\s]|$|\x02)",
                re.IGNORECASE,
            )
            result = pat.sub(deva, result)

        # Pass 3: restore stashed Devanagari
        for key, deva in placeholders.items():
            result = result.replace(key, deva)

        return result

    def _to_roman(self, text: str) -> str:
        """Convert Devanagari spans to ITRANS Roman; leave Latin unchanged."""
        if not re.search(r"[\u0900-\u097F]", text):
            return text   # no Devanagari — nothing to do
        _require_indic()
        parts = re.split(r"([\u0900-\u097F]+)", text)
        return "".join(
            self.devanagari_to_roman(p)
            if re.search(r"[\u0900-\u097F]", p) else p
            for p in parts
        )
