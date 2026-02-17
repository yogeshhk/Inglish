#!/usr/bin/env python3
"""
Example usage of the Inglish Translation Pipeline.
"""

import sys
from pathlib import Path

# Add the directory containing this file to sys.path so that pipeline.py
# and its siblings (term_extractor, translator, etc.) can be imported
# regardless of the working directory the script is launched from.
sys.path.insert(0, str(Path(__file__).parent))

from pipeline import InglishtranslationPipeline, TranslationConfig


def example_simple_translation():
    """Simple translation example."""
    print("="*60)
    print("Example 1: Simple Translation")
    print("="*60)
    
    # Configure pipeline
    config = TranslationConfig(
        domain="programming",
        target_language="hi",
        translator_type="baseline",
        output_format="both"
    )
    
    # Create pipeline
    pipeline = InglishtranslationPipeline(config)
    
    # Translate
    text = "The for loop iterates over the array of integers."
    result = pipeline.translate(text, verbose=True)
    
    print("\n" + "="*60)
    print("OUTPUT")
    print("="*60)
    print(f"Roman:      {result['hinglish_roman']}")
    print(f"Devanagari: {result['hinglish_devanagari']}")
    print(f"Terms:      {result['metadata']['technical_terms']}")
    print("="*60 + "\n")


def example_batch_translation():
    """Batch translation example."""
    print("="*60)
    print("Example 2: Batch Translation")
    print("="*60)
    
    # Configure pipeline
    config = TranslationConfig(
        domain="programming",
        target_language="hi",
        translator_type="baseline",
        output_format="roman"
    )
    
    pipeline = InglishtranslationPipeline(config)
    
    # Multiple texts
    texts = [
        "This class has four member variables.",
        "The function returns a boolean value.",
        "Each object has its own instance variables.",
    ]
    
    # Translate all
    results = pipeline.translate_batch(texts, verbose=False)
    
    print("\n" + "="*60)
    print("BATCH OUTPUT")
    print("="*60)
    for i, (text, result) in enumerate(zip(texts, results), 1):
        print(f"\n[{i}] English: {text}")
        print(f"    Roman:   {result['hinglish_roman']}")
    print("="*60 + "\n")


def example_quality_evaluation():
    """Example with quality evaluation."""
    print("="*60)
    print("Example 3: Quality Evaluation")
    print("="*60)
    
    config = TranslationConfig(
        domain="programming",
        target_language="hi",
        translator_type="baseline"
    )
    
    pipeline = InglishtranslationPipeline(config)
    
    # Original and reference
    english = "The while loop continues until the condition becomes false."
    reference = "while loop tab tak continue karta hai jab tak condition false nahi ho jati"
    
    # Translate
    result = pipeline.translate(english)
    translated = result['hinglish_roman']
    
    # Evaluate
    metrics = pipeline.evaluate_quality(english, translated, reference)
    
    print(f"\nEnglish:    {english}")
    print(f"Reference:  {reference}")
    print(f"Predicted:  {translated}")
    print(f"\nMetrics:")
    print(f"  Terminology Preservation: {metrics['terminology_preservation']*100:.1f}%")
    print(f"  Length Ratio:             {metrics['length_ratio']:.2f}")
    if 'word_overlap' in metrics:
        print(f"  Word Overlap:             {metrics['word_overlap']*100:.1f}%")
    print("="*60 + "\n")


def example_different_domains():
    """Example with different domains."""
    print("="*60)
    print("Example 4: Different Domains")
    print("="*60)
    
    examples = [
        ("programming", "The array stores multiple integer values."),
        ("physics", "Force equals mass times acceleration."),
        ("finance", "The ROI indicates investment profitability."),
    ]
    
    for domain, text in examples:
        print(f"\nDomain: {domain.upper()}")
        print(f"English: {text}")
        
        try:
            config = TranslationConfig(
                domain=domain,
                target_language="hi",
                translator_type="baseline"
            )
            
            pipeline = InglishtranslationPipeline(config)
            result = pipeline.translate(text)
            
            print(f"Roman:   {result['hinglish_roman']}")
            print(f"Terms:   {result['metadata']['technical_terms']}")
        except FileNotFoundError:
            print(f"(Glossary not available for {domain})")
    
    print("\n" + "="*60 + "\n")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("INGLISH TRANSLATOR - USAGE EXAMPLES")
    print("="*60 + "\n")
    
    example_simple_translation()
    example_batch_translation()
    example_quality_evaluation()
    example_different_domains()
    
    print("="*60)
    print("All examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
