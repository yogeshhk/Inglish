# -*- coding: utf-8 -*-
"""Script conversion module for Roman and Devanagari output."""

import re
from typing import Dict, Optional

# ---------------------------------------------------------------------------
# Optional dependency – only needed for Devanagari → Roman conversion.
# The primary path (Roman → Devanagari) uses a direct word-level map and
# does NOT require this package.
# ---------------------------------------------------------------------------
try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate as _transliterate
    _INDIC_AVAILABLE = True
except ImportError:
    _INDIC_AVAILABLE = False
    sanscript   = None  # type: ignore[assignment]
    _transliterate = None  # type: ignore[assignment]


def _require_indic() -> None:
    if not _INDIC_AVAILABLE:
        raise ImportError(
            "The 'indic-transliteration' package is required for Devanagari→Roman "
            "conversion.  Install it with:  pip install indic-transliteration"
        )


# ---------------------------------------------------------------------------
# WHY a word-level map instead of ITRANS
# ---------------------------------------------------------------------------
# ITRANS is a lossless encoding for classical Sanskrit.  It differs from
# casual Indian-Roman in two critical ways:
#
#  1. Word-final 'a' suppression – ITRANS adds a virama (halant ्) at word
#     boundaries, so "karta" → कर्त (wrong) instead of करता (right).
#
#  2. Digit conversion – ITRANS maps 0→०, 1→१, … Our sentinel keys embed
#     index digits, so "\x020\x03" was being turned into "०" which then
#     failed to match during placeholder restoration.
#
# The solution: bypass ITRANS entirely.  The set of Hindi context words
# produced by BaselineTranslator.word_map is closed and small, so we map
# them directly.  Tech-verb roots that appear in the Roman output (e.g.
# "return", "store") are also included so they convert even when they were
# not extracted as standalone glossary terms from the original sentence.
# Unknown Latin tokens (English words the baseline left untranslated) stay
# as Latin – correct code-mixing behaviour.
# ---------------------------------------------------------------------------
_ROMAN_TO_DEVA: Dict[str, str] = {
    # ── Numbers ──────────────────────────────────────────────────────────────
    'ek': 'एक', 'do': 'दो', 'teen': 'तीन', 'chaar': 'चार',
    'paanch': 'पाँच', 'chhe': 'छह', 'saat': 'सात',
    'aath': 'आठ', 'nau': 'नौ', 'das': 'दस', 'shunya': 'शून्य',

    # ── Pronouns – nominative ──────────────────────────────────────────────
    'yeh': 'यह', 'voh': 'वह', 'ye': 'ये', 've': 'वे',

    # ── Pronouns – oblique (longest first matters for sort) ────────────────
    'iske khud ka': 'इसके खुद का',
    'khud ka':      'खुद का',
    'iske':         'इसके',
    'is':           'इस',
    'us':           'उस',
    'in':           'इन',
    'un':           'उन',

    # ── Prepositions – multi-word ─────────────────────────────────────────
    'ke saath':  'के साथ',
    'ke upar':   'के ऊपर',
    'jab tak':   'जब तक',
    'kabhi nahi':'कभी नहीं',

    # ── Prepositions – single word ────────────────────────────────────────
    'mein': 'में', 'par': 'पर', 'ko': 'को', 'ka': 'का', 'se': 'से',

    # ── Linking verbs ─────────────────────────────────────────────────────
    'hai': 'है', 'hain': 'हैं', 'tha': 'था', 'the': 'थे',
    'ho': 'हो', 'gaya': 'गया',

    # ── Auxiliary verb fragments ──────────────────────────────────────────
    # These survive after Pass-1 stashing splits compound verb phrases.
    # e.g. "return karta hai" → Pass-1 stashes "return" → "\x020\x03 karta hai"
    # → Pass-2 converts "karta hai" → "करता है"
    # → Pass-3 restores "\x020\x03" → "रिटर्न"
    # → final: "रिटर्न करता है"
    'karta hai': 'करता है',
    'karta tha': 'करता था',
    'karo':      'करो',
    'kiya':      'किया',

    # ── Action verbs – multi-word (must precede their components) ─────────
    'banata hai':        'बनाता है',
    'upyog karta hai':   'उपयोग करता है',
    'iterate karta hai': 'iterate करता है',
    'jaari rehta hai':   'जारी रहता है',
    'ban jaata hai':     'बन जाता है',
    'upyog karo':        'उपयोग करो',
    'upyog kiya':        'उपयोग किया',
    'assign karo':       'असाइन करो',
    'assign kiya':       'असाइन किया',
    'iterate karo':      'iterate करो',
    'iterate kiya':      'iterate किया',

    # ── Action verbs – single-word ─────────────────────────────────────────
    'banao':   'बनाओ', 'banaya':  'बनाया',
    'badhao':  'बढ़ाओ', 'badhaya': 'बढ़ाया', 'ghatao': 'घटाओ',

    # ── Tech verb roots (appear in Roman output but may not be in term_map) ─
    # These are the base forms produced by word_map (e.g. 'returns'→'return karta hai'
    # → after SOV reorder the 'return' is at end → needs Devanagari).
    'return':   'रिटर्न',
    'store':    'स्टोर',
    'call':     'कॉल',
    'define':   'डिफाइन',
    'declare':  'डिक्लेयर',
    'throw':    'थ्रो',
    'run':      'रन',
    'execute':  'एग्जिक्यूट',

    # ── Adjectives ────────────────────────────────────────────────────────
    'har': 'हर', 'sabhi': 'सभी', 'kai': 'कई', 'naya': 'नया', 'wahi': 'वही',
    'pehla': 'पहला', 'aakhri': 'आखिरी', 'agla': 'अगला', 'pichla': 'पिछला',

    # ── Conjunctions / adverbs ────────────────────────────────────────────
    'aur': 'और', 'ya': 'या', 'lekin': 'लेकिन', 'phir': 'फिर',
    'baad': 'बाद', 'pehle': 'पहले', 'jab': 'जब', 'nahi': 'नहीं',
    'bhi': 'भी', 'sirf': 'सिर्फ', 'hamesha': 'हमेशा',

    # ── Common nouns ──────────────────────────────────────────────────────
    'naam': 'नाम', 'samay': 'समय', 'tarika': 'तरीका',
}

