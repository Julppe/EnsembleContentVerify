#!/usr/bin/env python3
"""
CheckEm Benchmark Evaluator — Precision, Recall & False-Positive Rate Report
=============================================================================
Loads `/root/hostinger-ai-reviewer/cache_store.json` via `app.compute_benchmark_metrics()`
and prints a transparent evaluation table covering:
  - Page-level Confusion Matrix (TP, FP, TN, FN)
  - Precision, Recall, F1, Overall False-Positive Rate (FPR)
  - Hard-Negative FPR (articles about propaganda vs active manipulation)
  - Image Forensics Recall & Precision
  - Per-Model Accuracy & Inter-Model Pairwise Agreement
"""

import os
import sys

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, APP_DIR)

import app  # noqa: E402


def main():
    metrics = app.compute_benchmark_metrics()
    pm = metrics["page_metrics"]
    sm = metrics["section_metrics"]
    vm = metrics["visual_metrics"]

    print("# CheckEm Benchmark Evaluation Report\n")
    print(f"- **Evaluated Pages**: `{pm['evaluated_pages']}` (`TP={pm['tp']}, FP={pm['fp']}, TN={pm['tn']}, FN={pm['fn']}`)")
    print(f"- **Page Precision**: `{pm['precision'] * 100:.1f}%`")
    print(f"- **Page Recall**: `{pm['recall'] * 100:.1f}%` (`F1={pm['f1_score']:.3f}`)")
    print(f"- **Overall False-Positive Rate (FPR)**: `{pm['false_positive_rate'] * 100:.1f}%`")
    print(
        f"- **Hard-Negative FPR (6 Wikipedia Propaganda Articles)**: "
        f"`{pm['hard_negative_fpr'] * 100:.1f}%` (`{pm['hard_negative_fp']}/{pm['hard_negative_total']}`)"
    )
    print(f"- **Sections Audited**: `{sm['total_sections']}` (`{sm['flagged_sections']} flagged`, `{sm['clean_sections']} clean`)")
    print(
        f"- **Visual Forensics (Synthetic Images)**: `{vm['flagged_images']}/{vm['evaluated_images']} flagged` "
        f"(`Precision={vm['precision'] * 100:.1f}%`, `Recall={vm['recall'] * 100:.1f}%`)"
    )
    print(f"- **Pairwise Inter-Model Agreement**: `{metrics['pairwise_agreement'] * 100:.1f}%`\n")

    print("## Per-Model Breakdown\n")
    print("| Model ID | Display Name | Page Accuracy | Precision | Recall | Jury Agreement |")
    print("|---|---|---:|---:|---:|---:|")
    for m in metrics["per_model"]:
        print(
            f"| `{m['model_id']}` | {m['model_name']} | "
            f"{m['page_accuracy'] * 100:.1f}% | {m['precision'] * 100:.1f}% | "
            f"{m['recall'] * 100:.1f}% | {m['agreement_with_consensus'] * 100:.1f}% |"
        )


if __name__ == "__main__":
    main()
