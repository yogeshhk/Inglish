"""
Term extraction module — Tier 1 of the Inglish pipeline.

Identifies technical terms in English text using:
  1. Trie-based compound-term matching (e.g. "for loop", "member variable")
  2. Single-term glossary lookup

Terms are then "guarded" by wrapping them in [square brackets] so the LLM
translator knows to leave them unchanged.
"""

from typing import List, Tuple, Dict

from utils import load_glossary, resolve_overlapping_spans, remove_brackets, extract_bracketed_terms

_PUNCT = '.,!?;:'


class TermExtractor:
    """
    Extract and guard technical terms from English text.

    extract_terms() → List[Tuple[str, int, int]]
        Each tuple: (term_text, char_start, char_end)
        Tuples are sorted by position; overlapping spans are resolved
        (longer match wins).
    """

    def __init__(self, domain: str):
        self.domain = domain
        self.glossary = load_glossary(domain)

        # Single-word terms (fast O(1) lookup)
        self._single_terms: set = set()
        # Compound-term Trie (enables O(n) multi-word matching)
        self._compound_trie: Dict = {}

        self._load_terms()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _load_terms(self) -> None:
        """Build single_terms set and compound_trie from glossary."""
        for entry in self.glossary.get("terms", []):
            term = str(entry).lower().strip()
            if term:
                self._single_terms.add(term)

        for entry in self.glossary.get("compound_terms", []):
            term = str(entry).lower().strip()
            if term:
                words = term.split()
                node = self._compound_trie
                for word in words:
                    node = node.setdefault(word, {})
                node["$"] = True   # end-of-term marker

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_terms(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Return all technical terms found in text.

        Compound terms are matched first; overlapping spans are resolved
        (longest span wins).
        """
        spans: List[Tuple[str, int, int]] = []
        spans.extend(self._match_compound_terms(text))
        spans.extend(self._match_single_terms(text))
        return resolve_overlapping_spans(spans)

    def guard_terms(self, text: str,
                    terms: List[Tuple[str, int, int]] = None) -> str:
        """
        Wrap each technical term in [square brackets].

        Processes spans in reverse order so that character offsets remain
        valid as the string grows.
        """
        if terms is None:
            terms = self.extract_terms(text)
        if not terms:
            return text

        result = text
        for term_text, start, end in sorted(terms, key=lambda t: t[1], reverse=True):
            actual = text[start:end]
            result = result[:start] + f"[{actual}]" + result[end:]
        return result

    def unguard_terms(self, text: str) -> str:
        """Remove square brackets, keeping the enclosed term text."""
        return remove_brackets(text)

    def get_guarded_terms(self, text: str) -> List[str]:
        """Return the list of terms currently inside brackets."""
        return extract_bracketed_terms(text)

    # ------------------------------------------------------------------
    # Internal matching
    # ------------------------------------------------------------------

    def _match_compound_terms(self, text: str) -> List[Tuple[str, int, int]]:
        """Walk the trie against space-split tokens to find compound terms."""
        matches = []
        words = text.split()

        for i in range(len(words)):
            node = self._compound_trie
            j = i
            matched_words: List[str] = []

            while j < len(words):
                word_clean = words[j].lower().strip(_PUNCT)
                if word_clean not in node:
                    break
                node = node[word_clean]
                matched_words.append(words[j])
                j += 1
                if node.get("$"):
                    # Strip trailing punctuation from the last word so the
                    # span covers only the term text, not the sentence punctuation.
                    last_clean = matched_words[-1].rstrip(_PUNCT)
                    clean_words = matched_words[:-1] + [last_clean]
                    match_text = " ".join(clean_words)
                    prefix = " ".join(words[:i])
                    start = len(prefix) + (1 if prefix else 0)
                    end = start + len(match_text)
                    matches.append((match_text, start, end))

        return matches

    def _match_single_terms(self, text: str) -> List[Tuple[str, int, int]]:
        """Match individual glossary terms against space-split tokens."""
        matches = []
        words = text.split()

        for i, word in enumerate(words):
            clean = word.lower().strip(_PUNCT)
            if clean in self._single_terms:
                prefix = " ".join(words[:i])
                start = len(prefix) + (1 if prefix else 0)
                end = start + len(clean)
                matches.append((clean, start, end))

        return matches
