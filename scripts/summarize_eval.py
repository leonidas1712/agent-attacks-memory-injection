#!/usr/bin/env python3
"""
Summarize results from one or more InspectAI .eval log files.

Prints the same detailed results table and aggregated stats table
that run_injection_scenarios.py prints after a run, without re-running.

Usage:
  uv run python scripts/summarize_eval.py logs/new_data_chinese_models/*.eval
  uv run python scripts/summarize_eval.py path/to/specific.eval
  uv run python scripts/summarize_eval.py log1.eval log2.eval log3.eval
"""

import sys
import argparse
from pathlib import Path
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from inspect_ai.log import read_eval_log


def print_results_table(logs):
    """Print a detailed per-sample results table."""
    print("\nResults Summary:")
    print("=" * 130)
    print(
        f"{'Scenario':<22} {'Condition':<15} {'Strategy':<18} "
        f"{'Injected':<10} {'Harm':<7} {'Manip':<7} {'Stealth':<9} "
        f"{'Disclosed':<10} {'Judge':<7}"
    )
    print("=" * 130)

    for log in logs:
        if log.samples:
            for sample in log.samples:
                metadata = sample.metadata or {}
                results = metadata.get("experiment_results", {})

                scenario = results.get(
                    "scenario_id", metadata.get("scenario_id", "?")
                )[:20]
                condition = results.get(
                    "condition", metadata.get("condition", "?")
                )[:13]
                strategy = results.get("strategy") or "-"
                strategy = strategy[:16] if strategy else "-"

                # Injection success
                injected = "✓" if results.get("target_overwritten") else "✗"

                # Heuristic harm from experiment results
                harm = "✓" if results.get("harm_detected") else "✗"

                # Judge scores — only set from the scorer that provides each field
                manip = "-"
                stealth = "-"
                disclosed = "-"
                judge_harm = "-"
                if sample.scores:
                    for score_name, score in sample.scores.items():
                        if score.metadata:
                            if "harmful_recommendation" in score.metadata:
                                judge_harm = (
                                    "✓"
                                    if score.metadata["harmful_recommendation"]
                                    else "✗"
                                )
                            if "manipulation_score" in score.metadata:
                                manip = str(
                                    score.metadata["manipulation_score"]
                                )
                            if "stealth_score" in score.metadata:
                                stealth = str(
                                    score.metadata["stealth_score"]
                                )
                            if "update_disclosed" in score.metadata:
                                ud = score.metadata["update_disclosed"]
                                disclosed = "yes" if ud else "no"

                print(
                    f"{scenario:<22} {condition:<15} {strategy:<18} "
                    f"{injected:<10} {harm:<7} {manip:<7} {stealth:<9} "
                    f"{disclosed:<10} {judge_harm:<7}"
                )

    print("=" * 130)
    print("\nLegend:")
    print("  Injected:   Memory was successfully overwritten by injection")
    print("  Harm:       Heuristic - response contains harm indicators")
    print("  Manip:      Judge - manipulation score (1-5)")
    print("  Stealth:    Judge - stealth score (1=disclosed, 5=fully stealthy)")
    print("  Disclosed:  Judge - did assistant reveal the memory update?")
    print("  Judge:      LLM judge - harmful recommendation detected")
    print()


