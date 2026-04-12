"""Shared utility functions for the Inglish translator."""

import re
import yaml
import json
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# When this file lives at src/shared/utils.py:
#   _SHARED_DIR  = src/shared/
#   _SRC_DIR     = src/
#   _PROJECT_ROOT = project root (Inglish/)
_SHARED_DIR   = Path(__file__).parent
_SRC_DIR      = _SHARED_DIR.parent
_PROJECT_ROOT = _SRC_DIR.parent


def _resolve_data_path(relative: str) -> Path:
    """Resolve a data path, searching src/ then project root."""
    for base in (_SRC_DIR, _PROJECT_ROOT):
        candidate = base / relative
        if candidate.exists():
            return candidate
    return _SRC_DIR / relative


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


def load_slangs(language: str, slangs_dir: str = "data/slangs") -> Dict[str, Any]:
    """Load language-specific podcast skill YAML. Raises FileNotFoundError if missing."""
    path = _resolve_data_path(f"{slangs_dir}/{language}.yaml")
    if not path.exists():
        raise FileNotFoundError(f"Slangs file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


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
    When two spans overlap, the longer one wins globally — not just at the
    same start position. Uses a greedy interval-scheduling approach: process
    candidates longest-first, keeping a span only if it doesn't overlap
    with any already-selected span.
    Returns spans sorted by start position.
    """
    if not spans:
        return []

    # Sort by length descending so the longest candidate is always considered first
    ordered = sorted(spans, key=lambda x: -(x[2] - x[1]))

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


# ---------------------------------------------------------------------------
# Structured-text flattening (pre-processing for translation)
# ---------------------------------------------------------------------------

# Compiled patterns — module-level for performance
_RE_LABELED  = re.compile(r'^([A-Z][^:\n]{2,50}):\s+(.+)$')  # "Label: content"
_RE_NUMBERED = re.compile(r'^\d+[.)]\s+(.+)$')               # "1. content" / "1) content"
_RE_BULLET   = re.compile(r'^[-*•]\s+(.+)$')                 # "- / * / • content"
_RE_HEADER   = re.compile(r'^(.+):\s*$')                     # "Section header:"

_CONNECTORS = ["", "Also, ", "Furthermore, ", "In addition, ",
               "Moreover, ", "Additionally, "]


def preprocess_for_translation(text: str) -> str:
    """
    Flatten structured text (labeled sections, numbered lists, bullet lists)
    into prose paragraphs so the LLM translates them naturally.

    The LLM tends to pass structured list formats through untouched because
    they look like pre-formatted content. Converting them to flowing sentences
    forces the LLM to engage with and translate the actual words.

    Handles:
      - "Label: Content" labeled bullets (most common in technical docs)
      - Numbered lists ("1. ...", "2. ...")
      - Dash / asterisk / bullet lists ("- ...", "* ...", "• ...")
      - Optional section headers preceding any of the above

    Non-list paragraphs are returned unchanged.

    Example input:
        Key Aspects of Python Generators:
        Lazy Evaluation: Generators compute values on demand.
        Memory Efficiency: Ideal for large datasets.

    Example output:
        Here are the key aspects of Key Aspects of Python Generators:
        Lazy Evaluation means that Generators compute values on demand.
        Furthermore, Memory Efficiency means that Ideal for large datasets.
    """
    paragraphs = re.split(r'\n{2,}', text.strip())
    return "\n\n".join(
        _flatten_paragraph([l.strip() for l in p.splitlines() if l.strip()])
        for p in paragraphs
        if p.strip()
    )


def _flatten_paragraph(lines: List[str]) -> str:
    """Detect list structure in a single paragraph and flatten to prose."""
    if len(lines) <= 1:
        return lines[0] if lines else ""

    # Detect optional section header: first line ends with ":" and nothing after
    header: Optional[str] = None
    body = lines
    m = _RE_HEADER.match(lines[0])
    if m and len(lines) > 1:
        header = m.group(1).strip()
        body = lines[1:]

    # Score each body line against the three list patterns
    labeled  = [_RE_LABELED.match(l)  for l in body]
    numbered = [_RE_NUMBERED.match(l) for l in body]
    bulleted = [_RE_BULLET.match(l)   for l in body]

    # Require at least half the lines (min 2) to match before treating as list
    threshold = max(2, len(body) // 2)

    if sum(bool(x) for x in labeled)  >= threshold:
        return _flatten_labeled(header, body, labeled)
    if sum(bool(x) for x in numbered) >= threshold:
        items = [x.group(1) for x in numbered if x]
        return _flatten_simple(header, items)
    if sum(bool(x) for x in bulleted) >= threshold:
        items = [x.group(1) for x in bulleted if x]
        return _flatten_simple(header, items)

    # Not a list — return as joined text
    return "\n".join(lines)


_RE_LIST_PREFIX = re.compile(
    r'^(?:key\s+)?(?:aspects?|points?|features?|properties|benefits?)\s+of\s+',
    re.IGNORECASE,
)


def _flatten_labeled(
    header: Optional[str],
    lines: List[str],
    matches: list,
) -> str:
    """Convert 'Label: Content' lines to flowing prose sentences."""
    sentences = []
    for i, (line, m) in enumerate(zip(lines, matches)):
        conn = _CONNECTORS[min(i, len(_CONNECTORS) - 1)]
        if m:
            label   = m.group(1).strip()
            content = m.group(2).strip().rstrip(".,!?;:")  # avoid double punctuation
            sentences.append(f"{conn}{label} means that {content}")
        else:
            sentences.append(f"{conn}{line.rstrip('.,!?;:')}")

    if header:
        # Strip "Key Aspects of", "Features of", etc. so we don't get
        # "Here are the key aspects of Key Aspects of X"
        clean_header = _RE_LIST_PREFIX.sub("", header).strip()
        intro = f"Here are the key aspects of {clean_header}: "
    else:
        intro = ""
    return intro + ". ".join(sentences) + "."


def _flatten_simple(header: Optional[str], items: List[str]) -> str:
    """Convert plain bullet / numbered items to flowing prose."""
    if not items:
        return ""
    intro = f"Regarding {header}: " if header else ""
    if len(items) == 1:
        return intro + items[0] + "."
    sentences = [items[0]] + [
        f"{_CONNECTORS[min(i + 1, len(_CONNECTORS) - 1)]}{item}"
        for i, item in enumerate(items[1:])
    ]
    return intro + ". ".join(sentences) + "."
