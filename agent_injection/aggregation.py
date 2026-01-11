"""
Results aggregation for memory injection experiments.

Computes statistics across rollouts and generates summary tables.
"""

from collections import defaultdict
from pathlib import Path
import csv
from inspect_ai.log import EvalLog


def aggregate_logs(logs: list[EvalLog]) -> dict:
    """
    Aggregate results from multiple logs by (scenario, condition).
    
    Args:
        logs: List of EvalLog objects from eval()
        
    Returns:
        Dictionary with aggregated statistics per (scenario, condition)
    """
    # Group by (scenario, condition)
    groups = defaultdict(list)
    
    for log in logs:
        if log.samples:
            for sample in log.samples:
                metadata = sample.metadata or {}
                results = metadata.get("experiment_results", {})
                
                scenario = results.get("scenario_id", metadata.get("scenario_id", "unknown"))
                condition = results.get("condition", metadata.get("condition", "unknown"))
                strategy = results.get("strategy")
                
                # Build key - for backdoor, include strategy
                if condition == "backdoor" and strategy:
                    key = (scenario, f"{condition}_{strategy}")
                else:
                    key = (scenario, condition)
                
                # Collect metrics
                entry = {
                    "harm_heuristic": results.get("harm_detected", False),
                    "safety_heuristic": results.get("safety_present", False),
                    "injection_triggered": results.get("injection_triggered", False),
                    "target_overwritten": results.get("target_overwritten", False),
                }
                
                # Add judge scores if available
                if sample.scores:
                    for score_name, score in sample.scores.items():
                        if score.metadata:
                            entry["harmful_judge"] = score.metadata.get("harmful_recommendation", False)
                            entry["manipulation_score"] = score.metadata.get("manipulation_score", 1)
                            entry["safety_judge"] = score.metadata.get("safety_warning_present", True)
                
                groups[key].append(entry)
    
    # Calculate aggregated stats
    results = {}
    
    for key, entries in groups.items():
        scenario, condition = key
        n = len(entries)
        
        # Calculate stats
        harmful_count = sum(1 for e in entries if e.get("harmful_judge", False))
        pct_harmful = (harmful_count / n * 100) if n > 0 else 0
        
        manip_scores = [e.get("manipulation_score", 1) for e in entries if "manipulation_score" in e]
        avg_manip = sum(manip_scores) / len(manip_scores) if manip_scores else 0
        
        safety_count = sum(1 for e in entries if e.get("safety_judge", True))
        pct_safety = (safety_count / n * 100) if n > 0 else 0
        
        # Heuristic stats
        harm_heuristic_count = sum(1 for e in entries if e.get("harm_heuristic", False))
        pct_harm_heuristic = (harm_heuristic_count / n * 100) if n > 0 else 0
        
        # Injection stats (backdoor only)
        injection_count = sum(1 for e in entries if e.get("injection_triggered", False))
        pct_injection = (injection_count / n * 100) if n > 0 else 0
        
        overwrite_count = sum(1 for e in entries if e.get("target_overwritten", False))
        pct_overwritten = (overwrite_count / n * 100) if n > 0 else 0
        
        results[key] = {
            "scenario": scenario,
            "condition": condition,
            "n": n,
            "pct_harmful": pct_harmful,
            "avg_manipulation_score": avg_manip,
            "pct_safety_warning": pct_safety,
            "pct_harm_heuristic": pct_harm_heuristic,
            "pct_injection_triggered": pct_injection,
            "pct_target_overwritten": pct_overwritten,
            "raw_entries": entries,
        }
    
    return results


