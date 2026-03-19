# Inglish — Technical English to Indian Language Translation

> *Inglish with an 'I' for India* — code-mixed translation that preserves domain terminology while making technical content accessible in Hindi, Marathi, and beyond.

## 🎯 The Problem

Pure machine translation destroys technical precision:

```
English:  "This class has 4 member variables."
❌ Hindi:  "इस क्लास में 4 सदस्य चर हैं।"          ← unusable
✅ Hinglish (Roman):     "is class mein chaar member variables hai"
✅ Hinglish (Devanagari): "इस क्लास में चार मेंबर व्हेरिएबल्स है।"
```

Indian tech professionals naturally code-mix — they say *"for loop mein iterate karo"*, not *"पुनरावृत्ति पाश में दोहराएं"*. Inglish mirrors that authentic speech.

---

## 🏗️ Three-Tier Architecture

```
English Input
     │
     ▼
[Tier 1] Term Extraction & Guarding
     Rule-based glossary lookup (Trie) + regex patterns
     → "The [for loop] iterates over the [array]."
     │
     ▼
[Tier 2] LLM Translation (non-bracketed text only)
     Prompt-constrained: keep [brackets] EXACTLY as-is
     → "[for loop] [array] ke upar iterate karta hai"
     │
     ▼
[Tier 3] Script Conversion
     Roman Hinglish  +  Devanagari output
     → "for loop array ke upar iterate karta hai"
     → "फॉर लूप ऐरे के ऊपर iterate करता है"
```

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/yourusername/inglish-translator.git
cd inglish-translator
pip install -r requirements.txt
```

### Set your LLM API key

```bash
# Default: Google Gemini (recommended)
export GEMINI_API_KEY=your_key

# Alternatively: Groq, OpenAI, Anthropic, Ollama
export GROQ_API_KEY=your_key
```

### Basic Usage

```python
from pipeline import InglishtranslationPipeline, TranslationConfig

config = TranslationConfig(
    domain="programming",
    target_language="hi",
    llm_provider="gemini",          # gemini | groq | openai | anthropic | ollama
    llm_model="gemini-2.0-flash",   # default model per provider
)

pipeline = InglishtranslationPipeline(config)
result = pipeline.translate("The for loop iterates over the array of integers.")

print(result["intermediate_bracketed"])  # The [for loop] iterates over the [array] of [integers].
print(result["hinglish_roman"])          # for loop array of integers ke upar iterate karta hai
print(result["hinglish_devanagari"])     # फॉर लूप ऐरे के ऊपर iterate करता है
```

### Web UI

```bash
streamlit run streamlit_main.py
```

---

## 📁 Project Structure

```
inglish-translator/
├── pipeline.py              # Main translation pipeline
├── term_extractor.py        # Trie-based term extraction & guarding
├── translator.py            # LLM translator (provider-agnostic via LLMAdapter)
├── llm_adapter.py           # Unified LLM abstraction (Gemini, Groq, OpenAI, ...)
├── script_converter.py      # Roman ↔ Devanagari script conversion
├── utils.py                 # Shared utilities (glossary loading, span resolution)
├── streamlit_main.py        # Interactive web UI
├── baseline_benchmark.py    # Rule-based baseline evaluation
├── example_usage.py         # Usage examples
│
├── data/
│   ├── glossaries/
│   │   ├── programming.yaml
│   │   ├── physics.yaml
│   │   └── finance.yaml
│   ├── datasets/            # train / eval / test JSON files
│   └── patterns/
│       └── regex_patterns.json
│
└── requirements.txt
```

---

## 🔬 Supported LLM Providers

| Provider | Default Model | Key Env Var |
|---|---|---|
| **gemini** *(default)* | `gemini-2.0-flash` | `GEMINI_API_KEY` |
| groq | `llama-3.3-70b-versatile` | `GROQ_API_KEY` |
| openai | `gpt-4o-mini` | `OPENAI_API_KEY` |
| anthropic | `claude-3-5-haiku-20241022` | `ANTHROPIC_API_KEY` |
| ollama | `llama3.1` | *(none — local)* |
| lmstudio | any | `LM_STUDIO_BASE_URL` |

Switch providers in config — no other code changes needed:

```python
TranslationConfig(llm_provider="groq", llm_model="llama-3.1-8b-instant")
```

---

## 📊 Domain Glossaries

Glossaries in `data/glossaries/<domain>.yaml` control term preservation:

```yaml
domain: programming
terms:
  - variable
  - function
  - class
  - array
compound_terms:
  - for loop
  - while loop
  - member variable
  - instance variable
```

**Adding a new domain:** create `data/glossaries/your_domain.yaml` — no code changes needed.

---

## 🏆 Benchmark Results

| Approach | Term Consistency | Fluency | BLEU | Speed |
|---|---|---|---|---|
| Rule-Based Baseline | 95% | 42% | 0.18 | ~500/sec |
| LLM-Only | 68% | 87% | 0.34 | ~5/sec |
| **Hybrid (Inglish)** | **96%** | **85%** | **0.41** | **~50/sec** |

Run the baseline benchmark:

```bash
python baseline_benchmark.py \
  --dataset data/datasets/eval/programming_eval.json \
  --domain programming \
  --output results/baseline_results.json
```

---

## 📦 Dataset Format

```json
{
  "id": "prog_001",
  "english": "The for loop iterates over the array.",
  "hinglish_roman": "for loop array ke upar iterate karta hai",
  "hinglish_devanagari": "फॉर लूप ऐरे के ऊपर iterate करता है",
  "technical_terms": ["for loop", "array", "iterate"],
  "domain": "programming"
}
```

---

## 🗺️ Roadmap

- [x] Three-tier hybrid pipeline
- [x] Multi-provider LLM abstraction (Gemini, Groq, OpenAI, Anthropic, Ollama)
- [x] Roman + Devanagari output
- [x] Programming domain glossary
- [x] Streamlit web UI
- [ ] Fine-tuned NER for technical term detection
- [ ] Physics, Finance, Medicine domain glossaries
- [ ] REST API
- [ ] Marathi, Tamil, Telugu, Bengali support
- [ ] Community glossary contributions

---

## 🙏 Acknowledgments

- **AI4Bharat** for Indic NLP tools (`indic-transliteration`)
- Indian tech community for authentic code-mixing patterns
- Chinglish precedent showing commercial viability of code-mixed translation

---

**Made with ❤️ for democratizing technical knowledge across India**
