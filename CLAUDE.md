# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Inglish** is a hybrid English → Indian language (Hindi/Marathi) framework with two modules:

1. **DocGen** — Three-tier translation pipeline that preserves technical terminology. Technical terms (function, array, for loop) survive translation intact while surrounding prose gets translated.
2. **PodGen** — Podcast generator that converts documents into a natural two-person Hinglish podcast conversation between Bunty (male) and Bubly (female), then synthesises audio via edge-tts and exports MP3/MP4 with subtitles and title card.

## Commands

All source files live in `src/`. Run commands from the repo root.

```bash
# Install dependencies
pip install -r src/requirements.txt

# System dependency for audio (PodGen):
# Windows: winget install ffmpeg
# Mac:     brew install ffmpeg
# Linux:   sudo apt install ffmpeg

# Launch unified web UI (both DocGen and PodGen)
streamlit run src/app.py

# Run examples (auto-detects LLM provider from env vars)
python src/example_usage.py

# Run all tests (run from src/)
cd src && pytest docgen/test_docgen.py podgen/test_podgen.py -v

# Run with coverage
cd src && pytest --cov=. docgen/test_docgen.py podgen/test_podgen.py

# Benchmarking
python src/docgen/baseline_benchmark.py --dataset src/data/datasets/eval/programming_eval.json --domain programming
```

## LLM Provider Setup

Groq is the recommended provider for development (fast, free tier available):
```bash
export GROQ_API_KEY=...       # recommended
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
export GEMINI_API_KEY=...
```

For local inference: Ollama or LM Studio — set provider to `ollama` or `lmstudio` in the UI.

## Project Structure

```
src/
  app.py                    # Unified Streamlit entry point (two-page app)
  shared/                   # Shared infrastructure
    llm_adapter.py          # Unified LLM abstraction (Gemini, Groq, OpenAI, …)
    utils.py                # Glossary/pattern/slangs loading, span utilities,
                            # preprocess_for_translation()
  docgen/                   # Translation module
    pipeline.py             # Main orchestrator (TranslationConfig + InglishtranslationPipeline)
    term_extractor.py       # Tier 1: Trie-based term extraction & guarding
    translator.py           # Tier 2: LLM translation (keeps [bracketed] terms intact)
    script_converter.py     # Tier 3: Roman ↔ Devanagari conversion
    baseline_benchmark.py   # Rule-based baseline evaluation
    streamlit_page.py       # DocGen Streamlit UI page
    test_docgen.py          # Unit tests (no API key required)
  podgen/                   # Podcast generation module
    document_loader.py      # PDF / DOCX / plain text → raw string
    script_generator.py     # LLM: Hinglish content → Bunty/Bubly dialogue
    audio_generator.py      # edge-tts → MP3 + SRT; Pillow title card; ffmpeg MP4
    streamlit_page.py       # PodGen Streamlit UI page
    test_podgen.py          # Unit tests (mocked LLM/audio)
  data/
    glossaries/             # Domain YAML glossaries (programming, physics, finance)
    slangs/                 # Language podcast skill files (hindi.yaml, marathi.yaml)
    datasets/               # Train/eval/test JSON datasets
```

## Three-Tier DocGen Architecture

```
English text
    │
    ▼ preprocess_for_translation() — shared/utils.py
Bullet/labeled lists flattened to prose
    │
    ▼ Tier 1: TermExtractor (docgen/term_extractor.py)
"The [for loop] iterates over the [array]"
    │
    ▼ Tier 2: LLMTranslator (docgen/translator.py)
"The [for loop] [array] ke upar iterate karta hai"
    │
    ▼ Tier 3: ScriptConverter (docgen/script_converter.py)
Roman Hinglish + Devanagari output
```

**Preprocessing** (`shared/utils.py` — `preprocess_for_translation()`):
- Runs before Tier 1; flattens structured input (labeled lists, numbered lists, bullet lists) into flowing prose so the LLM translates content rather than passing it through unchanged
- `Label: Content` lines become `"Label means that Content"` with connectors (Also, Furthermore, …)
- Section headers are detected and incorporated: `"Here are the key aspects of X: …"`

**Tier 1 — Term Extraction & Guarding** (`docgen/term_extractor.py`):
- Loads domain YAML glossary; uses a Trie for compound terms (multi-word phrases)
- `extract_terms()` returns `(term, start, end)` tuples; resolves overlaps (longest match wins)
- `guard_terms()` wraps matched terms in `[square brackets]` to protect them from LLM translation