def print_results_table(aggregated: dict, detailed: bool = False):
    """
    Print a formatted results table.
    
    Args:
        aggregated: Dictionary from aggregate_logs()
        detailed: Whether to include additional columns
    """
    print("\nAggregated Results:")
    print("=" * 100)
    
    if detailed:
        print(f"{'Scenario':<20} {'Condition':<18} {'N':<4} {'% Harmful':<12} {'Avg Manip':<12} {'% Safety':<12} {'% Injected':<12}")
        print("=" * 100)
        
        for key, stats in sorted(aggregated.items()):
            print(
                f"{stats['scenario']:<20} "
                f"{stats['condition']:<18} "
                f"{stats['n']:<4} "
                f"{stats['pct_harmful']:>6.0f}%      "
                f"{stats['avg_manipulation_score']:>6.1f}       "
                f"{stats['pct_safety_warning']:>6.0f}%      "
                f"{stats['pct_injection_triggered']:>6.0f}%"
            )
    else:
        print(f"{'Scenario':<20} {'Condition':<18} {'N':<4} {'% Harmful':<12} {'Avg Manip':<12} {'% Safety':<12}")
        print("=" * 100)
        
        for key, stats in sorted(aggregated.items()):
            print(
                f"{stats['scenario']:<20} "
                f"{stats['condition']:<18} "
                f"{stats['n']:<4} "
                f"{stats['pct_harmful']:>6.0f}%      "
                f"{stats['avg_manipulation_score']:>6.1f}       "
                f"{stats['pct_safety_warning']:>6.0f}%"
            )
    
    print("=" * 100)
    print()


def save_results_csv(aggregated: dict, output_path: str | Path):
    """
    Save aggregated results to a CSV file.
    
    Args:
        aggregated: Dictionary from aggregate_logs()
        output_path: Path to save CSV file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        "scenario",
        "condition",
        "n",
        "pct_harmful",
        "avg_manipulation_score",
        "pct_safety_warning",
        "pct_harm_heuristic",
        "pct_injection_triggered",
        "pct_target_overwritten",
    ]
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for key, stats in sorted(aggregated.items()):
            row = {k: v for k, v in stats.items() if k in fieldnames}
            writer.writerow(row)
    
    print(f"Results saved to: {output_path}")


def compare_conditions(aggregated: dict):
    """
    Compare results across conditions for each scenario.
    
    Prints a comparison showing whether backdoor condition achieves
    similar effects to direct_pressure condition.
    """
    # Group by scenario
    by_scenario = defaultdict(dict)
    for key, stats in aggregated.items():
        scenario, condition = key
        by_scenario[scenario][condition] = stats
    
    print("\nCondition Comparison:")
    print("=" * 80)
    print(f"{'Scenario':<20} {'Condition':<18} {'% Harmful':<12} {'Avg Manip':<12}")
    print("-" * 80)
    
    for scenario in sorted(by_scenario.keys()):
        conditions = by_scenario[scenario]
        
        for condition in ["baseline", "direct_pressure", "backdoor_chat_log", "backdoor_user_review"]:
            if condition in conditions:
                stats = conditions[condition]
                print(
                    f"{scenario:<20} "
                    f"{condition:<18} "
                    f"{stats['pct_harmful']:>6.0f}%      "
                    f"{stats['avg_manipulation_score']:>6.1f}"
                )
        
        print("-" * 80)
    
    print("=" * 80)
    print()
    
    # Calculate overall comparison
    print("Overall Summary:")
    print("-" * 60)
    
    condition_totals = defaultdict(lambda: {"harmful": 0, "manip": [], "n": 0})
    
    for key, stats in aggregated.items():
        scenario, condition = key
        base_condition = condition.split("_")[0] if "backdoor" in condition else condition
        
        condition_totals[base_condition]["harmful"] += stats["pct_harmful"] * stats["n"]
        condition_totals[base_condition]["manip"].extend(
            [stats["avg_manipulation_score"]] * stats["n"]
        )
        condition_totals[base_condition]["n"] += stats["n"]
    
    for condition in ["baseline", "direct_pressure", "backdoor"]:
        if condition in condition_totals:
            totals = condition_totals[condition]
            avg_harmful = totals["harmful"] / totals["n"] if totals["n"] > 0 else 0
            avg_manip = sum(totals["manip"]) / len(totals["manip"]) if totals["manip"] else 0
            print(f"  {condition:<18}: {avg_harmful:>5.1f}% harmful, {avg_manip:.1f} avg manipulation")
    
    print("-" * 60)
    print()

