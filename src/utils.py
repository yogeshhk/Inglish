"""Utility functions for the Inglish translator."""

import re
import yaml
import json
from typing import Dict, List, Tuple, Any
from pathlib import Path

_SRC_DIR = Path(__file__).parent
_PROJECT_ROOT = _SRC_DIR.parent


def _resolve_data_path(relative: str) -> Path:
    """Resolve a data path relative to the project root."""
    for base in (_PROJECT_ROOT, _SRC_DIR):
        candidate = base / relative
        if candidate.exists():
            return candidate
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


def extract_bracketed_terms(text: str) -> List[str]:
    """Extract all terms within square brackets."""
    return re.findall(r'\[([^\]]+)\]', text)


def remove_brackets(text: str) -> str:
    """Remove square brackets while keeping the content."""
    return re.sub(r'\[([^\]]+)\]', r'\1', text)


def normalize_devanagari(text: str) -> str:
    """Normalize Devanagari text."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+([।,;!?])', r'\1', text)
    return text.strip()


def calculate_overlap(span1: Tuple[int, int], span2: Tuple[int, int]) -> bool:
    """Check if two spans overlap."""
    return not (span1[1] <= span2[0] or span2[1] <= span1[0])


def resolve_overlapping_spans(spans: List[Tuple[str, int, int]]) -> List[Tuple[str, int, int]]:
    """Remove overlapping spans, keeping longer matches."""
    if not spans:
        return []
    
    sorted_spans = sorted(spans, key=lambda x: (x[1], -(x[2] - x[1])))
    
    result = []
    for span in sorted_spans:
        overlaps = any(calculate_overlap((span[1], span[2]), (s[1], s[2])) 
                      for s in result)
        if not overlaps:
            result.append(span)
    
    return sorted(result, key=lambda x: x[1])


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
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text
