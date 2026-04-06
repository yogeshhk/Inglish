# Domain Glossaries

Each YAML file defines the technical terms that must be **preserved in English** (not translated) for a given domain. The pipeline wraps matched terms in `[square brackets]` before sending text to the LLM, instructing the model to leave them unchanged.

## File naming

One file per domain: `<domain_name>.yaml`. The domain name in the filename must match the `domain` field inside the file and the `domain` argument passed to `TranslationConfig`.

## YAML schema

```yaml
domain: programming        # must match the filename stem
version: "2.2"             # semver string for changelog tracking

terms:                     # unigrams — looked up in O(1) via a set
  - variable
  - function
  - array

compound_terms:            # multi-word phrases — matched via a Trie
  - for loop
  - member variable
  - instance variable
```

### `terms` — single-word technical nouns

Use for individual English words that professionals keep in English when speaking (e.g. *"ek array lena hai"*). Only include **nouns and concept names**. Do not add verbs.

**Why no verbs?** Verbs like *iterate*, *compile*, *return* are handled naturally by the LLM with correct conjugation and Devanagari form (इटरेट करता है, कंपाइल करता है). Adding verbs here would force them to stay as bare English stems with no conjugation, which sounds unnatural.

### `compound_terms` — multi-word technical phrases

Use for noun phrases where the full phrase (not individual words) should be preserved — e.g. `for loop`, `member variable`, `null pointer`. The Trie matcher finds the longest possible match, so `member variable` will be preferred over matching `variable` alone.

## Adding a new domain

1. Create `src/data/glossaries/<domain>.yaml` following the schema above.
2. No code changes needed — `load_glossary(domain)` in `utils.py` discovers it automatically.
3. Aim for at least 50 core terms. Have a native speaker of the target language verify that each term is genuinely used in English form in technical speech (not translated).

## Quality guidelines

- Include plurals explicitly (`variable` and `variables`) — the matcher is exact-match on tokens.
- Prefer specificity: `null pointer` over just `pointer` if the full phrase is the standard term.
- Avoid generic English words unless they have a strong domain-specific technical meaning.
- Do not duplicate entries — the set/trie deduplicates at runtime but duplicates signal a missing lint step.
