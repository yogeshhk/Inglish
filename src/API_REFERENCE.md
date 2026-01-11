# API Reference

Complete API documentation for the Inglish Translation framework.

## Core Classes

### TranslationConfig

Configuration dataclass for the translation pipeline.

```python
@dataclass
class TranslationConfig:
    domain: str = "programming"           # Domain name
    target_language: str = "hi"           # Target language code
    translator_type: str = "baseline"     # 'baseline' or 'llm'
    output_format: str = "both"           # 'roman', 'devanagari', or 'both'
    llm_model: Optional[str] = "gpt-3.5-turbo"
    llm_api_key: Optional[str] = None
    temperature: float = 0.3
```

**Parameters:**
- `domain`: Domain of technical content (e.g., 'programming', 'physics', 'finance')
- `target_language`: ISO 639-1 code ('hi'=Hindi, 'mr'=Marathi, 'te'=Telugu, etc.)
- `translator_type`: Translation approach to use
- `output_format`: Desired output script format(s)
- `llm_model`: LLM model name (if using LLM translator)
- `llm_api_key`: API key for LLM service
- `temperature`: LLM temperature for consistency (0.0-1.0)

---

### InglishtranslationPipeline

Main translation pipeline orchestrating all components.

#### Constructor

```python
pipeline = InglishtranslationPipeline(config: TranslationConfig)
```

#### Methods

##### `translate(text: str, verbose: bool = False) -> Dict[str, str]`

Translate a single English text to Inglish.

**Parameters:**
- `text`: Input English text
- `verbose`: Print intermediate processing steps

**Returns:**
```python
{
    "original_english": str,
    "hinglish_roman": str,           # Roman script output
    "hinglish_devanagari": str,      # Devanagari script output
    "metadata": {
        "domain": str,
        "target_language": str,
        "translator_type": str,
        "terms_extracted": int,
        "technical_terms": List[str]
    }
}
```

**Example:**
```python
result = pipeline.translate("The for loop iterates over the array.")
print(result['hinglish_roman'])
# Output: "for loop array ke upar iterate karta hai"
```

##### `translate_batch(texts: List[str], verbose: bool = False) -> List[Dict]`

Translate multiple texts in batch.

**Parameters:**
- `texts`: List of English input texts
- `verbose`: Print progress information

**Returns:** List of translation result dictionaries

**Example:**
```python
texts = [
    "The function returns a value.",
    "Objects have instance variables."
]
results = pipeline.translate_batch(texts)
```

##### `evaluate_quality(original: str, translated: str, reference: str = None) -> Dict[str, float]`

Evaluate translation quality metrics.

**Parameters:**
- `original`: Original English text
- `translated`: Translated Inglish text
- `reference`: Optional reference translation

**Returns:**
```python
{
    "terminology_preservation": float,  # 0.0-1.0
    "length_ratio": float,
    "word_overlap": float              # Only if reference provided
}
```

---

### TermExtractor

Extract and guard technical terms from text.

#### Constructor

```python
extractor = TermExtractor(domain: str)
```

#### Methods

##### `extract_terms(text: str) -> List[Tuple[str, int, int]]`

Extract all technical terms from text.

**Returns:** List of `(term, start_index, end_index)` tuples

**Example:**
```python
terms = extractor.extract_terms("The for loop iterates.")
# [(for loop, 4, 12), (iterates, 13, 21)]
```

##### `guard_terms(text: str, terms: List = None) -> str`

Add square brackets around technical terms.

**Example:**
```python
guarded = extractor.guard_terms("The for loop iterates.")
# "The [for loop] [iterates]."
```

##### `unguard_terms(text: str) -> str`

Remove square brackets from text.

##### `get_guarded_terms(text: str) -> List[str]`

Extract list of currently bracketed terms.

---

### BaselineTranslator

Simple rule-based translator (baseline approach).

#### Constructor

```python
translator = BaselineTranslator(target_language: str = "hi")
```

#### Methods

##### `translate(text: str) -> str`

Translate text using rule-based approach.

**Example:**
```python
result = translator.translate("The [array] has [values].")
# "[array] mein [values] hain"
```

##### `validate_constraints(original: str, translated: str) -> bool`

Verify that bracketed terms are preserved exactly.

