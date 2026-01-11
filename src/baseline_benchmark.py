#!/usr/bin/env python3
"""
Baseline benchmark using simple rule-based translation.

This is the simplest, crudest algorithm for Inglish translation.
It serves as a baseline to compare more sophisticated approaches against.
"""

import sys
import json
import time
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pipeline import InglishtranslationPipeline, TranslationConfig
from utils import load_json_dataset


def calculate_metrics(predictions: list, references: list) -> dict:
    """
    Calculate evaluation metrics.
    
    Args:
        predictions: List of prediction dicts
        references: List of reference dicts
        
    Returns:
        Dictionary of metrics
    """
    assert len(predictions) == len(references), "Prediction and reference count mismatch"
    
    metrics = {
        "terminology_consistency": [],
        "constraint_preservation": [],
        "length_ratio": [],
    }
    
    for pred, ref in zip(predictions, references):
        pred_text = pred.get("hinglish_roman", "")
        ref_text = ref.get("hinglish_roman", "")
        english = ref.get("english", "")
        ref_terms = ref.get("technical_terms", [])
        
        # Terminology consistency
        if ref_terms:
            preserved = sum(1 for term in ref_terms if term.lower() in pred_text.lower())
            metrics["terminology_consistency"].append(preserved / len(ref_terms))
        else:
            metrics["terminology_consistency"].append(1.0)
        
        # Constraint preservation (all technical terms present)
        if ref_terms:
            all_preserved = all(term.lower() in pred_text.lower() for term in ref_terms)
            metrics["constraint_preservation"].append(1.0 if all_preserved else 0.0)
        else:
            metrics["constraint_preservation"].append(1.0)
        
        # Length ratio
        if english:
            pred_len = len(pred_text.split())
            eng_len = len(english.split())
            metrics["length_ratio"].append(pred_len / max(eng_len, 1))
    
    # Calculate averages
    return {
        "terminology_consistency": sum(metrics["terminology_consistency"]) / len(metrics["terminology_consistency"]),
        "constraint_preservation": sum(metrics["constraint_preservation"]) / len(metrics["constraint_preservation"]),
        "avg_length_ratio": sum(metrics["length_ratio"]) / len(metrics["length_ratio"]),
        "total_samples": len(predictions),
    }


def run_baseline_benchmark(dataset_path: str, domain: str = "programming", 
                          output_path: str = None, verbose: bool = False):
    """
    Run baseline benchmark on a dataset.
    
    Args:
        dataset_path: Path to evaluation dataset
        domain: Domain name
        output_path: Path to save results
        verbose: Print detailed output
    """
    print(f"\n{'='*60}")
    print(f"BASELINE BENCHMARK - Rule-Based Translation")
    print(f"{'='*60}\n")
    
    # Load dataset
    print(f"Loading dataset from: {dataset_path}")
    dataset = load_json_dataset(dataset_path)
    print(f"Loaded {len(dataset)} samples\n")
    
    # Initialize pipeline
    config = TranslationConfig(
        domain=domain,
        target_language="hi",
        translator_type="baseline",
        output_format="both"
    )
    
    pipeline = InglishtranslationPipeline(config)
    print(f"Initialized pipeline with domain: {domain}\n")
    
    # Run translations
    print("Running translations...")
    predictions = []
    total_time = 0
    
    for i, sample in enumerate(dataset):
        if verbose and i < 3:
            print(f"\n--- Sample {i+1} ---")
        
        start_time = time.time()
        result = pipeline.translate(sample["english"], verbose=(verbose and i < 3))
        elapsed = time.time() - start_time
        total_time += elapsed
        
        predictions.append(result)
        
        if (i + 1) % 10 == 0:
            print(f"Processed {i+1}/{len(dataset)} samples...")
    
    print(f"\nCompleted {len(predictions)} translations in {total_time:.2f}s")
    print(f"Average time per sample: {total_time/len(predictions):.4f}s")
    print(f"Throughput: {len(predictions)/total_time:.1f} sentences/sec\n")
    
    # Calculate metrics
    print("Calculating metrics...")
    metrics = calculate_metrics(predictions, dataset)
    
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"Terminology Consistency: {metrics['terminology_consistency']*100:.1f}%")
    print(f"Constraint Preservation: {metrics['constraint_preservation']*100:.1f}%")
    print(f"Average Length Ratio:    {metrics['avg_length_ratio']:.2f}")
    print(f"Total Samples:           {metrics['total_samples']}")
    print(f"{'='*60}\n")
    
    # Show sample outputs
    print("Sample Outputs:")
    print("-" * 60)
    for i in range(min(3, len(predictions))):
        print(f"\n[{i+1}] English:")
        print(f"    {dataset[i]['english']}")
        print(f"    Reference (Roman): {dataset[i].get('hinglish_roman', 'N/A')}")
        print(f"    Predicted (Roman): {predictions[i]['hinglish_roman']}")
        print(f"    Predicted (Devanagari): {predictions[i]['hinglish_devanagari']}")
    print("-" * 60)
    
    # Save results
    if output_path:
        results = {
            "config": {
                "domain": domain,
                "translator_type": "baseline",
                "dataset": dataset_path,
            },
            "metrics": metrics,
            "performance": {
                "total_time": total_time,
                "avg_time_per_sample": total_time / len(predictions),
                "throughput": len(predictions) / total_time,
            },
            "predictions": predictions,
        }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\nResults saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Run baseline benchmark for Inglish translation"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Path to evaluation dataset (JSON)"
    )
    parser.add_argument(
        "--domain",
        type=str,
        default="programming",
        help="Domain name (default: programming)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/baseline_results.json",
        help="Output path for results"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output for first few samples"
    )
    
    args = parser.parse_args()
    
    run_baseline_benchmark(
        dataset_path=args.dataset,
        domain=args.domain,
        output_path=args.output,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()