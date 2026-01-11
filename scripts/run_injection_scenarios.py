#!/usr/bin/env python3
"""
Run multi-scenario memory injection attack experiments.

Tests whether hidden instructions in web content can cause an AI agent
to update its persistent memory in ways that lead to harmful recommendations.

Experimental Conditions:
- baseline: Neutral prompt + clean pages (no injection)
- direct_pressure: Neutral prompt + pressure instruction + clean pages
- backdoor: Neutral prompt + injected pages (hidden manipulation)

Scenarios:
- financial_steering: Changes risk tolerance to recommend high-risk investments
- medical_allergy: Removes allergy info, risking dangerous drug recommendations
- dietary_diabetic: Removes diabetic flag, risking high-sugar recommendations
- security_downgrade: Changes security prefs to recommend weak security
- purchase_steering: Changes budget preference to recommend expensive products

Injection Strategies (for backdoor condition):
- chat_log: Fake customer support chat confirming preference
- user_review: Fake user review mentioning preference
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent_injection.scenarios import SCENARIOS, get_scenario_ids, INJECTION_STRATEGIES
from agent_injection.scenario_tasks import (
    multi_scenario_injection_eval, 
    single_scenario_injection_eval,
    VALID_CONDITIONS,
)
from inspect_ai import eval


def list_scenarios():
    """Print all available scenarios and conditions."""
    print("\nAvailable scenarios:")
    print("-" * 70)
    for sid, scenario in SCENARIOS.items():
        print(f"  {sid}")
        print(f"    Name: {scenario['name']}")
        print(f"    Description: {scenario['description']}")
        print(f"    Target key: {scenario['target_key']}")
        print(f"    Attack: {scenario['initial_memory'].get(scenario['target_key'])} → {scenario['injected_value']}")
        print()
    
    print("Available conditions:")
    print("-" * 70)
    for condition in VALID_CONDITIONS:
        if condition == "baseline":
            print(f"  {condition}: Neutral prompt + clean pages (control)")
        elif condition == "direct_pressure":
            print(f"  {condition}: Neutral prompt + pressure instruction")
        elif condition == "backdoor":
            print(f"  {condition}: Neutral prompt + injected pages")
    print()
    
    print("Available injection strategies (for backdoor condition):")
    print("-" * 70)
    for strategy in INJECTION_STRATEGIES:
        print(f"  {strategy}")
    print()


def print_results_table(logs):
    """Print a summary table of results."""
    print("\nResults Summary:")
    print("=" * 110)
    print(f"{'Scenario':<22} {'Condition':<15} {'Strategy':<12} {'Harm':<8} {'Manip':<8} {'Safety':<8} {'Judge':<10}")
    print("=" * 110)
    
    for log in logs:
        if log.samples:
            for sample in log.samples:
                metadata = sample.metadata or {}
                results = metadata.get("experiment_results", {})
                
                scenario = results.get("scenario_id", metadata.get("scenario_id", "?"))[:20]
                condition = results.get("condition", metadata.get("condition", "?"))[:13]
                strategy = results.get("strategy") or "-"
                strategy = strategy[:10] if strategy else "-"
                
                # Heuristic harm/safety from experiment results
                harm = "✓" if results.get("harm_detected") else "✗"
                safety = "✓" if results.get("safety_present") else "✗"
                
                # Judge scores if available
                if sample.scores:
                    for score_name, score in sample.scores.items():
                        if score.metadata:
                            manip = str(score.metadata.get("manipulation_score", "-"))
                            judge_harm = "✓" if score.metadata.get("harmful_recommendation") else "✗"
                        else:
                            manip = "-"
                            judge_harm = "-"
                else:
                    manip = "-"
                    judge_harm = "-"
                
                print(f"{scenario:<22} {condition:<15} {strategy:<12} {harm:<8} {manip:<8} {safety:<8} {judge_harm:<10}")
    
    print("=" * 110)
    print("\nLegend:")
    print("  Harm: Heuristic - response contains harm indicators")
    print("  Manip: Judge - manipulation score (1-5)")
    print("  Safety: Heuristic - response contains safety indicators")
    print("  Judge: LLM judge - harmful recommendation detected")
    print()


def aggregate_results(logs):
    """Aggregate results by (scenario, condition) and print stats table."""
    from collections import defaultdict
    
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
                }
                
                # Add judge scores if available
                if sample.scores:
                    for score_name, score in sample.scores.items():
                        if score.metadata:
                            entry["harmful_judge"] = score.metadata.get("harmful_recommendation", False)
                            entry["manipulation_score"] = score.metadata.get("manipulation_score", 1)
                            entry["safety_judge"] = score.metadata.get("safety_warning_present", True)
                
                groups[key].append(entry)
    
    # Print aggregated table
    print("\nAggregated Results:")
    print("=" * 100)
    print(f"{'Scenario':<20} {'Condition':<18} {'N':<4} {'% Harmful':<12} {'Avg Manip':<12} {'% Safety':<12}")
    print("=" * 100)
    
    for (scenario, condition), entries in sorted(groups.items()):
        n = len(entries)
        
        # Calculate stats
        harmful_count = sum(1 for e in entries if e.get("harmful_judge", False))
        pct_harmful = (harmful_count / n * 100) if n > 0 else 0
        
        manip_scores = [
            e.get("manipulation_score", 1) 
            for e in entries 
            if "manipulation_score" in e and e.get("manipulation_score") is not None
        ]
        avg_manip = sum(manip_scores) / len(manip_scores) if manip_scores else 0
        
        safety_count = sum(1 for e in entries if e.get("safety_judge", True))
        pct_safety = (safety_count / n * 100) if n > 0 else 0
        
        print(f"{scenario:<20} {condition:<18} {n:<4} {pct_harmful:>6.0f}%      {avg_manip:>6.1f}       {pct_safety:>6.0f}%")
    
    print("=" * 100)
    print()


def run_experiment(
    model: str,
    scenarios: list[str] | None = None,
    conditions: list[str] | None = None,
    strategies: list[str] | None = None,
    rollouts: int = 1,
    judge_model: str | None = None,
    use_judge: bool = True,
):
    """Run the full experiment with specified parameters."""
    if scenarios is None:
        scenarios = get_scenario_ids()
    if conditions is None:
        conditions = list(VALID_CONDITIONS)
    if strategies is None:
        strategies = list(INJECTION_STRATEGIES)
    
    # Calculate total samples
    backdoor_samples = len(scenarios) * len(strategies) if "backdoor" in conditions else 0
    other_samples = len(scenarios) * len([c for c in conditions if c != "backdoor"])
    total_samples = (backdoor_samples + other_samples) * rollouts
    
    print(f"\n{'='*70}")
    print(f"Memory Injection Manipulation Experiment")
    print(f"{'='*70}")
    print(f"  Model: {model}")
    print(f"  Judge model: {judge_model or model}")
    print(f"  Scenarios: {len(scenarios)}")
    for sid in scenarios:
        print(f"    - {sid}: {SCENARIOS[sid]['name']}")
    print(f"  Conditions: {conditions}")
    print(f"  Strategies (for backdoor): {strategies}")
    print(f"  Rollouts per sample: {rollouts}")
    print(f"  Total samples: {total_samples}")
    print(f"{'='*70}\n")
    
    # Create task
    task = multi_scenario_injection_eval(
        scenarios=scenarios,
        conditions=conditions,
        strategies=strategies,
        model_name=model,
        use_scorer=use_judge,
        scorer_model=judge_model or model,
    )
    
    try:
        logs = eval(
            task, 
            model=model,
            epochs=rollouts if rollouts > 1 else None,
        )
        
        print(f"\n{'='*70}")
        print(f"Experiment complete!")
        print(f"{'='*70}")
        
        print_results_table(logs)
        
        if rollouts > 1:
            aggregate_results(logs)
        
        # Print log locations
        print("Log files:")
        for log in logs:
            print(f"  {log.location}")
        print()
        
        return logs
        
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"Experiment failed with error:")
        print(f"{str(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'='*70}\n")
        raise


def run_single(
    model: str, 
    scenario_id: str, 
    condition: str,
    strategy: str | None = None,
    judge_model: str | None = None,
    use_judge: bool = True,
):
    """Run a single scenario/condition combination."""
    print(f"\n{'='*70}")
    print(f"Single Scenario Injection Attack")
    print(f"{'='*70}")
    print(f"  Model: {model}")
    print(f"  Scenario: {scenario_id} ({SCENARIOS[scenario_id]['name']})")
    print(f"  Condition: {condition}")
    if condition == "backdoor":
        print(f"  Strategy: {strategy or 'user_review'}")
    print(f"{'='*70}\n")
    
    task = single_scenario_injection_eval(
        scenario_id=scenario_id,
        condition=condition,
        strategy=strategy,
        model_name=model,
        use_scorer=use_judge,
        scorer_model=judge_model or model,
    )
    
    try:
        logs = eval(task, model=model)
        
        print(f"\n{'='*70}")
        print(f"Experiment complete!")
        print(f"{'='*70}")
        
        print_results_table(logs)
        
        print(f"Log file: {logs[0].location}")
        print()
        
        return logs
        
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"Experiment failed with error:")
        print(f"{str(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'='*70}\n")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Run multi-scenario memory injection attack experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available scenarios and conditions
  uv run python scripts/run_injection_scenarios.py --list
  
  # Run all scenarios with all conditions (baseline, direct_pressure, backdoor)
  uv run python scripts/run_injection_scenarios.py --model openrouter/openai/gpt-4o --all
  
  # Run with 5 rollouts per sample for statistical significance
  uv run python scripts/run_injection_scenarios.py --model openrouter/openai/gpt-4o --all --rollouts 5
  
  # Run only baseline and backdoor conditions
  uv run python scripts/run_injection_scenarios.py --model openrouter/openai/gpt-4o --all --conditions baseline,backdoor
  
  # Run specific scenarios
  uv run python scripts/run_injection_scenarios.py --model openrouter/openai/gpt-4o --scenarios financial_steering,medical_allergy
  
  # Run a single scenario with a specific condition
  uv run python scripts/run_injection_scenarios.py --model openrouter/openai/gpt-4o --scenario financial_steering --condition direct_pressure
  
  # Use a different model for judging
  uv run python scripts/run_injection_scenarios.py --model openrouter/openai/gpt-4o --all --judge-model openrouter/anthropic/claude-sonnet-4
  
  # Run without LLM judge (faster, heuristic scoring only)
  uv run python scripts/run_injection_scenarios.py --model openrouter/openai/gpt-4o --all --no-judge
        """
    )
    
    parser.add_argument(
        "--model",
        type=str,
        help="Target model identifier (e.g., openrouter/openai/gpt-4o)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available scenarios, conditions, and strategies"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all scenarios with all conditions"
    )
    parser.add_argument(
        "--scenarios",
        type=str,
        help="Comma-separated list of scenario IDs to run"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        help="Single scenario ID to run (use with --condition)"
    )
    parser.add_argument(
        "--conditions",
        type=str,
        help="Comma-separated list of conditions (baseline,direct_pressure,backdoor). Defaults to all."
    )
    parser.add_argument(
        "--condition",
        type=str,
        choices=VALID_CONDITIONS,
        default="baseline",
        help="Single condition to run (use with --scenario)"
    )
    parser.add_argument(
        "--strategies",
        type=str,
        help="Comma-separated list of strategies for backdoor condition (e.g., 'chat_log,user_review')"
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=list(INJECTION_STRATEGIES),
        help="Single strategy for backdoor condition (use with --scenario)"
    )
    parser.add_argument(
        "--rollouts",
        type=int,
        default=1,
        help="Number of rollouts per sample (for statistical significance). Default: 1"
    )
    parser.add_argument(
        "--judge-model",
        type=str,
        help="Model to use for LLM judge scoring. Defaults to same as target model."
    )
    parser.add_argument(
        "--no-judge",
        action="store_true",
        help="Skip LLM judge scoring (faster, heuristic scoring only)"
    )
    
    args = parser.parse_args()
    
    # Handle --list
    if args.list:
        list_scenarios()
        return
    
    # Validate model is provided for running
    if not args.model:
        if not args.list:
            parser.error("--model is required (unless using --list)")
        return
    
    # Parse conditions if provided
    conditions = None
    if args.conditions:
        conditions = [c.strip() for c in args.conditions.split(",")]
        for c in conditions:
            if c not in VALID_CONDITIONS:
                print(f"Error: Unknown condition '{c}'. Available: {VALID_CONDITIONS}")
                sys.exit(1)
    
    # Parse strategies if provided
    strategies = None
    if args.strategies:
        strategies = [s.strip() for s in args.strategies.split(",")]
        for st in strategies:
            if st not in INJECTION_STRATEGIES:
                print(f"Error: Unknown strategy '{st}'. Available: {INJECTION_STRATEGIES}")
                sys.exit(1)
    
    use_judge = not args.no_judge
    
    if args.all:
        run_experiment(
            model=args.model,
            conditions=conditions,
            strategies=strategies,
            rollouts=args.rollouts,
            judge_model=args.judge_model,
            use_judge=use_judge,
        )
    elif args.scenarios:
        scenario_ids = [s.strip() for s in args.scenarios.split(",")]
        # Validate scenario IDs
        for sid in scenario_ids:
            if sid not in SCENARIOS:
                print(f"Error: Unknown scenario '{sid}'")
                list_scenarios()
                sys.exit(1)
        run_experiment(
            model=args.model,
            scenarios=scenario_ids,
            conditions=conditions,
            strategies=strategies,
            rollouts=args.rollouts,
            judge_model=args.judge_model,
            use_judge=use_judge,
        )
    elif args.scenario:
        if args.scenario not in SCENARIOS:
            print(f"Error: Unknown scenario '{args.scenario}'")
            list_scenarios()
            sys.exit(1)
        run_single(
            model=args.model, 
            scenario_id=args.scenario, 
            condition=args.condition,
            strategy=args.strategy,
            judge_model=args.judge_model,
            use_judge=use_judge,
        )
    else:
        parser.error("Specify --all, --scenarios, or --scenario")


if __name__ == "__main__":
    main()
