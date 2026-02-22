"""Translation modules for converting English to Indian languages."""

import re
import sys
from abc import ABC, abstractmethod
from typing import Dict, Optional


class BaseTranslator(ABC):
    """Abstract base class for translators."""

    def __init__(self, target_language: str = "hi"):
        self.target_language = target_language

    @abstractmethod
    def translate(self, text: str) -> str:
        """Translate text to target language."""
        pass

    def validate_constraints(self, original: str, translated: str) -> bool:
        """Verify that bracketed terms are preserved."""
        original_terms  = sorted(re.findall(r'\[([^\]]+)\]', original))
        translated_terms = sorted(re.findall(r'\[([^\]]+)\]', translated))
        return original_terms == translated_terms


class BaselineTranslator(BaseTranslator):
    """
    Rule-based English → Hinglish translator (baseline approach).

    Pipeline (all steps work on already-guarded text received from the pipeline):
      1. Pre-grammar rules   – structural rewrites on raw English constructs
                               (e.g. "X has Y" → "X mein Y hain").
      2. Protect [brackets]  – guarded technical terms become __P0__ placeholders.
      3. Word substitution   – each non-placeholder word is looked up in word_map.
      4. SOV reorder         – if a multi-word verb phrase sits mid-sentence,
                               move it to the end (English SVO → Hindi SOV).
      5. Restore [brackets]  – placeholders become [term] again.
    """

    # Verb phrases that should appear at sentence-end in Hindi.
    # Sorted longest-first so the most specific phrase is tried first.
    _SOV_VERBS = sorted([
        'return karta hai', 'store karta hai', 'contain karta hai',
        'banata hai',       'upyog karta hai', 'iterate karta hai',
        'extend karta hai', 'implement karta hai', 'call karta hai',
        'jaari rehta hai',  'ban jaata hai',   'define karta hai',
        'declare karta hai','throw karta hai', 'run karta hai',
        'execute karta hai',
    ], key=len, reverse=True)

    def __init__(self, target_language: str = "hi"):
        super().__init__(target_language)

        self.word_map: Dict[str, str] = {
            # Articles
            'the': '', 'a': 'ek', 'an': 'ek',

            # Pronouns – oblique forms are natural before postpositions
            # ("is class mein" = "in this class", not "yeh class mein")
            'this': 'is',   # oblique of yeh
            'that': 'us',   # oblique of voh
            'these': 'in',  # oblique plural
            'those': 'un',  # oblique plural
            'it': 'yeh', 'he': 'voh', 'she': 'voh', 'its': 'iske',

            # Prepositions
            'in': 'mein', 'on': 'par', 'at': 'par', 'to': 'ko',
            'of': 'ka',   'from': 'se', 'with': 'ke saath', 'over': 'ke upar',
            'until': 'jab tak',

            # Linking verbs
            # NOTE: 'has' is intentionally absent – handled by the possession
            # grammar rule which converts "Subject has Object" → "Subject mein Object hain".
            'is': 'hai', 'are': 'hain', 'was': 'tha', 'were': 'the',
            'have': 'hain', 'had': 'tha', 'be': 'ho', 'been': 'gaya',

            # Number words
            'zero': 'shunya', 'one': 'ek',  'two': 'do',    'three': 'teen',
            'four': 'chaar',  'five': 'paanch', 'six': 'chhe', 'seven': 'saat',
            'eight': 'aath',  'nine': 'nau',    'ten': 'das',

            # Adjectives / determiners
            'each': 'har', 'every': 'har', 'all': 'sabhi', 'own': 'khud ka',
            'multiple': 'kai', 'new': 'naya', 'same': 'wahi',
            'first': 'pehla', 'last': 'aakhri', 'next': 'agla', 'previous': 'pichla',

            # Conjunctions / adverbs
            'and': 'aur', 'or': 'ya', 'but': 'lekin', 'then': 'phir',
            'after': 'baad', 'before': 'pehle', 'when': 'jab', 'not': 'nahi',
            'also': 'bhi', 'only': 'sirf', 'always': 'hamesha',
            'never': 'kabhi nahi',

            # Action verbs – infinitive / imperative
            'create': 'banao',       'use': 'upyog karo',  'assign': 'assign karo',
            'iterate': 'iterate karo', 'increment': 'badhao', 'decrement': 'ghatao',
            'return': 'return karo', 'store': 'store karo', 'call': 'call karo',
            'define': 'define karo', 'declare': 'declare karo', 'throw': 'throw karo',
            'run': 'run karo',       'execute': 'execute karo',

            # Action verbs – 3rd-person singular present (karta hai forms)
            'creates': 'banata hai',     'uses': 'upyog karta hai',
            'iterates': 'iterate karta hai', 'incremented': 'badhaya',
            'returns': 'return karta hai',   'stores': 'store karta hai',
            'calls': 'call karta hai',       'defines': 'define karta hai',
            'declares': 'declare karta hai', 'throws': 'throw karta hai',
            'runs': 'run karta hai',         'executes': 'execute karta hai',
            'contains': 'contain karta hai', 'extends': 'extend karta hai',
            'implements': 'implement karta hai',
            'continues': 'jaari rehta hai',
            'becomes': 'ban jaata hai',

            # Action verbs – past
            'created': 'banaya', 'used': 'upyog kiya', 'assigned': 'assign kiya',
            'iterated': 'iterate kiya',

            # Common non-technical nouns
            'name': 'naam', 'time': 'samay', 'way': 'tarika', 'number': 'number',
            'true': 'true', 'false': 'false',
        }

        # ── Pre-translation grammar rules ──────────────────────────────────
        # Applied BEFORE word substitution, while [bracket] syntax is visible.
        # Each entry: (compiled_regex, replacement_string).
        #
        # Possession rule: "Subject has Object." → "Subject mein Object hain."
        # English "X has Y" → Hindi "X mein Y hain" (locative possession).
        # Pattern handles [bracketed] tokens because guarding already happened.
        # Guard: negative lookahead skips "has been" (perfect tense).
        self._pre_rules = [
            (
                re.compile(
                    r'((?:[\w]+|\[[^\]]+\])(?:\s+(?:[\w]+|\[[^\]]+\]))*?)'
                    r'\s+has\s+(?!been\b)'
                    r'((?:[\w]+|\[[^\]]+\])(?:\s+(?:[\w]+|\[[^\]]+\]))*?)'
                    r'([.!?]*)$',
                    re.IGNORECASE,
                ),
                r'\1 mein \2 hain\3',
            ),
        ]

        # ── Post-bracket grammar rules ──────────────────────────────────────
        # Applied AFTER word substitution but BEFORE bracket restoration,
        # while [bracket] syntax is still visible.  Used for term-pair reordering.
        self._post_rules = [
            # "[X] of [Y]" → "[Y] ka [X]"
            (re.compile(r'\[([^\]]+)\] of \[([^\]]+)\]'), r'[\2] ka [\1]'),
            # "[X] in [Y]" → "[Y] mein [X]"
            (re.compile(r'\[([^\]]+)\] in \[([^\]]+)\]'), r'[\2] mein [\1]'),
        ]

    # ------------------------------------------------------------------

    def translate(self, text: str) -> str:
        """Translate guarded English text to Roman Hinglish."""

        # Step 1: pre-grammar rules (possession restructure, etc.)
        result = text
        for pattern, replacement in self._pre_rules:
            result = pattern.sub(replacement, result)

        # Step 2: protect [bracketed] technical terms
        protected: Dict[str, str] = {}

        def protect(m: re.Match) -> str:
            key = f'__P{len(protected)}__'
            protected[key] = m.group(0)
            return key

        result = re.sub(r'\[([^\]]+)\]', protect, result)

        # Step 3: word-by-word substitution
        words = result.split()
        out = []
        for word in words:
            if word in protected:
                out.append(word)
                continue
            clean = word.lower().strip('.,!?;:()')
            if clean in self.word_map:
                mapped = self.word_map[clean]
                if mapped:          # skip empty mappings (e.g. 'the' → '')
                    out.append(mapped)
            else:
                out.append(word)
        result = ' '.join(out)

        # Step 4: post-bracket grammar rules (term-pair reordering)
        for pattern, replacement in self._post_rules:
            result = pattern.sub(replacement, result)

        # Step 5: SOV reorder – move verb phrase from mid-sentence to end
        # English SVO → Hindi SOV:
        #   "function return karta hai ek boolean value" →
        #   "function ek boolean value return karta hai"
        for verb in self._SOV_VERBS:
            m = re.match(
                r'^(.+?)\s+' + re.escape(verb) + r'\s+(.+?)([.,!?]*)$',
                result,
            )
            if m:
                result = f'{m.group(1)} {m.group(2)} {verb}{m.group(3)}'
                break

        # Step 6: restore protected terms
        for key, term in protected.items():
            result = result.replace(key, term)

        return re.sub(r'\s+', ' ', result).strip()


