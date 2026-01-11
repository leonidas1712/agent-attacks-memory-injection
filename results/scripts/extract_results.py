"""
Extract experiment results from InspectAI log files.

Reads eval logs directly and extracts metrics for visualization and reporting.
"""

import sys
from pathlib import Path
import pandas as pd
from typing import Optional
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from inspect_ai.log import read_eval_log, EvalLog, list_eval_logs


def extract_injection_data(logs_dir: str | Path = "logs") -> pd.DataFrame:
    """
    Extract sample-level data from injection experiment logs.
    
    Args:
        logs_dir: Directory containing .eval log files
        
    Returns:
        DataFrame with columns: model, scenario_id, condition, strategy,
        harmful_recommendation, manipulation_score, safety_warning_present,
        injection_triggered, target_overwritten, etc.
    """
    logs_dir = Path(logs_dir)
    
    # Filter to injection experiment logs only
    def is_injection_log(log: EvalLog) -> bool:
        """Check if log is from injection experiment."""
        task_name = log.eval.task or ""
        return "injection" in task_name.lower() and "5scenarios" in task_name.lower()
    
    log_infos = list_eval_logs(str(logs_dir), filter=is_injection_log, recursive=True)
    
    if not log_infos:
        raise ValueError(f"No injection experiment logs found in {logs_dir}")
    
    print(f"Found {len(log_infos)} injection experiment log(s)")
    
    # Target models to include
    target_models = [
        "openrouter/openai/gpt-4o",
        "openai/gpt-4o",
        "openrouter/openai/gpt-4.1",
        "openai/gpt-4.1",
        "openrouter/anthropic/claude-sonnet-4",
        "anthropic/claude-sonnet-4",
        "openrouter/google/gemini-2.5-pro",
        "google/gemini-2.5-pro",
        "openrouter/x-ai/grok-4-fast",
        "x-ai/grok-4-fast",
    ]
    
    # Extract data from each log
    rows = []
    for log_info in log_infos:
        try:
            log = read_eval_log(log_info.name)
            model = log.eval.model or "unknown"
            
            # Skip if not a target model
            if model not in target_models:
                continue
            
            # Clean model name for display
            model_display = model.replace("openrouter/", "").replace("openai/", "").replace("anthropic/", "").replace("google/", "").replace("x-ai/", "")
            
            if log.samples:
                for sample in log.samples:
                    metadata = sample.metadata or {}
                    results = metadata.get("experiment_results", {})
                    
                    scenario_id = results.get("scenario_id", metadata.get("scenario_id", "unknown"))
                    condition = results.get("condition", metadata.get("condition", "unknown"))
                    strategy = results.get("strategy")
                    
                    # Extract judge scores
                    harmful_recommendation = False
                    manipulation_score = 1
                    safety_warning_present = True
                    
                    if sample.scores:
                        judge_score = sample.scores.get("injection_judge")
                        if judge_score and judge_score.metadata:
                            harmful_recommendation = judge_score.metadata.get("harmful_recommendation", False)
                            manipulation_score = judge_score.metadata.get("manipulation_score", 1)
                            safety_warning_present = judge_score.metadata.get("safety_warning_present", True)
                    
                    row = {
                        "model": model,
                        "model_display": model_display,
                        "scenario_id": scenario_id,
                        "condition": condition,
                        "strategy": strategy,
                        "harmful_recommendation": harmful_recommendation,
                        "manipulation_score": manipulation_score if manipulation_score is not None else 1,
                        "safety_warning_present": safety_warning_present,
                        "injection_triggered": results.get("injection_triggered", False),
                        "target_overwritten": results.get("target_overwritten", False),
                        "sample_id": sample.id,
                        "epoch": sample.epoch,
                    }
                    rows.append(row)
        except Exception as e:
            print(f"Warning: Could not read log {log_info.name}: {e}")
            continue
    
    df = pd.DataFrame(rows)
    
    print(f"Extracted {len(df)} samples")
    if len(df) > 0:
        print(f"Models: {df['model_display'].unique()}")
    
    return df


