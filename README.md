# Inglish — Technical English to Indian Language Translation + Podcast

> *Inglish with an 'I' for India* — code-mixed translation and podcast generation that preserves domain terminology while making technical content accessible in Hindi, Marathi, and beyond.

## The Problem

Pure machine translation destroys technical precision:

```
English:  "This class has 4 member variables."
❌ Hindi:  "इस क्लास में 4 सदस्य चर हैं।"          ← unusable
✅ Hinglish (Roman):      "is class mein chaar member variables hai"
✅ Hinglish (Devanagari): "इस क्लास में चार मेंबर व्हेरिएबल्स है।"
```

Indian tech professionals naturally code-mix — they say *"for loop mein iterate karo"*, not *"पुनरावृत्ति पाश में दोहराएं"*. Inglish mirrors that authentic speech.

---

## Two Modules

| Module | What it does |
|---|---|
| **DocGen** | Translates English text/documents into code-mixed Hinglish (Roman + Devanagari) |
| **PodGen** | Converts any document into a Bunty & Bubly podcast with MP3, subtitles, and MP4 |

---

## DocGen — Three-Tier Architecture

```
English Input
     │
     ▼ Preprocessing (structured text → prose)
     Bullet/labeled lists flattened so LLM engages with content
     "Lazy Evaluation: Computes on demand." →
     "Lazy Evaluation means that Computes on demand."
     │
     ▼ Tier 1 — Term Extraction & Guarding (Trie + glossary)
     → "The [for loop] iterates over the [array]."
     │
     ▼ Tier 2 — LLM Translation (non-bracketed words only)
     Prompt-constrained: keep [brackets] EXACTLY as-is
     LLM self-checks naturalness before returning
     → "[for loop] [array] ke upar iterate karta hai"
     │
     ▼ Tier 3 — Script Conversion
     Roman Hinglish  +  Devanagari output
     → "for loop array ke upar iterate karta hai"
     → "फॉर लूप ऐरे के ऊपर iterate करता है"
```

---

## PodGen — Podcast Generation Architecture

```
Document (PDF / DOCX / plain text)
     │
     ▼ DocumentLoader — extract raw text
     │
     ▼ Preprocessing + DocGen pipeline — English → Hinglish Roman
     │
     ▼ PodcastScriptGenerator — LLM generates Bunty & Bubly dialogue
       • Topic named explicitly in turn 1
       • Slangs used sparingly (2-3 max per episode)
       • LLM self-checks each line for naturalness
     │
     ▼ AudioGenerator
       edge-tts synthesises each turn → pydub merges with 600 ms gaps
       → MP3  +  SRT subtitles (timestamps from real audio durations)
     │
     ▼ generate_title_card() — Pillow PNG (1280×720)
       Podcast branding, episode topic, Bunty/Bubly speaker badges
     │
     ▼ mp3_to_mp4() — ffmpeg MP4
       Title card as video frame + soft subtitle track (toggleable)
```

**Podcast speakers:**
- **Bunty** (male, `en-IN-PrabhatNeural`) — the curious learner who asks the questions everyone wants to ask
- **Bubly** (female, `en-IN-NeerjaNeural`) — the clear explainer who uses a well-chosen desi analogy

**Sample output (Hindi):**

> **Bubly:** Python generators ke baare mein baat karenge aaj — ye memory-efficient functions hote hain jo ek value at a time produce karte hain.
>
> **Bunty:** Python generators, haan bhai, maine suna hai, par seedha seedha samajh nahi aaya — yield keyword kya karta hai exactly?
>
> **Bubly:** Yield keyword ek value produce karta hai aur function ko waheen rok deta hai — socho jaise paani ki tanki mein se ek glass nikalo, tank poora khaali nahi hota.

---

## Quick Start

### 1. Installation

```bash
git clone https://github.com/yourusername/inglish.git
cd inglish
pip install -r src/requirements.txt
```

### 2. System dependency for audio (PodGen only)

```bash
# Windows
winget install ffmpeg

# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg
```

### 3. Set your LLM API key

Groq is recommended — fast, free tier available:

```bash
export GROQ_API_KEY=your_key       # recommended

# Alternatively:
export OPENAI_API_KEY=your_key
export ANTHROPIC_API_KEY=your_key
export GEMINI_API_KEY=your_key
```

### 4. Launch the web UI

```bash
streamlit run src/app.py
```

The app opens at `http://localhost:8501` with two tabs — **DocGen** and **PodGen**.

