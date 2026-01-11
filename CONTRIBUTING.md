# Contributing to Inglish Translator

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Ways to Contribute

### 1. Add Domain Glossaries

Help expand coverage by adding glossaries for new technical domains.

**Steps:**
1. Create `data/glossaries/your_domain.yaml`
2. Add at least 50 core terms
3. Include compound terms (multi-word phrases)
4. Add regex patterns if needed
5. Create sample evaluation dataset (20+ examples)
6. Submit pull request

**Example Domains Needed:**
- Chemistry
- Biology
- Medicine
- Engineering disciplines
- Business/Management
- Mathematics

### 2. Improve Translations

Enhance translation quality for existing domains.

**How:**
- Review existing translations
- Suggest better Hindi/Marathi equivalents
- Add missing terms to glossaries
- Improve regex patterns
- Report translation errors

### 3. Add Language Support

Extend support to more Indian languages.

**Priority Languages:**
- Telugu (తెలుగు)
- Tamil (தமிழ்)
- Bengali (বাংলা)
- Kannada (ಕನ್ನಡ)
- Gujarati (ગુજરાતી)

**Requirements:**
- Native speaker proficiency
- Create word mapping dictionary
- Adapt script converter
- Provide evaluation dataset

### 4. Contribute Training Data

High-quality parallel data improves the system.

**Format:**
```json
{
  "id": "unique_id",
  "english": "Technical English sentence",
  "hinglish_roman": "Natural Hinglish translation",
  "hinglish_devanagari": "Devanagari version",
  "technical_terms": ["term1", "term2"],
  "domain": "domain_name"
}
```

**Quality Standards:**
- Authentic Hinglish (as professionals actually speak)
- All technical terms preserved
- Natural grammar
- Verified by native speaker

### 5. Code Contributions

Improve the codebase.

**Areas:**
- Bug fixes
- Performance optimization
- New features
- Documentation
- Tests

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/inglish-translator.git
cd inglish-translator
git remote add upstream https://github.com/original/inglish-translator.git
```

### 2. Set Up Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e .
```

### 3. Create Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

## Code Standards

### Python Style

We follow PEP 8 with some modifications:

```bash
# Format code
make format

# Check linting
make lint

# Type checking
make typecheck
```

**Key Points:**
- Maximum line length: 100 characters
- Use type hints
- Write docstrings for all public functions
- Follow existing code style

### Docstring Format

```python
def function_name(param1: str, param2: int) -> dict:
    """
    Brief description.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Example:
        >>> result = function_name("test", 42)
        >>> print(result)
    """
    pass
```

### Testing

All new features must include tests.

```bash
# Run tests
make test

# Run specific test
pytest tests/test_pipeline.py -v

# Check coverage
pytest --cov=src tests/
```

**Test Requirements:**
- Unit tests for new functions
- Integration tests for new features
- Maintain >80% code coverage
- All tests must pass

## Pull Request Process

### 1. Before Submitting

- [ ] Code follows style guidelines
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Commits are atomic and well-described

### 2. Commit Messages

Follow conventional commits:

```
type(scope): brief description

Longer description if needed.

Fixes #issue_number
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Examples:**
```
feat(glossary): add physics domain glossary

Added 75 core physics terms including mechanics, 
thermodynamics, and quantum physics terminology.

Closes #42
```

```
fix(translator): preserve compound terms correctly

Fixed issue where multi-word terms were being split
during translation.

Fixes #56
```

### 3. Submit PR

1. Push your branch
2. Create pull request on GitHub
3. Fill out PR template
4. Wait for review
5. Address feedback
6. Merge when approved

## Review Process

### Timeline

- Initial review: Within 3 days
- Feedback response: Please respond within 7 days
- Final approval: 1-2 weeks typical

### What We Look For

- **Quality**: Code is clean, tested, documented
- **Scope**: Changes are focused and atomic
- **Value**: Contribution adds clear value
- **Compatibility**: Doesn't break existing functionality

## Domain-Specific Guidelines

### Adding Glossaries

**Structure:**
```yaml
domain: domain_name
version: "1.0"

terms:
  - term: "single_word_term"
    preserve: true
    context: "brief context"

compound_terms:
  - "multi word term"
  - "another compound"
```

**Quality Standards:**
- Minimum 50 core terms
- Include most common terms first
- Group related terms
- Provide context for ambiguous terms

### Adding Patterns

**Format:**
```json
{
  "domain_name": [
    {
      "regex": "\\bPattern\\b",
      "type": "pattern_type",
      "description": "What this matches"
    }
  ]
}
```

**Guidelines:**
- Test regex thoroughly
- Avoid overly broad patterns
- Document what each pattern matches
- Include examples

### Creating Datasets

**Requirements:**
- Minimum 20 samples for eval set
- Minimum 100 samples for training set
- Diverse sentence structures
- Verified by native speaker
- Include edge cases

**Quality Checklist:**
- [ ] Natural English source
- [ ] Authentic Hinglish translation
- [ ] All technical terms identified
- [ ] Both Roman and Devanagari provided
- [ ] No grammatical errors

## Getting Help

### Questions?

- Check [existing issues](https://github.com/yourusername/inglish-translator/issues)
- Ask in [discussions](https://github.com/yourusername/inglish-translator/discussions)
- Read [documentation](docs/)

### Found a Bug?

1. Check if already reported
2. Create new issue with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - System information
   - Code samples

### Feature Requests

1. Check existing feature requests
2. Create new issue with:
   - Use case description
   - Proposed solution
   - Alternative approaches
   - Examples

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism
- Focus on what's best for the project
- Show empathy

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Public or private harassment
- Publishing others' private information
- Unprofessional conduct

### Enforcement

Violations may result in:
1. Warning
2. Temporary ban
3. Permanent ban

Report issues to: conduct@example.com

## Recognition

Contributors are recognized in:
- README.md contributors section
- CHANGELOG.md for specific contributions
- Release notes for significant features

## Questions?

Contact: contributors@example.com

---

Thank you for contributing to democratizing technical knowledge across India! 🙏