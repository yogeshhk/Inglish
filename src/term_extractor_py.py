"""Term extraction module for identifying technical terms."""

import re
from typing import List, Tuple, Dict, Set
from .utils import load_glossary, load_patterns, build_trie, resolve_overlapping_spans


class TermExtractor:
    """Extract and guard technical terms from English text."""
    
    def __init__(self, domain: str):
        """
        Initialize term extractor for a specific domain.
        
        Args:
            domain: Domain name (e.g., 'programming', 'physics', 'finance')
        """
        self.domain = domain
        self.glossary = load_glossary(domain)
        self.patterns = load_patterns(domain)
        
        # Build term sets for efficient lookup
        self.single_terms = set()
        self.compound_terms = []
        
        if 'terms' in self.glossary:
            for term_entry in self.glossary['terms']:
                if isinstance(term_entry, dict):
                    self.single_terms.add(term_entry['term'].lower())
                else:
                    self.single_terms.add(term_entry.lower())
        
        if 'compound_terms' in self.glossary:
            self.compound_terms = [t.lower() for t in self.glossary['compound_terms']]
        
        # Build Trie for compound terms
        self.compound_trie = self._build_compound_trie()
        
    def _build_compound_trie(self) -> Dict:
        """Build Trie for multi-word terms."""
        root = {}
        for term in self.compound_terms:
            words = term.split()
            node = root
            for word in words:
                if word not in node:
                    node[word] = {}
                node = node[word]
            node['$'] = True
        return root
    
    def extract_terms(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Extract all technical terms from text.
        
        Returns:
            List of (term, start_index, end_index) tuples
        """
        terms = []
        
        # Method 1: Exact glossary matching (compound terms first)
        terms.extend(self._extract_compound_terms(text))
        
        # Method 2: Single word terms
        terms.extend(self._extract_single_terms(text))
        
        # Method 3: Pattern-based extraction
        terms.extend(self._extract_pattern_terms(text))
        
        # Remove overlaps, preferring longer matches
        terms = resolve_overlapping_spans(terms)
        
        return terms
    
    def _extract_compound_terms(self, text: str) -> List[Tuple[str, int, int]]:
        """Extract multi-word technical terms."""
        matches = []
        words = text.split()
        
        i = 0
        while i < len(words):
            # Try to match from current position
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
                        # Found complete match
                        match_text = ' '.join(match_words)
                        # Calculate position in original text
                        prefix = ' '.join(words[:i])
                        start = len(prefix) + (1 if prefix else 0)
                        end = start + len(match_text)
                        matches.append((match_text, start, end))
                else:
                    break
            
            i += 1
        
        return matches
    
    def _extract_single_terms(self, text: str) -> List[Tuple[str, int, int]]:
        """Extract single-word technical terms."""
        matches = []
        words = text.split()
        
        for i, word in enumerate(words):
            clean_word = word.lower().strip('.,!?;:()')
            if clean_word in self.single_terms:
                # Calculate position
                prefix = ' '.join(words[:i])
                start = len(prefix) + (1 if prefix else 0)
                end = start + len(word)
                matches.append((word, start, end))
        
        return matches
    
    def _extract_pattern_terms(self, text: str) -> List[Tuple[str, int, int]]:
        """Extract terms matching regex patterns."""
        matches = []
        
        for pattern_dict in self.patterns:
            if isinstance(pattern_dict, dict):
                pattern = pattern_dict.get('regex', '')
            else:
                pattern = pattern_dict
            
            if not pattern:
                continue
            
            try:
                for match in re.finditer(pattern, text):
                    term = match.group(0)
                    matches.append((term, match.start(), match.end()))
            except re.error:
                # Invalid regex, skip
                continue
        
        return matches
    
    def guard_terms(self, text: str, terms: List[Tuple[str, int, int]] = None) -> str:
        """
        Add square brackets around technical terms.
        
        Args:
            text: Original text
            terms: List of terms to guard (if None, auto-extract)
            
        Returns:
            Text with [bracketed] technical terms
        """
        if terms is None:
            terms = self.extract_terms(text)
        
        if not terms:
            return text
        
        # Sort by position (reverse) to maintain indices
        sorted_terms = sorted(terms, key=lambda x: x[1], reverse=True)
        
        result = text
        for term, start, end in sorted_terms:
            # Extract the actual term from text
            actual_term = text[start:end]
            result = result[:start] + f"[{actual_term}]" + result[end:]
        
        return result
    
    def unguard_terms(self, text: str) -> str:
        """Remove square brackets from guarded terms."""
        return re.sub(r'\[([^\]]+)\]', r'\1', text)
    
    def get_guarded_terms(self, text: str) -> List[str]:
        """Extract list of terms that are currently guarded (in brackets)."""
        return re.findall(r'\[([^\]]+)\]', text)
    
    def validate_guarding(self, original: str, guarded: str) -> bool:
        """
        Validate that guarding preserved all non-bracketed text.
        
        Returns:
            True if validation passes
        """
        unguarded = self.unguard_terms(guarded)
        return original.strip() == unguarded.strip()