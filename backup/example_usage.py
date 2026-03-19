#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example usage of the Inglish Translation Pipeline.
"""
import sys
import os

# Fix console encoding on Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pipeline import InglishtranslationPipeline, TranslationConfig


def example_simple_translation():
    """Simple translation example."""
    print("="*60)
    print("Example 1: Simple Translation")
    print("="*60)
    
    config = TranslationConfig(
        domain="programming",
        target_language="hi",
        llm_model="llama-3.1-8b-instant",
        llm_api_key=os.environ.get("GROQ_API_KEY"),
    )
    
    pipeline = InglishtranslationPipeline(config)
    
    text = "The for loop iterates over the array of integers."
    result = pipeline.translate(text, verbose=True)
    
    print("\n" + "="*60)
    print("OUTPUT")
    print("="*60)
    print(f"Intermediate (bracketed): {result['intermediate_bracketed']}")
    print(f"Roman:                   {result['hinglish_roman']}")
    print(f"Devanagari:              {result['hinglish_devanagari']}")
    print(f"Terms:                   {result['metadata']['technical_terms']}")
    print("="*60 + "\n")


def example_batch_translation():
    """Batch translation example."""
    print("="*60)
    print("Example 2: Batch Translation")
    print("="*60)
    
    config = TranslationConfig(
        domain="programming",
        target_language="hi",
        llm_api_key=os.environ.get("GROQ_API_KEY"),
    )
    
    pipeline = InglishtranslationPipeline(config)
    
    texts = [
        "This class has four member variables.",
        "The function returns a boolean value.",
        "Each object has its own instance variables.",
    ]
    
    results = pipeline.translate_batch(texts, verbose=False)
    
    print("\n" + "="*60)
    print("BATCH OUTPUT")
    print("="*60)
    for i, (text, result) in enumerate(zip(texts, results), 1):
        print(f"\n[{i}] English: {text}")
        print(f"    Bracketed: {result['intermediate_bracketed']}")
        print(f"    Roman:     {result['hinglish_roman']}")
    print("="*60 + "\n")


def example_different_domains():
    """Example with different domains."""
    print("="*60)
    print("Example 2: Different Domains")
    print("="*60)
    
    examples = [
        ("programming", "The array stores multiple integer values."),
    ]
    
    for domain, text in examples:
        print(f"\nDomain: {domain.upper()}")
        print(f"English: {text}")
        
        try:
            config = TranslationConfig(
                domain=domain,
                target_language="hi",
                llm_api_key=os.environ.get("GROQ_API_KEY"),
            )
            
            pipeline = InglishtranslationPipeline(config)
            result = pipeline.translate(text)
            
            print(f"Bracketed: {result['intermediate_bracketed']}")
            print(f"Roman:     {result['hinglish_roman']}")
            print(f"Terms:     {result['metadata']['technical_terms']}")
        except FileNotFoundError:
            print(f"(Glossary not available for {domain})")
    
    print("\n" + "="*60 + "\n")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("INGLISH TRANSLATOR - USAGE EXAMPLES")
    print("="*60 + "\n")
    
    if not os.environ.get("GROQ_API_KEY"):
        print("WARNING: GROQ_API_KEY not set in environment.")
        print("Set it with: export GROQ_API_KEY=your_api_key")
        print("Examples will not work without a valid API key.\n")
    
    example_simple_translation()
    example_batch_translation()
    example_different_domains()
    
    print("="*60)
    print("All examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