class LLMTranslator(BaseTranslator):
    """
    LLM-based translator using the OpenAI API (v1.x client).
    Falls back to BaselineTranslator if the package is unavailable or the
    API key is not set.
    """

    def __init__(self, target_language: str = "hi",
                 model: str = "gpt-3.5-turbo",
                 api_key: Optional[str] = None,
                 temperature: float = 0.3):
        super().__init__(target_language)
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.lang_names = {
            'hi': 'Hindi', 'mr': 'Marathi', 'te': 'Telugu',
            'ta': 'Tamil',  'bn': 'Bengali',
        }

    def translate(self, text: str) -> str:
        try:
            import openai
        except ImportError:
            print("Warning: OpenAI package not installed. Falling back to baseline.", file=sys.stderr)
            return BaselineTranslator(self.target_language).translate(text)

        if not self.api_key:
            print("Warning: No API key provided. Falling back to baseline.", file=sys.stderr)
            return BaselineTranslator(self.target_language).translate(text)

        lang = self.lang_names.get(self.target_language, 'Hindi')
        try:
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": (
                        f"You are an expert technical translator to {lang}.\n"
                        "RULES: Keep ALL [bracketed] content EXACTLY unchanged. "
                        "Translate only non-bracketed text. Use Roman script (not Devanagari). "
                        "Maintain natural Hindi grammar and technical tone."
                    )},
                    {"role": "user", "content": f'Translate to {lang}:\n"{text}"\n\nKeep [bracketed] content unchanged.'},
                ],
                temperature=self.temperature,
                max_tokens=len(text.split()) * 3,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Warning: LLM translation failed ({e}). Falling back to baseline.", file=sys.stderr)
            return BaselineTranslator(self.target_language).translate(text)
