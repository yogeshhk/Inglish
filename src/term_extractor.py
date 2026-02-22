"""Term extraction module for identifying technical terms."""

import re
from typing import List, Tuple, Dict
from utils import load_glossary, resolve_overlapping_spans

_PUNCT = '.,!?;:'


class TermExtractor:
    """
    Extract and guard technical terms from English text.
    
    extract_terms() returns List[Tuple[str, int, int]] where:
      [0] term_text : matched term as it appears in the input
      [1] start     : character start index in original text
      [2] end       : character end index in original text
    """

    def __init__(self, domain: str):
        self.domain = domain
        self.glossary = load_glossary(domain)
        
        self.single_terms: set = set()
        self.compound_trie: Dict = {}
        
        self._load_terms()

    def _load_terms(self):
        """Populate single_terms set and compound_trie from plain list."""
        all_terms = []
        
        for entry in self.glossary.get('terms', []):
            term = str(entry).lower().strip()
            if term:
                all_terms.append(term)
                self.single_terms.add(term)
        
        for entry in self.glossary.get('compound_terms', []):
            term = str(entry).lower().strip()
            if term:
                all_terms.append(term)
                words = term.split()
                node = self.compound_trie
                for word in words:
                    node = node.setdefault(word, {})
                node['$'] = True

    def extract_terms(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Extract all technical terms from text.
        
        Returns:
            List of (term_text, start, end) tuples,
            sorted by position, with overlaps resolved (longer wins).
        """
        raw: List[Tuple[str, int, int]] = []
        raw.extend(self._extract_compound_terms(text))
        raw.extend(self._extract_single_terms(text))
        
        return resolve_overlapping_spans(raw)

    def guard_terms(self, text: str, terms: List[Tuple[str, int, int]] = None) -> str:
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
        
        sorted_terms = sorted(terms, key=lambda t: t[1], reverse=True)
        result = text
        for term_text, start, end in sorted_terms:
            actual = text[start:end]
            result = result[:start] + f"[{actual}]" + result[end:]
        return result

    def unguard_terms(self, text: str) -> str:
        """Remove square brackets, keeping the term text."""
        return re.sub(r'\[([^\]]+)\]', r'\1', text)

    def get_guarded_terms(self, text: str) -> List[str]:
        """Return list of terms currently inside brackets."""
        return re.findall(r'\[([^\]]+)\]', text)

    def _extract_compound_terms(self, text: str) -> List[Tuple[str, int, int]]:
        matches = []
        words = text.split()
        
        i = 0
        while i < len(words):
            node = self.compound_trie
            match_words = []
            j = i
            
            while j < len(words):
                word = words[j].lower().strip(_PUNCT)
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
            clean = word.lower().strip(_PUNCT)
            if clean in self.single_terms:
                prefix = ' '.join(words[:i])
                start = len(prefix) + (1 if prefix else 0)
                end = start + len(clean)
                matches.append((clean, start, end))
        
        return matches