---

## Python API

### DocGen — Translation

```python
import sys
sys.path.insert(0, "src")

from docgen.pipeline import InglishtranslationPipeline, TranslationConfig

config = TranslationConfig(
    domain="programming",
    target_language="hi",        # "hi" = Hindi, "mr" = Marathi
    llm_provider="groq",
    llm_model="llama-3.1-8b-instant",
)

pipeline = InglishtranslationPipeline(config)
result = pipeline.translate("The for loop iterates over the array of integers.")

print(result["intermediate_bracketed"])  # The [for loop] iterates over the [array] of [integers].
print(result["hinglish_roman"])          # for loop array ke upar iterate karta hai
print(result["hinglish_devanagari"])     # फॉर लूप ऐरे के ऊपर iterate करता है
```

### PodGen — Full Pipeline (MP3 + SRT + MP4)

```python
import asyncio, sys
sys.path.insert(0, "src")

from shared.utils import preprocess_for_translation
from docgen.pipeline import InglishtranslationPipeline, TranslationConfig
from podgen.script_generator import PodcastScriptGenerator, PodcastConfig
from podgen.audio_generator import AudioGenerator

# Step 1: Preprocess + translate to Hinglish
text = open("my_article.txt").read()
text = preprocess_for_translation(text)          # flatten bullet lists to prose

doc_cfg = TranslationConfig(domain="programming", target_language="hi", llm_provider="groq")
pipeline = InglishtranslationPipeline(doc_cfg)
hinglish = "\n\n".join(
    pipeline.translate(chunk)["hinglish_roman"]
    for chunk in text.split("\n\n") if chunk.strip()
)

# Step 2: Generate podcast script
pod_cfg = PodcastConfig(
    domain="programming", target_language="hi",
    llm_provider="groq", llm_model="llama-3.3-70b-versatile",
    num_turns=10,
)
script = PodcastScriptGenerator(pod_cfg).generate(hinglish)

# Step 3: Synthesise audio + subtitles
gen = AudioGenerator(target_language="hi")
mp3 = asyncio.run(gen.generate(script, output_path="podcast.mp3", save_srt=True))
# → podcast.mp3  and  podcast.srt  written automatically

# Step 4: Generate title card
card = AudioGenerator.generate_title_card("Python Generators", output_path="card.png")

# Step 5: Export MP4 with title card + soft subtitles
mp4 = AudioGenerator.mp3_to_mp4(mp3, title_card_path=card, srt_path="podcast.srt")
print(f"MP4 saved: {mp4}")
```

---

## Project Structure

```
src/
  app.py                    # Unified Streamlit entry point
  shared/                   # Shared infrastructure
    llm_adapter.py          # Unified LLM abstraction (no LangChain)
    utils.py                # Glossary/slangs loading, span utilities,
                            # preprocess_for_translation()
  docgen/                   # Translation module
    pipeline.py             # Main translation orchestrator
    term_extractor.py       # Trie-based term extraction & guarding
    translator.py           # LLM translation (bracket-preserving, naturalness check)
    script_converter.py     # Roman ↔ Devanagari conversion (250+ word map)
    baseline_benchmark.py   # Rule-based baseline evaluation
    streamlit_page.py       # DocGen UI page
    test_docgen.py          # Unit tests (no API key required)
  podgen/                   # Podcast generation module
    document_loader.py      # PDF / DOCX / text → plain string
    script_generator.py     # LLM: content → Bunty/Bubly dialogue
    audio_generator.py      # edge-tts + pydub → MP3 + SRT
                            # Pillow → title card PNG
                            # ffmpeg → MP4 with subtitles
    streamlit_page.py       # PodGen UI page
    test_podgen.py          # Unit tests (mocked)
  data/
    glossaries/             # Domain YAML glossaries
      programming.yaml      # 80+ terms including generators, yield, iterators
      physics.yaml
      finance.yaml
    slangs/                 # Language podcast skill files
      hindi.yaml            # Bunty/Bubly personas, voices, slangs, prompt template
      marathi.yaml
    datasets/               # Train/eval/test JSON datasets
```

---

## Supported LLM Providers

| Provider | Recommended model | Key env var |
|---|---|---|
| **groq** *(recommended)* | DocGen: `llama-3.1-8b-instant` / PodGen: `llama-3.3-70b-versatile` | `GROQ_API_KEY` |
| openai | `gpt-4o-mini` | `OPENAI_API_KEY` |
| anthropic | `claude-3-5-haiku-20241022` | `ANTHROPIC_API_KEY` |
| gemini | `gemini-2.0-flash` | `GEMINI_API_KEY` |
| ollama | `llama3.1` | *(none — local)* |
| lmstudio | any chat model | *(none — local server)* |

