#!/usr/bin/env python3
"""
Baseline benchmark — rule-based (no LLM) translation evaluation.

This is the simplest possible approach: term extraction + guarding only.
Used as a lower-bound reference when comparing against LLM-based methods.

Usage (run from src/):
    python docgen/baseline_benchmark.py \\
        --dataset data/datasets/eval/programming_eval.json \\
        --domain  programming \\
        --output  results/baseline_results.json
"""

import sys
import json
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from docgen.pipeline import InglishtranslationPipeline, TranslationConfig
from shared.utils import load_json_dataset


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def calculate_metrics(predictions: list, references: list) -> dict:
    """
    Compute terminology consistency, constraint preservation, and length ratio.

    Args:
        predictions: List of pipeline result dicts.
        references:  List of reference sample dicts from the dataset.
    """
    assert len(predictions) == len(references), (
        f"Count mismatch: {len(predictions)} predictions vs {len(references)} references"
    )

    term_consistency   = []
    constraint_ok      = []
    length_ratios      = []

    for pred, ref in zip(predictions, references):
        pred_text  = pred.get("hinglish_roman", "")
        ref_terms  = ref.get("technical_terms", [])
        english    = ref.get("english", "")

        if ref_terms:
            preserved = sum(1 for t in ref_terms if t.lower() in pred_text.lower())
            term_consistency.append(preserved / len(ref_terms))
            constraint_ok.append(1.0 if preserved == len(ref_terms) else 0.0)
        else:
            term_consistency.append(1.0)
            constraint_ok.append(1.0)

        if english:
            length_ratios.append(len(pred_text.split()) / max(len(english.split()), 1))

    def avg(lst): return sum(lst) / len(lst) if lst else 0.0

    return {
        "terminology_consistency": avg(term_consistency),
        "constraint_preservation": avg(constraint_ok),
        "avg_length_ratio":        avg(length_ratios),
        "total_samples":           len(predictions),
    }


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

def run_baseline_benchmark(
    dataset_path: str,
    domain: str = "programming",
    output_path: str = None,
    verbose: bool = False,
) -> None:
    sep = "=" * 60
    print(f"\n{sep}\nBASELINE BENCHMARK — Rule-Based Translation\n{sep}\n")

    print(f"Loading dataset: {dataset_path}")
    dataset = load_json_dataset(dataset_path)
    print(f"Loaded {len(dataset)} samples\n")

    config = TranslationConfig(
        domain=domain,
        target_language="hi",
        llm_provider="none",
    )
    pipeline = InglishtranslationPipeline(config)
    print(f"Pipeline initialised (domain={domain}, baseline mode)\n")

    predictions = []
    total_time  = 0.0

    for i, sample in enumerate(dataset):
        t0 = time.time()
        result = pipeline.translate(sample["english"], verbose=(verbose and i < 3))
        total_time += time.time() - t0

        # Baseline: use the guarded (bracketed) text as the Roman output
        result["hinglish_roman"] = result["intermediate_bracketed"]

        predictions.append(result)

        if (i + 1) % 10 == 0:
            print(f"  Processed {i+1}/{len(dataset)}...")

    throughput = len(predictions) / total_time if total_time else 0
    print(f"\nDone: {len(predictions)} samples in {total_time:.2f}s "
          f"({throughput:.1f} sent/sec)\n")

    metrics = calculate_metrics(predictions, dataset)

    print(f"{sep}\nRESULTS\n{sep}")
    print(f"Terminology Consistency: {metrics['terminology_consistency']*100:.1f}%")
    print(f"Constraint Preservation: {metrics['constraint_preservation']*100:.1f}%")
    print(f"Average Length Ratio:    {metrics['avg_length_ratio']:.2f}")
    print(f"Total Samples:           {metrics['total_samples']}")
    print(sep)

    print("\nSample Outputs:")
    print("-" * 60)
    for i in range(min(3, len(predictions))):
        print(f"\n[{i+1}] English:    {dataset[i]['english']}")
        print(f"     Reference:  {dataset[i].get('hinglish_roman', 'N/A')}")
        print(f"     Predicted:  {predictions[i]['hinglish_roman']}")
        print(f"     Devanagari: {predictions[i]['hinglish_devanagari']}")
    print("-" * 60)

    if output_path:
        results = {
            "config": {"domain": domain, "translator_type": "baseline", "dataset": dataset_path},
            "metrics": metrics,
            "performance": {
                "total_time":          total_time,
                "avg_time_per_sample": total_time / len(predictions),
                "throughput":          throughput,
            },
            "predictions": predictions,
        }
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nResults saved to: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Run Inglish baseline benchmark")
    parser.add_argument("--dataset", required=True,
                        help="Path to evaluation dataset JSON")
    parser.add_argument("--domain",  default="programming",
                        help="Domain name (default: programming)")
    parser.add_argument("--output",  default="results/baseline_results.json",
                        help="Output path for results JSON")
    parser.add_argument("--verbose", action="store_true",
                        help="Print detailed output for first few samples")
    args = parser.parse_args()

    run_baseline_benchmark(
        dataset_path=args.dataset,
        domain=args.domain,
        output_path=args.output,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