**Tier 2 — LLM Translation** (`docgen/translator.py`):
- Prompt instructs the LLM to keep `[bracketed]` terms **exactly unchanged**
- Includes a naturalness self-check rule: LLM must read the roman output aloud mentally and revise if it sounds unnatural before returning
- `max_tokens=4096` to handle long structured paragraphs without truncation
- Robust JSON parsing: field-level regex extraction recovers roman/devanagari even from truncated responses
- `validate_constraints()` verifies all bracketed terms survived in LLM output

**Tier 3 — Script Conversion** (`docgen/script_converter.py`):
- `_ROMAN_TO_DEVA`: word-level lookup map (250+ entries); not ITRANS
- Covers common verb conjugations (`karte hain → करते हैं`), tech loanwords (`compute → कंप्यूट`, `pipeline → पाइपलाइन`), and multi-word verb phrases (`kiye ja sakte hain → किए जा सकते हैं`)
- Unknown Latin tokens (English technical terms) stay as Latin — correct code-mixing behaviour

## PodGen Architecture

```
Document (PDF/DOCX/text)
    │
    ▼ DocumentLoader (podgen/document_loader.py)
Raw English text
    │
    ▼ preprocess_for_translation() + DocGen pipeline → Hinglish Roman text
    │
    ▼ PodcastScriptGenerator (podgen/script_generator.py)
    Loads slangs skill YAML → builds LLM prompt with Bunty/Bubly personas,
    sparse slangs, topic-naming rule, naturalness self-check
    → [{speaker, text}, ...] dialogue list
    │
    ▼ AudioGenerator (podgen/audio_generator.py)
    edge-tts per turn (sequential) → pydub merge with 600 ms silence
    → MP3  +  SRT subtitle file (per-segment timestamps)
    │
    ▼ generate_title_card() → Pillow PNG (1280×720)
    ▼ mp3_to_mp4()          → ffmpeg MP4 with title card + soft subtitle track
```

**Podcast speakers:**
- **Bunty** (male, `en-IN-PrabhatNeural`) — curious learner, asks the questions everyone wants to ask
- **Bubly** (female, `en-IN-NeerjaNeural`) — clear explainer, uses a desi analogy when it fits naturally

**Slang discipline:** The prompt enforces at most 2–3 slangs across the entire script. Bubly must name the topic explicitly in turn 1. A naturalness self-check rule requires the LLM to re-read each turn before outputting.

**Audio outputs:**
- `generate(script, output_path, save_srt=True)` → MP3 + SRT (timestamps from real segment durations)
- `generate_title_card(topic, output_path)` → Pillow PNG with branding, topic, Bunty/Bubly badges
- `mp3_to_mp4(mp3, title_card_path=..., srt_path=...)` → MP4 with title card image + toggleable subtitle track

**Slangs skill files** (`data/slangs/`): YAML files per language storing speaker personas, voice IDs, slang vocabulary, and the podcast prompt template. Add a new language by creating `data/slangs/<language>.yaml`.

## LLM Abstraction (`shared/llm_adapter.py`)
- Unified interface over Gemini, Groq, OpenAI, Anthropic, Ollama, LM Studio
- Built-in exponential backoff + jitter for 429 rate-limit errors
- No LangChain — uses provider native SDKs directly

## Domain Glossaries

Glossaries are in `src/data/glossaries/` as YAML. Adding a new domain requires only a new YAML file — no code changes.

```yaml
domain: programming
terms:          # unigrams — O(1) set lookup
  - variable
  - function
  - generator   # include both singular and plural forms
  - generators
  - yield
compound_terms: # multi-word — Trie lookup
  - for loop
  - yield statement
  - member variable
```

**Glossary discipline:** Only include nouns and noun phrases that professionals genuinely say in English while speaking the target language. Avoid overly generic words (`key`, `keys`) that appear in non-technical contexts — they cause over-guarding and confuse the LLM.

## Conventions

- Python ≥ 3.8, PEP 8, max 100-char lines, type hints, docstrings on public methods
- Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`)
- >80% test coverage required for new code
- New glossaries need ≥50 core terms and native-speaker verification
- New language slangs files must pass `TestSlangYAML` parametrized tests
