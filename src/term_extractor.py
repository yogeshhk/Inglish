"""Term extraction module for identifying technical terms."""

import re
from typing import List, Tuple, Dict
from utils import load_glossary, load_patterns, resolve_overlapping_spans


class TermExtractor:
    """
    Extract and guard technical terms from English text.

    extract_terms() returns List[Tuple[str, str, int, int]] where:
      [0] term_text    : matched term as it appears in the input
      [1] devanagari   : phonetic Devanagari form from the glossary ('' if absent)
      [2] start        : character start index in original text
      [3] end          : character end index in original text

    The devanagari field is passed through the pipeline to ScriptConverter
    so English loanwords are rendered phonetically in Devanagari output
    rather than being garbled by ITRANS.
    """

    def __init__(self, domain: str):
        self.domain = domain
        self.glossary = load_glossary(domain)
        self.patterns = load_patterns(domain)

        # term_lower -> devanagari_phonetic
        self._deva_map: Dict[str, str] = {}

        self.single_terms: set = set()
        self.compound_trie: Dict = {}

        self._load_terms()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_terms(self, text: str) -> List[Tuple[str, str, int, int]]:
        """
        Extract all technical terms from text.

        Returns:
            List of (term_text, devanagari, start, end) tuples,
            sorted by position, with overlaps resolved (longer wins).
        """
        raw: List[Tuple[str, int, int]] = []
        raw.extend(self._extract_compound_terms(text))
        raw.extend(self._extract_single_terms(text))
        raw.extend(self._extract_pattern_terms(text))

        resolved = resolve_overlapping_spans(raw)

        return [
            (term, self._deva_map.get(term.lower(), ""), start, end)
            for term, start, end in resolved
        ]

    def guard_terms(self, text: str,
                    terms: List[Tuple[str, str, int, int]] = None) -> str:
        """
        Wrap each technical term in square brackets.

        Args:
            text: Original text.
            terms: Output of extract_terms(). Auto-extracted if None.
        """
        if terms is None:
            terms = self.extract_terms(text)
        if not terms:
            return text

        # Sort by position descending so index arithmetic stays correct
        sorted_terms = sorted(terms, key=lambda t: t[2], reverse=True)
        result = text
        for term_text, _deva, start, end in sorted_terms:
            actual = text[start:end]
            result = result[:start] + f"[{actual}]" + result[end:]
        return result

    def unguard_terms(self, text: str) -> str:
        """Remove square brackets, keeping the term text."""
        return re.sub(r'\[([^\]]+)\]', r'\1', text)

    def get_guarded_terms(self, text: str) -> List[str]:
        """Return list of terms currently inside brackets."""
        return re.findall(r'\[([^\]]+)\]', text)

    def validate_guarding(self, original: str, guarded: str) -> bool:
        """True if unguarding the guarded text reproduces the original."""
        return original.strip() == self.unguard_terms(guarded).strip()

    # ------------------------------------------------------------------
    # Private: load glossary
    # ------------------------------------------------------------------

    def _load_terms(self):
        """Populate single_terms set, compound_trie, and _deva_map."""
        # --- single terms ---
        for entry in self.glossary.get('terms', []):
            if isinstance(entry, dict):
                term = entry['term'].lower()
                deva = entry.get('devanagari', '')
            else:
                term = str(entry).lower()
                deva = ''
            self.single_terms.add(term)
            if deva:
                self._deva_map[term] = deva

        # --- compound terms ---
        # Support both old format (plain strings) and new format (dicts with devanagari)
        for entry in self.glossary.get('compound_terms', []):
            if isinstance(entry, dict):
                term = entry['term'].lower()
                deva = entry.get('devanagari', '')
            else:
                term = str(entry).lower()
                deva = ''
            if deva:
                self._deva_map[term] = deva
            # Build trie
            words = term.split()
            node = self.compound_trie
            for word in words:
                node = node.setdefault(word, {})
            node['$'] = True

    # ------------------------------------------------------------------
    # Private: extraction methods
    # ------------------------------------------------------------------

    def _extract_compound_terms(self, text: str) -> List[Tuple[str, int, int]]:
        matches = []
        words = text.split()

        i = 0
        while i < len(words):
            node = self.compound_trie
            match_words = []
            j = i

            while j < len(words):
                word = words[j].lower().strip('.,!?;:()')
                if word in node:
                    node = node[word]
                    match_words.append(words[j])
                    j += 1
                    if node.get('$'):
                        match_text = ' '.join(match_words)
                        prefix = ' '.join(words[:i])
                        start = len(prefix) + (1 if prefix else 0)
                        end = start + len(match_text)
                        matches.append((match_text, start, end))
                else:
                    break
            i += 1

        return matches

    def _extract_single_terms(self, text: str) -> List[Tuple[str, int, int]]:
        matches = []
        words = text.split()

        for i, word in enumerate(words):
            clean = word.lower().strip('.,!?;:()')
            if clean in self.single_terms:
                prefix = ' '.join(words[:i])
                start = len(prefix) + (1 if prefix else 0)
                end = start + len(word)
                matches.append((word, start, end))

        return matches

    def _extract_pattern_terms(self, text: str) -> List[Tuple[str, int, int]]:
        matches = []
        for entry in self.patterns:
            pattern = entry.get('regex', '') if isinstance(entry, dict) else entry
            if not pattern:
                continue
            try:
                for m in re.finditer(pattern, text):
                    matches.append((m.group(0), m.start(), m.end()))
            except re.error:
                continue
        return matches