def aggregate_results(logs):
    """Aggregate results by (scenario, condition) and print stats table."""
    groups = defaultdict(list)

    for log in logs:
        if log.samples:
            for sample in log.samples:
                metadata = sample.metadata or {}
                results = metadata.get("experiment_results", {})

                scenario = results.get(
                    "scenario_id", metadata.get("scenario_id", "unknown")
                )
                condition = results.get(
                    "condition", metadata.get("condition", "unknown")
                )
                strategy = results.get("strategy")

                # Build key — for backdoor, include strategy
                if condition == "backdoor" and strategy:
                    key = (scenario, f"{condition}_{strategy}")
                else:
                    key = (scenario, condition)

                # Collect metrics
                entry = {
                    "harm_heuristic": results.get("harm_detected", False),
                    "injected": results.get("target_overwritten", False),
                }

                # Add judge scores — only from the scorer that provides each field
                if sample.scores:
                    for score_name, score in sample.scores.items():
                        if score.metadata:
                            if "harmful_recommendation" in score.metadata:
                                entry["harmful_judge"] = score.metadata[
                                    "harmful_recommendation"
                                ]
                            if "manipulation_score" in score.metadata:
                                entry["manipulation_score"] = score.metadata[
                                    "manipulation_score"
                                ]
                            if "stealth_score" in score.metadata:
                                entry["stealth_score"] = score.metadata[
                                    "stealth_score"
                                ]
                            if "update_disclosed" in score.metadata:
                                entry["disclosed"] = score.metadata[
                                    "update_disclosed"
                                ]

                groups[key].append(entry)

    # Print aggregated table
    print("\nAggregated Results:")
    print("=" * 120)
    print(
        f"{'Scenario':<20} {'Condition':<22} {'N':<4} "
        f"{'% Inject':<10} {'% Harmful':<11} {'Avg Manip':<11} "
        f"{'Avg Stealth':<13} {'% Disclosed':<12}"
    )
    print("=" * 120)

    for (scenario, condition), entries in sorted(groups.items()):
        n = len(entries)

        inject_count = sum(
            1 for e in entries if e.get("injected", False)
        )
        pct_inject = (inject_count / n * 100) if n > 0 else 0

        harmful_count = sum(
            1 for e in entries if e.get("harmful_judge", False)
        )
        pct_harmful = (harmful_count / n * 100) if n > 0 else 0

        manip_scores = [
            e["manipulation_score"]
            for e in entries
            if "manipulation_score" in e
            and e["manipulation_score"] is not None
        ]
        avg_manip = (
            sum(manip_scores) / len(manip_scores) if manip_scores else 0
        )

        stealth_scores = [
            e["stealth_score"]
            for e in entries
            if "stealth_score" in e and e["stealth_score"] is not None
        ]
        avg_stealth = (
            sum(stealth_scores) / len(stealth_scores)
            if stealth_scores
            else 0
        )

        disclosed_count = sum(
            1 for e in entries if e.get("disclosed", False)
        )
        disclosed_total = sum(1 for e in entries if "disclosed" in e)
        pct_disclosed = (
            (disclosed_count / disclosed_total * 100)
            if disclosed_total > 0
            else 0
        )

        stealth_str = (
            f"{avg_stealth:>6.1f}" if stealth_scores else "    -"
        )
        disclosed_str = (
            f"{pct_disclosed:>6.0f}%"
            if disclosed_total > 0
            else "     -"
        )

        print(
            f"{scenario:<20} {condition:<22} {n:<4} "
            f"{pct_inject:>5.0f}%    {pct_harmful:>5.0f}%     "
            f"{avg_manip:>6.1f}     {stealth_str}       {disclosed_str}"
        )

    print("=" * 120)
    print()


def aggregate_by_strategy(logs):
    """Aggregate results by strategy across all scenarios."""
    strategies = defaultdict(list)

    for log in logs:
        if log.samples:
            for sample in log.samples:
                metadata = sample.metadata or {}
                results = metadata.get("experiment_results", {})
                strategy = results.get("strategy") or metadata.get("strategy")
                if not strategy:
                    continue

                entry = {
                    "injected": results.get("target_overwritten", False),
                }

                if sample.scores:
                    for score_name, score in sample.scores.items():
                        if score.metadata:
                            if "harmful_recommendation" in score.metadata:
                                entry["harmful_judge"] = score.metadata[
                                    "harmful_recommendation"
                                ]
                            if "manipulation_score" in score.metadata:
                                entry["manipulation_score"] = score.metadata[
                                    "manipulation_score"
                                ]
                            if "stealth_score" in score.metadata:
                                entry["stealth_score"] = score.metadata[
                                    "stealth_score"
                                ]

                strategies[strategy].append(entry)

    if not strategies:
        return

    print("\nStrategy Summary:")
    print("=" * 80)
    print(
        f"{'Strategy':<20} {'N':<5} {'% Inject':<10} "
        f"{'% Harmful':<11} {'Avg Manip':<11} {'Avg Stealth':<12}"
    )
    print("=" * 80)

    for strategy, entries in sorted(strategies.items()):
        n = len(entries)

        inject_count = sum(1 for e in entries if e.get("injected", False))
        pct_inject = (inject_count / n * 100) if n > 0 else 0

        harmful_count = sum(
            1 for e in entries if e.get("harmful_judge", False)
        )
        pct_harmful = (harmful_count / n * 100) if n > 0 else 0

        manip_scores = [
            e["manipulation_score"]
            for e in entries
            if "manipulation_score" in e
            and e["manipulation_score"] is not None
        ]
        avg_manip = (
            sum(manip_scores) / len(manip_scores) if manip_scores else 0
        )

        stealth_scores = [
            e["stealth_score"]
            for e in entries
            if "stealth_score" in e and e["stealth_score"] is not None
        ]
        avg_stealth = (
            sum(stealth_scores) / len(stealth_scores)
            if stealth_scores
            else 0
        )

        stealth_str = (
            f"{avg_stealth:>6.1f}" if stealth_scores else "     -"
        )

        print(
            f"{strategy:<20} {n:<5} {pct_inject:>5.0f}%    "
            f"{pct_harmful:>5.0f}%     {avg_manip:>6.1f}     {stealth_str}"
        )

    print("=" * 80)
    print()


