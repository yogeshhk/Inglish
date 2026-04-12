"""
Compatibility shim — re-exports shared utilities under the docgen namespace.

Modules inside docgen/ import from here so they don't need to know about
the shared/ package location.
"""
from shared.utils import (  # noqa: F401
    load_glossary,
    load_patterns,
    load_slangs,
    extract_bracketed_terms,
    remove_brackets,
    spans_overlap,
    resolve_overlapping_spans,
    load_json_dataset,
    save_json_dataset,
    clean_text,
    normalize_devanagari,
)
