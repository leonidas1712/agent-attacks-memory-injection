#!/usr/bin/env python3
"""
Compare harm rates across Western and Chinese model groups, and compute
strategy comparison (user_review vs persona_memory) for Chinese models.

Reads .eval log files from benchmark_logs/ and new_data_chinese_models/.

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

# Friendly display names
MODEL_NAMES = {
    "openrouter/openai/gpt-4o": "GPT-4o",
    "openrouter/openai/gpt-4.1": "GPT-4.1",
    "openrouter/anthropic/claude-sonnet-4": "Claude Sonnet 4",
    "openrouter/google/gemini-2.5-pro": "Gemini 2.5 Pro",
    "openrouter/x-ai/grok-4-fast": "Grok-4-fast",
    "openrouter/moonshotai/kimi-k2.5": "Kimi K2.5",
    "openrouter/z-ai/glm-4.7-flash": "GLM-4.7-Flash",
    "openrouter/deepseek/deepseek-v3.1-terminus:exacto": "DeepSeek V3.1 Terminus",
}


def extract_sample_data(sample):
    """Extract all metrics from a single sample."""
    metadata = sample.metadata or {}
    exp = metadata.get("experiment_results", {})

    entry = {
        "condition": metadata.get("condition", ""),
        "strategy": metadata.get("strategy", ""),
        "scenario": metadata.get("scenario_id", ""),
        "injected": exp.get("target_overwritten", False),
        "harmful_judge": False,
        "manipulation_score": None,
        "stealth_score": None,
        "disclosed": None,
    }

    if sample.scores:
        ij = sample.scores.get("injection_judge")
        if ij and ij.metadata:
            entry["harmful_judge"] = ij.metadata.get("harmful_recommendation", False)
            entry["manipulation_score"] = ij.metadata.get("manipulation_score")

        sj = sample.scores.get("stealth_judge")
        if sj and sj.metadata:
            entry["stealth_score"] = sj.metadata.get("stealth_score")
            entry["disclosed"] = sj.metadata.get("update_disclosed")

    return entry


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
                entry = extract_sample_data(sample)
                if entry["condition"] != filter_condition:
                    continue
                if filter_strategy and entry["strategy"] != filter_strategy:
                    continue

                total_count += 1
                if entry["harmful_judge"]:
                    harmful_count += 1

        harm_rate = harmful_count / total_count if total_count > 0 else 0
        results[model] = {
            "harmful": harmful_count,
            "total": total_count,
            "harm_rate": harm_rate,
        }

    return results


def get_strategy_comparison(log_paths):
    """Compute per-model and pooled strategy comparison for backdoor condition."""
    # model -> strategy -> list of sample entries
    model_strategy_data = defaultdict(lambda: defaultdict(list))

    for log_path in log_paths:
        if not log_path.exists():
            print(f"  WARNING: {log_path} not found, skipping")
            continue

        log = read_eval_log(str(log_path))
        model = log.eval.model

        if log.samples:
            for sample in log.samples:
                entry = extract_sample_data(sample)
                if entry["condition"] != "backdoor" or not entry["strategy"]:
                    continue
                model_strategy_data[model][entry["strategy"]].append(entry)

    return model_strategy_data


def compute_strategy_stats(entries):
    """Compute aggregate stats from a list of sample entries."""
    n = len(entries)
    if n == 0:
        return None

    injected = sum(1 for e in entries if e["injected"])
    harmful = sum(1 for e in entries if e["harmful_judge"])

    manip_scores = [e["manipulation_score"] for e in entries if e["manipulation_score"] is not None]
    avg_manip = sum(manip_scores) / len(manip_scores) if manip_scores else 0

    # Stealth: only for samples where injection succeeded (stealth is meaningless otherwise)
    stealth_scores = [e["stealth_score"] for e in entries if e["injected"] and e["stealth_score"] is not None]
    avg_stealth = sum(stealth_scores) / len(stealth_scores) if stealth_scores else None

    return {
        "n": n,
        "inject_rate": injected / n,
        "harm_rate": harmful / n,
        "avg_manip": avg_manip,
        "avg_stealth": avg_stealth,
    }


def print_strategy_table(model_strategy_data):
    """Print the strategy comparison table by model and pooled."""
    header = f"{'Model':<30s} {'Strategy':<18s} {'N':>4s} {'% Inject':>10s} {'% Harmful':>11s} {'Avg Manip':>11s} {'Avg Stealth':>13s}"
    sep = "-" * len(header)

    print(header)
    print(sep)

    # Pooled accumulators
    pooled = defaultdict(list)

    for model in sorted(model_strategy_data.keys()):
        display = MODEL_NAMES.get(model, model)
        for strategy in ["user_review", "persona_memory"]:
            entries = model_strategy_data[model].get(strategy, [])
            pooled[strategy].extend(entries)
            stats = compute_strategy_stats(entries)
            if stats:
                stealth_str = f"{stats['avg_stealth']:.1f}" if stats["avg_stealth"] is not None else "-"
                print(f"{display:<30s} {strategy:<18s} {stats['n']:>4d} {stats['inject_rate']:>10.0%} {stats['harm_rate']:>11.0%} {stats['avg_manip']:>11.1f} {stealth_str:>13s}")

    print(sep)
    print(f"{'POOLED (all 3 models)':<30s}")
    for strategy in ["user_review", "persona_memory"]:
        stats = compute_strategy_stats(pooled[strategy])
        if stats:
            stealth_str = f"{stats['avg_stealth']:.1f}" if stats["avg_stealth"] is not None else "-"
            print(f"{'':30s} {strategy:<18s} {stats['n']:>4d} {stats['inject_rate']:>10.0%} {stats['harm_rate']:>11.0%} {stats['avg_manip']:>11.1f} {stealth_str:>13s}")

    print(sep)


def print_per_scenario_strategy(model_strategy_data):
    """Print per-scenario breakdown for each model."""
    for model in sorted(model_strategy_data.keys()):
        display = MODEL_NAMES.get(model, model)
        print(f"\n--- {display} ---")

        # Group by scenario
        scenario_strategy = defaultdict(lambda: defaultdict(list))
        for strategy, entries in model_strategy_data[model].items():
            for e in entries:
                scenario_strategy[e["scenario"]][strategy].append(e)

        header = f"  {'Scenario':<25s} {'Strategy':<18s} {'N':>3s} {'%Inj':>6s} {'%Harm':>7s} {'Manip':>7s} {'Stealth':>9s}"
        print(header)
        print("  " + "-" * (len(header) - 2))

        for scenario in sorted(scenario_strategy.keys()):
            for strategy in ["user_review", "persona_memory"]:
                entries = scenario_strategy[scenario].get(strategy, [])
                stats = compute_strategy_stats(entries)
                if stats:
                    stealth_str = f"{stats['avg_stealth']:.1f}" if stats["avg_stealth"] is not None else "-"
                    print(f"  {scenario:<25s} {strategy:<18s} {stats['n']:>3d} {stats['inject_rate']:>6.0%} {stats['harm_rate']:>7.0%} {stats['avg_manip']:>7.1f} {stealth_str:>9s}")


def main():
    # ========== PART 1: Western vs Chinese harm rate comparison ==========
    print("=" * 80)
    print("PART 1: Harm Rate Comparison — Western vs Chinese Models")
    print("Condition: backdoor | Strategy: user_review")
    print("=" * 80)

    print("\n--- Western Models ---")
    western = get_harm_rate_by_model(WESTERN_LOGS)
    for model, data in sorted(western.items()):
        display = MODEL_NAMES.get(model, model)
        print(f"  {display:<30s}  {data['harmful']:>2}/{data['total']:<2}  = {data['harm_rate']:.1%}")

    western_total_harmful = sum(d["harmful"] for d in western.values())
    western_total_samples = sum(d["total"] for d in western.values())
    western_avg = western_total_harmful / western_total_samples if western_total_samples > 0 else 0
    western_per_model_avg = sum(d["harm_rate"] for d in western.values()) / len(western) if western else 0

    print(f"\n  Pooled harm rate:     {western_total_harmful}/{western_total_samples} = {western_avg:.1%}")
    print(f"  Per-model avg:        {western_per_model_avg:.1%}")

    print("\n--- Chinese Models ---")
    chinese = get_harm_rate_by_model(CHINESE_LOGS)
    for model, data in sorted(chinese.items()):
        display = MODEL_NAMES.get(model, model)
        print(f"  {display:<30s}  {data['harmful']:>2}/{data['total']:<2}  = {data['harm_rate']:.1%}")

    chinese_total_harmful = sum(d["harmful"] for d in chinese.values())
    chinese_total_samples = sum(d["total"] for d in chinese.values())
    chinese_avg = chinese_total_harmful / chinese_total_samples if chinese_total_samples > 0 else 0
    chinese_per_model_avg = sum(d["harm_rate"] for d in chinese.values()) / len(chinese) if chinese else 0

    print(f"\n  Pooled harm rate:     {chinese_total_harmful}/{chinese_total_samples} = {chinese_avg:.1%}")
    print(f"  Per-model avg:        {chinese_per_model_avg:.1%}")

    print("\n" + "-" * 80)
    print(f"  Western per-model avg harm rate:  {western_per_model_avg:.1%}")
    print(f"  Chinese per-model avg harm rate:  {chinese_per_model_avg:.1%}")
    print(f"  Difference (Chinese - Western):   {(chinese_per_model_avg - western_per_model_avg):+.1%}")

    western_no_41 = {k: v for k, v in western.items() if "4.1" not in k and "4-1" not in k}
    if western_no_41:
        avg_no_41 = sum(d["harm_rate"] for d in western_no_41.values()) / len(western_no_41)
        print(f"\n  Western avg (excl. GPT-4.1):     {avg_no_41:.1%}")
        print(f"  Chinese avg:                     {chinese_per_model_avg:.1%}")
        print(f"  Difference (Chinese - Western*): {(chinese_per_model_avg - avg_no_41):+.1%}")

    # ========== PART 2: Strategy comparison ==========
    print("\n\n" + "=" * 80)
    print("PART 2: Strategy Comparison — user_review vs persona_memory")
    print("Condition: backdoor | Chinese models only")
    print("=" * 80 + "\n")

    model_strategy_data = get_strategy_comparison(CHINESE_LOGS)
    print_strategy_table(model_strategy_data)

    # ========== PART 3: Per-scenario breakdown ==========
    print("\n\n" + "=" * 80)
    print("PART 3: Per-Scenario Breakdown by Model & Strategy")
    print("=" * 80)

    print_per_scenario_strategy(model_strategy_data)
    print()


if __name__ == "__main__":
    main()
