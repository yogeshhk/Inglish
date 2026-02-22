"""Utility functions for the Inglish translator."""

import re
import yaml
import json
from typing import Dict, List, Tuple, Any
from pathlib import Path

# Root of the project is two levels above this file:
#   <project_root>/src/utils.py  ->  _SRC_DIR = <project_root>/src
#   <project_root>/data/...
# If the layout is flat (all files in one directory) _SRC_DIR and _PROJECT_ROOT
# point to the same place, and data/ is looked up relative to that directory.
_SRC_DIR = Path(__file__).parent
_PROJECT_ROOT = _SRC_DIR.parent


def _resolve_data_path(relative: str) -> Path:
    """
    Resolve a data path relative to the project root.

    Searches two candidate locations so the helper works both with the
    canonical src/ layout (data/ sits beside src/) and with a flat layout
    where all files share one directory:

      1. <project_root> / relative        e.g. <root>/data/glossaries/programming.yaml
      2. <src_dir>      / relative        e.g. <src>/data/glossaries/programming.yaml

    Returns the first path that exists, or the canonical location (1) as a
    fallback so that the caller receives a meaningful FileNotFoundError message.
    """
    for base in (_PROJECT_ROOT, _SRC_DIR):
        candidate = base / relative
        if candidate.exists():
            return candidate
    # Return the canonical path even though it doesn't exist; the caller will
    # raise FileNotFoundError with a useful message.
    return _PROJECT_ROOT / relative


def load_glossary(domain: str, glossary_dir: str = "data/glossaries") -> Dict[str, Any]:
    """Load domain-specific glossary from YAML file."""
    glossary_path = _resolve_data_path(f"{glossary_dir}/{domain}.yaml")

    if not glossary_path.exists():
        raise FileNotFoundError(f"Glossary not found: {glossary_path}")

    with open(glossary_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def load_patterns(domain: str, pattern_dir: str = "data/patterns") -> List:
    """Load regex patterns for term detection."""
    pattern_path = _resolve_data_path(f"{pattern_dir}/regex_patterns.json")

    if not pattern_path.exists():
        return []

    with open(pattern_path, 'r', encoding='utf-8') as f:
        all_patterns = json.load(f)

    return all_patterns.get(domain, [])


def build_trie(words: List[str]) -> Dict:
    """Build a Trie data structure for efficient word matching."""
    root = {}
    for word in words:
        node = root
        for char in word.lower():
            if char not in node:
                node[char] = {}
            node = node[char]
        node['$'] = True  # End of word marker
    return root


def find_trie_matches(text: str, trie: Dict) -> List[Tuple[str, int, int]]:
    """Find all matches in text using Trie."""
    matches = []
    words = text.split()
    
    for i, word in enumerate(words):
        # Try matching from this position
        node = trie
        match_words = []
        
        for j in range(i, len(words)):
            current_word = words[j].lower().strip('.,!?;:')
            if current_word in node:
                node = node[current_word]
                match_words.append(words[j])
                
                if node.get('$'):
                    # Found a complete match
                    match_text = ' '.join(match_words)
                    start_pos = len(' '.join(words[:i]))
                    end_pos = start_pos + len(match_text)
                    matches.append((match_text, start_pos, end_pos))
            else:
                break
    
    return matches


def extract_bracketed_terms(text: str) -> List[str]:
    """Extract all terms within square brackets."""
    return re.findall(r'\[([^\]]+)\]', text)


def remove_brackets(text: str) -> str:
    """Remove square brackets while keeping the content."""
    return re.sub(r'\[([^\]]+)\]', r'\1', text)


def add_brackets(text: str, terms: List[Tuple[str, int, int]]) -> str:
    """Add square brackets around specified terms."""
    # Sort by position (reverse) to maintain correct indices
    sorted_terms = sorted(terms, key=lambda x: x[1], reverse=True)
    
    result = text
    for term, start, end in sorted_terms:
        # Simple replacement (more robust implementation would track positions)
        result = result.replace(term, f"[{term}]", 1)
    
    return result


def normalize_devanagari(text: str) -> str:
    """Normalize Devanagari text (remove extra spaces, etc.)."""
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    # Fix spacing around punctuation
    text = re.sub(r'\s+([।,;!?])', r'\1', text)
    return text.strip()


def calculate_overlap(span1: Tuple[int, int], span2: Tuple[int, int]) -> bool:
    """Check if two spans overlap."""
    return not (span1[1] <= span2[0] or span2[1] <= span1[0])


def resolve_overlapping_spans(spans: List[Tuple[str, int, int]]) -> List[Tuple[str, int, int]]:
    """Remove overlapping spans, keeping longer matches."""
    if not spans:
        return []
    
    # Sort by start position, then by length (descending)
    sorted_spans = sorted(spans, key=lambda x: (x[1], -(x[2] - x[1])))
    
    result = []
    for span in sorted_spans:
        # Check if it overlaps with any already accepted span
        overlaps = any(calculate_overlap((span[1], span[2]), (s[1], s[2])) 
                      for s in result)
        if not overlaps:
            result.append(span)
    
    return sorted(result, key=lambda x: x[1])


def simple_romanize(devanagari_text: str) -> str:
    """Simple Devanagari to Roman transliteration (basic mapping)."""
    # This is a simplified mapping - use indic-transliteration for production
    mapping = {
        'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ii', 'उ': 'u', 'ऊ': 'uu',
        'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
        'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
        'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
        'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
        'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
        'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
        'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh',
        'ष': 'sh', 'स': 's', 'ह': 'h',
        'ा': 'aa', 'ि': 'i', 'ी': 'ii', 'ु': 'u', 'ू': 'uu',
        'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
        '्': '', 'ं': 'm', 'ः': 'h', '।': '.'
    }
    
    result = []
    for char in devanagari_text:
        result.append(mapping.get(char, char))
    
    return ''.join(result)


def load_json_dataset(file_path: str) -> List[Dict[str, Any]]:
    """Load dataset from JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and 'samples' in data:
        return data['samples']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected dataset format in {file_path}")


def save_json_dataset(data: List[Dict[str, Any]], file_path: str):
    """Save dataset to JSON file."""
    output_dir = Path(file_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text