# Pre-sort longest-first: ensures "iske khud ka" matches before "iske" and "ka".
_ROMAN_SORTED = sorted(_ROMAN_TO_DEVA.items(), key=lambda x: len(x[0]), reverse=True)


class ScriptConverter:
    """
    Convert Roman Hinglish ↔ Devanagari.

    Roman → Devanagari  (does NOT require indic-transliteration):
      Pass 1 – stash glossary tech-term Devanagari behind sentinels.
      Pass 2 – word-level lookup of Hindi/tech-verb tokens via _ROMAN_TO_DEVA.
      Pass 3 – restore stashed Devanagari.
      Remaining Latin tokens stay as Latin (correct code-mixing).

    Devanagari → Roman  (requires indic-transliteration):
      Devanagari spans are ITRANS-converted; Latin spans are left unchanged.
      Used only when the input already contains Devanagari (e.g. from an LLM).
    """

    _SCHEME = {'itrans': 'ITRANS', 'hk': 'HK', 'velthuis': 'VELTHUIS', 'iast': 'IAST'}

    def __init__(self, target_language: str = "hi"):
        self.target_language = target_language

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def devanagari_to_roman(self, text: str, scheme: str = "itrans") -> str:
        """Devanagari → ITRANS Roman (requires indic-transliteration)."""
        _require_indic()
        src = getattr(sanscript, self._SCHEME.get(scheme, 'ITRANS'))
        return _transliterate(text, sanscript.DEVANAGARI, src)

    # ------------------------------------------------------------------
    # Pipeline-facing methods
    # ------------------------------------------------------------------

    def convert_mixed_text(self, text: str,
                           to_format: str = "roman",
                           term_devanagari_map: Optional[Dict[str, str]] = None) -> str:
        """
        Convert Roman Hinglish to the requested script.

        Args:
            text:                Roman Hinglish string from the translator.
            to_format:           'roman' (default) or 'devanagari'.
            term_devanagari_map: {english_term_lower: phonetic_devanagari}
                                 Built from glossary entries for the current sentence.
        """
        if to_format == 'roman':
            return self._to_roman(text)
        if to_format == 'devanagari':
            return self._to_devanagari(text, term_devanagari_map or {})
        return text

    def generate_bilingual_output(self, english_input: str,
                                  translated_text: str,
                                  term_devanagari_map: Optional[Dict[str, str]] = None
                                  ) -> Dict[str, str]:
        """Return both Roman and Devanagari from a single translated string."""
        has_deva = bool(re.search(r'[\u0900-\u097F]', translated_text))
        roman    = self._to_roman(translated_text) if has_deva else translated_text
        deva     = translated_text if has_deva else self._to_devanagari(
            translated_text, term_devanagari_map or {}
        )
        return {
            'original_english':    english_input,
            'hinglish_roman':      roman,
            'hinglish_devanagari': deva,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _to_devanagari(self, text: str, term_map: Dict[str, str]) -> str:
        """
        Three-pass Roman → Devanagari conversion.

        Sentinel format: STX + decimal index + ETX  (\\x02N\\x03).
        Control chars cannot appear in normal text and are not matched by
        the word-regex in Pass 2.
        """
        placeholders: Dict[str, str] = {}

        def stash(deva: str) -> str:
            key = f'\x02{len(placeholders)}\x03'
            placeholders[key] = deva
            return key

        result = text

        # Pass 1: stash glossary tech-term Devanagari (longest term first)
        for term, deva in sorted(term_map.items(), key=lambda x: len(x[0]), reverse=True):
            pat = re.compile(
                r'(?<![^\s\x02\x03])' + re.escape(term) + r'(?![^\s\x02\x03.,!?;:])',
                re.IGNORECASE,
            )
            result = pat.sub(lambda _, d=deva: stash(d), result)

        # Pass 2: word-level map for Hindi words and tech-verb roots
        for roman, deva in _ROMAN_SORTED:
            pat = re.compile(
                r'(?<![^\s\x02\x03])' + re.escape(roman) + r'(?=[.,!?;:\s]|$|\x02)',
                re.IGNORECASE,
            )
            result = pat.sub(deva, result)

        # Pass 3: restore stashed Devanagari
        for key, deva in placeholders.items():
            result = result.replace(key, deva)

        return result

    def _to_roman(self, text: str) -> str:
        """
        Convert any Devanagari spans in a mixed string to ITRANS Roman.
        If the input contains no Devanagari (the common baseline case),
        return it unchanged without requiring indic-transliteration.
        """
        if not re.search(r'[\u0900-\u097F]', text):
            return text
        _require_indic()
        parts = re.split(r'([\u0900-\u097F]+)', text)
        return ''.join(
            self.devanagari_to_roman(p) if re.search(r'[\u0900-\u097F]', p) else p
            for p in parts
        )
