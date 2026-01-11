# Getting Started with Inglish Translator

This guide will help you get up and running with the Inglish Translation framework in 5 minutes.

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/inglish-translator.git
cd inglish-translator

# Run quick start script
chmod +x quickstart.sh
./quickstart.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Your First Translation

```python
from pipeline import InglishtranslationPipeline, TranslationConfig

# Configure pipeline
config = TranslationConfig(
    domain="programming",
    target_language="hi",
    output_format="both"
)

# Create and use pipeline
pipeline = InglishtranslationPipeline(config)
result = pipeline.translate("The for loop iterates over the array.")

print("Roman:", result['hinglish_roman'])
print("Devanagari:", result['hinglish_devanagari'])
```

**Output:**
```
Roman: for loop array ke upar iterate karta hai
Devanagari: फॉर लूप ऐरे के ऊपर iterate करता है
```

### 3. Run Examples

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Run usage examples
python examples/basic_usage.py

# Or use Make
make example
```

### 4. Run Benchmark

```bash
# Run baseline benchmark
make benchmark

# Results will be saved to results/baseline_results.json
```

## Understanding the Output

### Roman Script (Hinglish)
Phonetic representation using Roman alphabet:
```
"for loop array ke upar iterate karta hai"
```

### Devanagari Script
Same content in Devanagari:
```
"फॉर लूप ऐरे के ऊपर iterate करता है"
```

### Technical Terms Preserved
Notice how `for loop`, `array`, and `iterate` remain in English while the connecting grammar is in Hindi.

## Project Structure

```
inglish-translator/
├── src/                    # Source code
│   ├── pipeline.py         # Main pipeline
│   ├── term_extractor.py   # Term extraction
│   ├── translator.py       # Translation modules
│   └── script_converter.py # Script conversion
│
├── data/
│   ├── glossaries/         # Domain glossaries
│   ├── patterns/           # Regex patterns
│   └── datasets/           # Training/eval data
│
├── benchmarks/             # Benchmark scripts
├── examples/               # Usage examples
├── tests/                  # Unit tests
└── notebooks/              # Jupyter notebooks
```

## Common Tasks

### Translate Text

```python
from pipeline import InglishtranslationPipeline, TranslationConfig

config = TranslationConfig(domain="programming", target_language="hi")
pipeline = InglishtranslationPipeline(config)

text = "Your English sentence here"
result = pipeline.translate(text)
```

### Translate Multiple Texts

```python
texts = [
    "First sentence",
    "Second sentence",
    "Third sentence"
]

results = pipeline.translate_batch(texts)

for r in results:
    print(r['hinglish_roman'])
```

### Extract Technical Terms

```python
from term_extractor import TermExtractor

extractor = TermExtractor("programming")
terms = extractor.extract_terms("The for loop iterates over the array.")

print([t[0] for t in terms])
# Output: ['for loop', 'array', 'iterates']
```

### Evaluate Quality

```python
metrics = pipeline.evaluate_quality(
    original="The loop iterates",
    translated="loop iterate karta hai",
    reference="loop iterate karta hai"  # optional
)

print(f"Terminology preserved: {metrics['terminology_preservation']*100:.1f}%")
```

## Available Commands

```bash
# Show all available commands
make help

# Install dependencies
make install

# Run tests
make test

# Run examples
make example

# Run benchmark
make benchmark

# Format code
make format

# Lint code
make lint

# Clean generated files
make clean
```

## Configuration Options

### Domains

Currently supported:
- `programming` - Software development terms
- `physics` - Physics terminology
- `finance` - Financial terms

### Languages

Currently supported:
- `hi` - Hindi (हिंदी)
- `mr` - Marathi (मराठी) - Partial support
- `te` - Telugu (తెలుగు) - Partial support

### Translator Types

- `baseline` - Simple rule-based (fast, consistent)
- `llm` - LLM-based (high quality, requires API key)

### Output Formats

- `roman` - Roman script only
- `devanagari` - Devanagari script only
- `both` - Both scripts

## Working with Datasets

### Load Dataset

```python
from utils import load_json_dataset

dataset = load_json_dataset("data/datasets/eval/programming_eval.json")

for sample in dataset:
    print(sample['english'])
    print(sample['hinglish_roman'])
```

### Create Custom Dataset

```json
{
  "dataset_name": "my_dataset",
  "domain": "programming",
  "samples": [
    {
      "id": "001",
      "english": "Your English text",
      "hinglish_roman": "Your Hinglish text",
      "technical_terms": ["term1", "term2"]
    }
  ]
}
```

## Adding New Domains

### 1. Create Glossary

Create `data/glossaries/your_domain.yaml`:

```yaml
domain: your_domain
version: "1.0"

terms:
  - term: "technical_term"
    preserve: true
    
compound_terms:
  - "multi word term"
```

### 2. Add Patterns (Optional)

Update `data/patterns/regex_patterns.json`:

```json
{
  "your_domain": [
    {
      "regex": "\\bYourPattern\\b",
      "type": "your_type"
    }
  ]
}
```

### 3. Prepare Data

Create training/evaluation datasets following the standard format.

### 4. Test

```python
config = TranslationConfig(domain="your_domain")
pipeline = InglishtranslationPipeline(config)
result = pipeline.translate("Your domain-specific text")
```

## Troubleshooting

### "Glossary not found" Error

**Problem:** Glossary file missing for the domain.

**Solution:**
```bash
# Check if glossary exists
ls data/glossaries/

# Create glossary if needed
cp data/glossaries/programming.yaml data/glossaries/your_domain.yaml
# Edit as needed
```

### Poor Translation Quality

**Problem:** Translations don't look natural.

**Solutions:**
1. Add more domain-specific terms to glossary
2. Improve regex patterns for term extraction
3. Try LLM-based translator (requires API key)

### Terms Not Being Preserved

**Problem:** Technical terms are being translated incorrectly.

**Solutions:**
1. Add terms to glossary
2. Check term extraction: `extractor.extract_terms(text)`
3. Verify patterns in `regex_patterns.json`

## Next Steps

1. **Run the Jupyter Notebook**
   ```bash
   jupyter notebook notebooks/01_quick_demo.ipynb
   ```

2. **Read the Full Documentation**
   - [API Reference](docs/API_REFERENCE.md)
   - [Architecture](docs/ARCHITECTURE.md)
   - [Research Framework](docs/research_framework.md)

3. **Try Advanced Features**
   - Custom glossaries
   - LLM-based translation
   - Batch processing
   - Quality evaluation

4. **Contribute**
   - Add new domains
   - Improve translations
   - Report issues
   - Submit pull requests

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/yourusername/inglish-translator/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/inglish-translator/discussions)
- **Email**: your.email@example.com

## Quick Reference

### Most Common Usage

```python
from pipeline import InglishtranslationPipeline, TranslationConfig

# Setup
config = TranslationConfig(domain="programming", target_language="hi")
pipeline = InglishtranslationPipeline(config)

# Translate
result = pipeline.translate("Your English text here")

# Access results
print(result['hinglish_roman'])      # Roman script
print(result['hinglish_devanagari']) # Devanagari script
print(result['metadata']['technical_terms'])  # Terms extracted
```

### Command Line

```bash
# Run benchmark
python benchmarks/baseline_benchmark.py \
    --dataset data/datasets/eval/programming_eval.json \
    --domain programming \
    --output results/results.json
```

---

**You're all set!** Start translating technical content to make it accessible across India. 🚀