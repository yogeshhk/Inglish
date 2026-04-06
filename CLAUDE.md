# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Inglish** is a hybrid English → Indian language (Hindi/Marathi) translation framework that preserves technical terminology through a three-tier pipeline. The key insight: technical terms (function, array, for loop) must survive translation intact while surrounding prose gets translated.

## Commands

All source files live in `src/`. Run commands from the repo root.

```bash
# Install dependencies
pip install -r src/requirements.txt

# Launch web UI
streamlit run src/streamlit_main.py

# Run examples (auto-detects LLM provider from env vars)
python src/example_usage.py

# Run tests (must run from src/ because modules use bare imports)
cd src && pytest test_pipeline.py -v
cd src && pytest --cov=. test_pipeline.py

# Benchmarking
python src/baseline_benchmark.py --dataset src/data/datasets/eval/programming_eval.json --domain programming

# Code quality (requires make)
make format    # PEP 8 formatting
make lint
make typecheck
make test
```

## LLM Provider Setup

Set exactly one of these env vars (Gemini is default):
```bash
export GEMINI_API_KEY=...
export GROQ_API_KEY=...
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
```

## Three-Tier Architecture

```
English text
    │
    ▼ Tier 1: TermExtractor (term_extractor.py)
"The [for loop] iterates over the [array]"
    │
    ▼ Tier 2: LLMTranslator (translator.py)
"The [for loop] [array] ke upar iterate karta hai"
    │
    ▼ Tier 3: ScriptConverter (script_converter.py)
Roman Hinglish + Devanagari output
```

**Tier 1 — Term Extraction & Guarding** (`term_extractor.py`):
- Loads domain YAML glossary; uses a Trie for compound terms (multi-word phrases)
- `extract_terms()` returns `(term, start, end)` tuples; resolves overlaps (longest match wins)
- `guard_terms()` wraps matched terms in `[square brackets]` to protect them from LLM translation

**Tier 2 — LLM Translation** (`translator.py`):
- Prompt instructs the LLM to keep `[bracketed]` terms **exactly unchanged**
- `validate_constraints()` verifies all bracketed terms survived in LLM output
- Falls back gracefully if brackets were dropped

**Tier 3 — Script Conversion** (`script_converter.py`):
- `_ROMAN_TO_DEVA`: word-level lookup map (~200+ entries); not ITRANS (ITRANS breaks sentinels and converts digits)
- `roman_to_devanagari()`: 3-pass — stash Devanagari glossary terms behind sentinels → word-level lookup → restore
- Unknown Latin tokens (English technical terms) stay as Latin (correct code-mixing behavior)

**LLM Abstraction** (`llm_adapter.py`):
- Unified interface over Gemini, Groq, OpenAI, Anthropic, Ollama, LM Studio
- Built-in exponential backoff + jitter for 429 rate-limit errors
- No LangChain — uses provider native SDKs directly

**Orchestration** (`pipeline.py`):
- `TranslationConfig` dataclass: domain, target_language, llm_provider, llm_model, api_key, temperature
- `InglishtranslationPipeline.translate(text)` → dict with keys: `original_english`, `intermediate_bracketed`, `hinglish_roman`, `hinglish_devanagari`, `metadata`

## Domain Glossaries

Glossaries are in `src/data/glossaries/` as YAML. Adding a new domain requires only a new YAML file — no code changes.

```yaml
domain: programming
terms:          # unigrams — O(1) set lookup
  - variable
  - function
compound_terms: # multi-word — Trie lookup
  - for loop
  - member variable
```

## Dataset Format

Training/eval JSON at `src/data/datasets/`:
```json
{
  "id": "prog_001",
  "english": "The for loop iterates over the array.",
  "hinglish_roman": "for loop array ke upar iterate karta hai",
  "hinglish_devanagari": "...",
  "technical_terms": ["for loop", "array", "iterate"],
  "domain": "programming"
}
```

## Conventions

- Python ≥ 3.8, PEP 8, max 100-char lines, type hints, docstrings on public methods
- Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`)
- >80% test coverage required for new code
- New glossaries need ≥50 core terms and native-speaker verification