def aggregate_by_model_condition(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate results by (model, condition), averaging across scenarios and rollouts.
    
    Returns DataFrame with columns: model, condition, pct_harmful, avg_manipulation, etc.
    """
    grouped = df.groupby(["model_display", "condition"]).agg({
        "harmful_recommendation": ["mean", "count"],
        "manipulation_score": "mean",
        "safety_warning_present": "mean",
    }).reset_index()
    
    grouped.columns = [
        "model",
        "condition",
        "pct_harmful",
        "n",
        "avg_manipulation",
        "pct_safety_warning",
    ]
    
    grouped["pct_harmful"] = grouped["pct_harmful"] * 100
    grouped["pct_safety_warning"] = grouped["pct_safety_warning"] * 100
    
    return grouped


def aggregate_by_model_scenario_condition(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate results by (model, scenario, condition).
    
    Returns DataFrame for scenario-level analysis.
    """
    grouped = df.groupby(["model_display", "scenario_id", "condition"]).agg({
        "harmful_recommendation": ["mean", "count"],
        "manipulation_score": "mean",
        "safety_warning_present": "mean",
        "injection_triggered": "mean",
    }).reset_index()
    
    grouped.columns = [
        "model",
        "scenario",
        "condition",
        "pct_harmful",
        "n",
        "avg_manipulation",
        "pct_safety_warning",
        "pct_injection_triggered",
    ]
    
    grouped["pct_harmful"] = grouped["pct_harmful"] * 100
    grouped["pct_safety_warning"] = grouped["pct_safety_warning"] * 100
    grouped["pct_injection_triggered"] = grouped["pct_injection_triggered"] * 100
    
    return grouped


def compute_backdoor_decomposition(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute injection acceptance vs harm given injection for backdoor condition.
    
    Returns DataFrame with columns: model, injection_rate, harm_overall, harm_given_injection
    """
    backdoor_df = df[df["condition"] == "backdoor"].copy()
    
    grouped = backdoor_df.groupby("model_display").agg({
        "injection_triggered": "mean",
        "harmful_recommendation": "mean",
    }).reset_index()
    
    # Compute harm given injection
    harm_given_injection = []
    for model in grouped["model_display"]:
        model_backdoor = backdoor_df[backdoor_df["model_display"] == model]
        injected = model_backdoor[model_backdoor["injection_triggered"] == True]
        if len(injected) > 0:
            harm_rate = injected["harmful_recommendation"].mean() * 100
        else:
            harm_rate = 0.0
        harm_given_injection.append(harm_rate)
    
    grouped["injection_rate"] = grouped["injection_triggered"] * 100
    grouped["harm_overall"] = backdoor_df.groupby("model_display")["harmful_recommendation"].mean().values * 100
    grouped["harm_given_injection"] = harm_given_injection
    
    # Determine failure mode
    def determine_failure_mode(row):
        if row["injection_rate"] < 50:
            return "Injection resistance"
        elif row["harm_given_injection"] < 50:
            return "Response-level safety"
        else:
            return "Accepts injection, unsafe response"
    
    grouped["failure_mode"] = grouped.apply(determine_failure_mode, axis=1)
    
    return grouped[["model_display", "injection_rate", "harm_overall", "harm_given_injection", "failure_mode"]].rename(
        columns={"model_display": "model"}
    )


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract results from injection experiment logs")
    parser.add_argument("--logs-dir", default="logs", help="Directory containing .eval log files")
    parser.add_argument("--output", default="results/aggregated_results.csv", help="Output CSV path")
    parser.add_argument("--full-output", default="results/full_results.csv", help="Output CSV path for full sample-level data")
    
    args = parser.parse_args()
    
    print("Extracting results from logs...")
    df = extract_injection_data(args.logs_dir)
    
    # Save full sample-level data
    full_output_path = Path(args.full_output)
    full_output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(full_output_path, index=False)
    print(f"\nSaved full sample-level data to: {full_output_path}")
    
    print("\nAggregating by model and condition...")
    aggregated = aggregate_by_model_condition(df)
    
    print("\nSaving aggregated results to CSV...")
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    aggregated.to_csv(output_path, index=False)
    
    print(f"\nSaved aggregated results to: {output_path}")
    print(f"\nSummary:")
    print(aggregated.to_string())