---

### LLMTranslator

LLM-based translator using OpenAI or Anthropic APIs.

#### Constructor

```python
translator = LLMTranslator(
    target_language: str = "hi",
    model: str = "gpt-3.5-turbo",
    api_key: str = None
)
```

#### Methods

##### `translate(text: str) -> str`

Translate using LLM with constraint prompting.

**Note:** Requires API key to be set. Falls back to baseline if unavailable.

---

### ScriptConverter

Convert between Roman and Devanagari scripts.

#### Constructor

```python
converter = ScriptConverter(target_language: str = "hi")
```

#### Methods

##### `devanagari_to_roman(text: str) -> str`

Convert Devanagari text to Roman script.

##### `roman_to_devanagari_simple(text: str) -> str`

Convert Roman text to Devanagari (simplified).

##### `convert_mixed_text(text: str, to_format: str = "roman") -> str`

Convert mixed language text to desired format.

**Parameters:**
- `to_format`: 'roman' or 'devanagari'

##### `generate_bilingual_output(english: str, translated: str) -> Dict`

Generate output in multiple formats.

---

## Utility Functions

### `load_glossary(domain: str, glossary_dir: str = "data/glossaries") -> Dict`

Load domain-specific glossary from YAML file.

### `load_patterns(domain: str, pattern_dir: str = "data/patterns") -> List`

Load regex patterns for term detection.

### `build_trie(words: List[str]) -> Dict`

Build Trie data structure for efficient term matching.

### `extract_bracketed_terms(text: str) -> List[str]`

Extract all terms within square brackets.

### `remove_brackets(text: str) -> str`

Remove square brackets while keeping content.

### `load_json_dataset(file_path: str) -> List[Dict]`

Load dataset from JSON file.

### `save_json_dataset(data: List[Dict], file_path: str)`

Save dataset to JSON file.

---

## Command Line Interface

### Baseline Benchmark

```bash
python benchmarks/baseline_benchmark.py \
    --dataset data/datasets/eval/programming_eval.json \
    --domain programming \
    --output results/baseline_results.json \
    --verbose
```

**Arguments:**
- `--dataset`: Path to evaluation dataset (required)
- `--domain`: Domain name (default: programming)
- `--output`: Output path for results
- `--verbose`: Print detailed output

---

## Dataset Format

### Training/Evaluation Dataset

```json
{
  "dataset_name": "programming_hinglish_eval",
  "domain": "programming",
  "language_pair": "en_hi",
  "size": 20,
  "samples": [
    {
      "id": "prog_001",
      "english": "The for loop iterates over the array.",
      "hinglish_roman": "for loop array ke upar iterate karta hai",
      "hinglish_devanagari": "फॉर लूप ऐरे के ऊपर iterate करता है",
      "technical_terms": ["for loop", "array", "iterate"],
      "domain": "programming"
    }
  ]
}
```

### Glossary Format

```yaml
domain: programming
version: "1.0"

terms:
  - term: "variable"
    preserve: true
    context: "data storage element"

compound_terms:
  - "for loop"
  - "member variable"

patterns:
  - regex: '\w+\(\)'
    type: "function_call"
```

---

## Error Handling

All methods handle errors gracefully:

```python
try:
    result = pipeline.translate(text)
except FileNotFoundError:
    # Glossary file not found
    pass
except Exception as e:
    # Other errors
    pass
```

---

## Performance Characteristics

| Component | Time Complexity | Space Complexity |
|-----------|----------------|------------------|
| Term Extraction (Trie) | O(n) | O(m) where m = glossary size |
| Baseline Translation | O(n) | O(n) |
| LLM Translation | O(API latency) | O(n) |
| Script Conversion | O(n) | O(1) |

Where n = text length

---

## Extension Points

### Adding New Domains

1. Create glossary: `data/glossaries/your_domain.yaml`
2. Add patterns: Update `data/patterns/regex_patterns.json`
3. Prepare training data in standard format

### Custom Translators

Extend `BaseTranslator`:

```python
class CustomTranslator(BaseTranslator):
    def translate(self, text: str) -> str:
        # Your custom logic
        return translated_text
```

### Custom Term Extractors

Extend or modify `TermExtractor` methods for domain-specific extraction logic.