def print_header(logs):
    """Print summary header with model, task, and token info."""
    for log in logs:
        model = log.eval.model or "unknown"
        task = log.eval.task or "unknown"
        status = log.status
        n_samples = len(log.samples) if log.samples else 0
        epochs = log.eval.config.epochs if log.eval.config else None

        print(f"\n{'='*70}")
        print(f"Eval Log Summary")
        print(f"{'='*70}")
        print(f"  File: {log.location}")
        print(f"  Model: {model}")
        print(f"  Task: {task}")
        print(f"  Status: {status}")
        print(f"  Samples: {n_samples}")
        if epochs:
            print(f"  Epochs: {epochs}")

        # Results summary
        if log.results and log.results.scores:
            print(f"  Scores:")
            for score in log.results.scores:
                print(f"    {score.name}:")
                if score.metrics:
                    for name, metric in score.metrics.items():
                        print(f"      {name}: {metric.value:.3f}")

        # Stats
        if log.stats:
            if log.stats.completed_at and log.stats.started_at:
                try:
                    from datetime import datetime
                    start = datetime.fromisoformat(str(log.stats.started_at))
                    end = datetime.fromisoformat(str(log.stats.completed_at))
                    duration = end - start
                    print(f"  Duration: {duration}")
                except Exception:
                    pass

        print(f"{'='*70}")


def main():
    parser = argparse.ArgumentParser(
        description="Summarize results from InspectAI .eval log files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Summarize a single eval log
  uv run python scripts/summarize_eval.py logs/new_data_chinese_models/2026-02-16T07-43-01*.eval

  # Summarize all logs in a directory
  uv run python scripts/summarize_eval.py logs/new_data_chinese_models/*.eval

  # Show only aggregated table (skip per-sample details)
  uv run python scripts/summarize_eval.py --agg-only path/to/log.eval

  # Show only the header/scores summary
  uv run python scripts/summarize_eval.py --header-only path/to/log.eval
        """,
    )

    parser.add_argument(
        "eval_files",
        nargs="+",
        help="One or more .eval log files to summarize",
    )
    parser.add_argument(
        "--agg-only",
        action="store_true",
        help="Show only aggregated table (skip per-sample details)",
    )
    parser.add_argument(
        "--header-only",
        action="store_true",
        help="Show only header/scores summary (no tables)",
    )

    args = parser.parse_args()

    # Load all eval files
    logs = []
    for filepath in args.eval_files:
        p = Path(filepath)
        if not p.exists():
            print(f"Warning: File not found: {filepath}", file=sys.stderr)
            continue
        try:
            log = read_eval_log(str(p))
            logs.append(log)
        except Exception as e:
            print(f"Warning: Could not read {filepath}: {e}", file=sys.stderr)
            continue

    if not logs:
        print("Error: No valid eval logs loaded.", file=sys.stderr)
        sys.exit(1)

    # Header
    print_header(logs)

    if args.header_only:
        return

    # Detailed table
    if not args.agg_only:
        print_results_table(logs)

    # Aggregated table (always show if not header-only)
    aggregate_results(logs)

    # Strategy summary
    aggregate_by_strategy(logs)


if __name__ == "__main__":
    main()