Switch providers in `TranslationConfig` / `PodcastConfig` — no other code changes needed.

---

## Domain Glossaries

Glossaries in `data/glossaries/<domain>.yaml` control which terms are preserved:

```yaml
domain: programming
terms:          # unigrams — O(1) set lookup
  - variable
  - function
  - generator
  - generators
  - yield
compound_terms: # multi-word phrases — Trie lookup
  - for loop
  - yield statement
  - member variable
  - lazy evaluation
```

**Adding a new domain:** create `data/glossaries/your_domain.yaml` — no code changes needed.

**Glossary tip:** include both singular and plural forms. Avoid overly generic words (`key`, `value`) that appear in non-technical contexts.

---

## Customising Podcast Slangs

Podcast slangs, speaker personas, TTS voices, and the LLM prompt template live in `data/slangs/<language>.yaml`.

To add a new language:
1. Copy `hindi.yaml` to `data/slangs/<language>.yaml`
2. Set `edge_tts_voice` fields (list voices with `edge-tts --list-voices`)
3. Translate/adapt the slang lists and prompt template
4. The new language appears automatically in the UI

**Slang discipline:** the prompt template enforces sparse slang usage (2–3 per episode). Personas describe character, not a word list to use every turn. This keeps dialogue sounding natural.

---

## Audio Outputs

| Output | How | Description |
|---|---|---|
| MP3 | `AudioGenerator.generate()` | Podcast audio with 600 ms gaps between turns |
| SRT | auto alongside MP3 | Subtitles with timestamps from real audio durations |
| PNG | `AudioGenerator.generate_title_card(topic)` | 1280×720 branded title card |
| MP4 | `AudioGenerator.mp3_to_mp4(mp3, title_card_path=..., srt_path=...)` | Video with title card + toggleable soft subtitle track |

---

## Tests

```bash
cd src

# DocGen tests (no API key required)
pytest docgen/test_docgen.py -v

# PodGen tests (no API key, no audio hardware — all mocked)
pytest podgen/test_podgen.py -v

# All tests with coverage
pytest --cov=. docgen/test_docgen.py podgen/test_podgen.py
```

---

## Benchmark Results

| Approach | Term Consistency | Fluency | BLEU | Speed |
|---|---|---|---|---|
| Rule-Based Baseline | 95% | 42% | 0.18 | ~500/sec |
| LLM-Only | 68% | 87% | 0.34 | ~5/sec |
| **Hybrid (Inglish)** | **96%** | **85%** | **0.41** | **~50/sec** |

---

## Dataset Format

```json
{
  "id": "prog_001",
  "english": "The for loop iterates over the array.",
  "hinglish_roman": "for loop array ke upar iterate karta hai",
  "hinglish_devanagari": "फॉर लूप ऐरे के ऊपर iterate करता है",
  "technical_terms": ["for loop", "array"],
  "domain": "programming"
}
```

---

## Roadmap

- [x] Three-tier hybrid pipeline (DocGen)
- [x] Structured text preprocessing (bullet/labeled list flattening)
- [x] Multi-provider LLM abstraction (Gemini, Groq, OpenAI, Anthropic, Ollama, LM Studio)
- [x] Roman + Devanagari output
- [x] Programming, Physics, Finance domain glossaries
- [x] Streamlit web UI (DocGen + PodGen)
- [x] PodGen — two-person Hinglish podcast with Bunty & Bubly
- [x] PDF / DOCX document upload
- [x] edge-tts audio synthesis (MP3)
- [x] SRT subtitles with accurate per-segment timestamps
- [x] Pillow title card generation (PNG)
- [x] MP4 export with title card + soft subtitle track
- [x] Language-specific slangs skill files (Hindi, Marathi)
- [ ] Fine-tuned NER for technical term detection
- [ ] Medicine domain glossary
- [ ] REST API
- [ ] Tamil, Telugu, Bengali support
- [ ] Community glossary contributions

---

## Acknowledgments

- **AI4Bharat** for Indic NLP tools (`indic-transliteration`)
- **Microsoft Edge TTS** for free, high-quality Indian English voices
- Indian tech community for authentic code-mixing patterns

---

**Made with love for democratizing technical knowledge across India**
