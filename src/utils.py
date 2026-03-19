"""Shared utility functions for the Inglish translator."""

import re
import yaml
import json
from typing import Dict, List, Tuple, Any
from pathlib import Path

_SRC_DIR      = Path(__file__).parent
_PROJECT_ROOT = _SRC_DIR.parent


def _resolve_data_path(relative: str) -> Path:
    """Resolve a data path relative to the project root (or src dir as fallback)."""
    for base in (_PROJECT_ROOT, _SRC_DIR):
        candidate = base / relative
        if candidate.exists():
            return candidate
    return _PROJECT_ROOT / relative


# ---------------------------------------------------------------------------
# Glossary / pattern loading
# ---------------------------------------------------------------------------

def load_glossary(domain: str, glossary_dir: str = "data/glossaries") -> Dict[str, Any]:
    """Load domain glossary from YAML. Raises FileNotFoundError if missing."""
    path = _resolve_data_path(f"{glossary_dir}/{domain}.yaml")
    if not path.exists():
        raise FileNotFoundError(f"Glossary not found: {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_patterns(domain: str, pattern_dir: str = "data/patterns") -> List:
    """Load regex patterns for term detection. Returns empty list if file absent."""
    path = _resolve_data_path(f"{pattern_dir}/regex_patterns.json")
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f).get(domain, [])


# ---------------------------------------------------------------------------
# Bracket utilities
# ---------------------------------------------------------------------------

def extract_bracketed_terms(text: str) -> List[str]:
    """Return list of all terms found inside [square brackets]."""
    return re.findall(r'\[([^\]]+)\]', text)


def remove_brackets(text: str) -> str:
    """Remove square brackets while keeping enclosed text."""
    return re.sub(r'\[([^\]]+)\]', r'\1', text)


# ---------------------------------------------------------------------------
# Span utilities
# ---------------------------------------------------------------------------

def spans_overlap(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
    """Return True if two (start, end) spans overlap."""
    return not (a[1] <= b[0] or b[1] <= a[0])


def resolve_overlapping_spans(
    spans: List[Tuple[str, int, int]]
) -> List[Tuple[str, int, int]]:
    """
    Given a list of (term, start, end) spans, remove overlaps.
    When two spans overlap, the longer one wins.
    Returns spans sorted by start position.
    """
    if not spans:
        return []

    # Sort by start position, then by length (longer first) for tie-breaking
    ordered = sorted(spans, key=lambda x: (x[1], -(x[2] - x[1])))

    kept: List[Tuple[str, int, int]] = []
    for span in ordered:
        if not any(spans_overlap((span[1], span[2]), (s[1], s[2])) for s in kept):
            kept.append(span)

    return sorted(kept, key=lambda x: x[1])


# ---------------------------------------------------------------------------
# Dataset I/O
# ---------------------------------------------------------------------------

def load_json_dataset(file_path: str) -> List[Dict[str, Any]]:
    """Load a JSON dataset file. Supports top-level list or {"samples": [...]}."""
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "samples" in data:
        return data["samples"]
    raise ValueError(f"Unexpected dataset format in {file_path}")


def save_json_dataset(data: List[Dict[str, Any]], file_path: str) -> None:
    """Save a dataset to a JSON file, creating parent directories as needed."""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """Collapse whitespace and strip leading/trailing spaces."""
    return re.sub(r'\s+', ' ', text).strip()


def normalize_devanagari(text: str) -> str:
    """Normalize whitespace around Devanagari punctuation."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+([।,;!?])', r'\1', text)
    return text.strip()
