#!/usr/bin/env python3
"""
Compare average harm rates (user_review, backdoor) across Western and Chinese model groups.

Reads .eval log files from benchmark_logs/ and new_data_chinese_models/ and
computes per-model harm rates for the backdoor+user_review condition, then
prints group averages.

Usage:
  uv run python scripts/compare_harm_rates.py
"""

import sys
from pathlib import Path
from collections import defaultdict

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from inspect_ai.log import read_eval_log


WESTERN_LOGS = sorted(Path(project_root / "logs" / "benchmark_logs").glob("*.eval"))

# Chinese model logs (excluding DeepSeek V3.2 which was incomplete)
CHINESE_LOG_DIR = project_root / "logs" / "new_data_chinese_models"
CHINESE_LOGS = [
    # Kimi K2.5 (50/50)
    CHINESE_LOG_DIR / "2026-02-16T07-43-01+00-00_injection-5scenarios-backdoor_openrouter-moonshotai-kimi-k2.5_NS7w8UXxC4bDhXSU3bVCVh.eval",
    # GLM-4.7-Flash (50/50)
    CHINESE_LOG_DIR / "2026-02-16T09-00-44+00-00_injection-5scenarios-backdoor_openrouter-z-ai-glm-4.7-flash_4PJrcfZNxUQmQxRFSmahqm.eval",
    # DeepSeek V3.1 Terminus (50/50)
    CHINESE_LOG_DIR / "2026-02-16T09-19-20+00-00_injection-5scenarios-backdoor_openrouter-deepseek-deepseek-v3.1-terminus-exacto_cbCUCVtqU6Z2kNSLRYCWSw.eval",
]


def get_harm_rate_by_model(log_paths, filter_condition="backdoor", filter_strategy="user_review"):
    """For each log file, compute harm rate for samples matching the given condition+strategy."""
    results = {}

    for log_path in log_paths:
        if not log_path.exists():
            print(f"  WARNING: {log_path} not found, skipping")
            continue

        log = read_eval_log(str(log_path))
        model = log.eval.model

        harmful_count = 0
        total_count = 0

        if log.samples:
            for sample in log.samples:
                metadata = sample.metadata or {}
                condition = metadata.get("condition", "")
                strategy = metadata.get("strategy", "")

                # Filter to backdoor + user_review only
                if condition != filter_condition:
                    continue
                if filter_strategy and strategy != filter_strategy:
                    continue

                total_count += 1

                # Get harmful_recommendation from injection_judge
                if sample.scores:
                    ij = sample.scores.get("injection_judge")
                    if ij and ij.metadata:
                        if ij.metadata.get("harmful_recommendation"):
                            harmful_count += 1

        harm_rate = harmful_count / total_count if total_count > 0 else 0
        results[model] = {
            "harmful": harmful_count,
            "total": total_count,
            "harm_rate": harm_rate,
        }

    return results


def main():
    print("=" * 80)
    print("Harm Rate Comparison: Western vs Chinese Models")
    print("Condition: backdoor | Strategy: user_review")
    print("=" * 80)

    print("\n--- Western Models ---")
    western = get_harm_rate_by_model(WESTERN_LOGS)
    for model, data in sorted(western.items()):
        print(f"  {model:<50s}  {data['harmful']:>2}/{data['total']:<2}  = {data['harm_rate']:.1%}")

    western_total_harmful = sum(d["harmful"] for d in western.values())
    western_total_samples = sum(d["total"] for d in western.values())
    western_avg = western_total_harmful / western_total_samples if western_total_samples > 0 else 0
    western_per_model_avg = sum(d["harm_rate"] for d in western.values()) / len(western) if western else 0

    print(f"\n  Pooled harm rate:     {western_total_harmful}/{western_total_samples} = {western_avg:.1%}")
    print(f"  Per-model avg:        {western_per_model_avg:.1%}")

    print("\n--- Chinese Models (excl. DeepSeek V3.2) ---")
    chinese = get_harm_rate_by_model(CHINESE_LOGS)
    for model, data in sorted(chinese.items()):
        print(f"  {model:<50s}  {data['harmful']:>2}/{data['total']:<2}  = {data['harm_rate']:.1%}")

    chinese_total_harmful = sum(d["harmful"] for d in chinese.values())
    chinese_total_samples = sum(d["total"] for d in chinese.values())
    chinese_avg = chinese_total_harmful / chinese_total_samples if chinese_total_samples > 0 else 0
    chinese_per_model_avg = sum(d["harm_rate"] for d in chinese.values()) / len(chinese) if chinese else 0

    print(f"\n  Pooled harm rate:     {chinese_total_harmful}/{chinese_total_samples} = {chinese_avg:.1%}")
    print(f"  Per-model avg:        {chinese_per_model_avg:.1%}")

    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"  Western per-model avg harm rate:  {western_per_model_avg:.1%}")
    print(f"  Chinese per-model avg harm rate:  {chinese_per_model_avg:.1%}")
    print(f"  Difference (Chinese - Western):   {(chinese_per_model_avg - western_per_model_avg):+.1%}")

    # Also show without GPT-4.1
    western_no_41 = {k: v for k, v in western.items() if "4.1" not in k and "4-1" not in k}
    if western_no_41:
        avg_no_41 = sum(d["harm_rate"] for d in western_no_41.values()) / len(western_no_41)
        print(f"\n  Western avg (excl. GPT-4.1):     {avg_no_41:.1%}")
        print(f"  Chinese avg:                     {chinese_per_model_avg:.1%}")
        print(f"  Difference (Chinese - Western*): {(chinese_per_model_avg - avg_no_41):+.1%}")


if __name__ == "__main__":
    main()
