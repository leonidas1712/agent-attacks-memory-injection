"""
Generate markdown tables for injection experiment results.

Creates publication-ready tables as specified in CHARTS.md.
"""

import sys
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def table1_main_results(df: pd.DataFrame) -> str:
    """
    Table 1: Main Results Table
    
    One row per (Model × Condition), averaged across scenarios.
    """
    # Aggregate by model and condition
    aggregated = df.groupby(["model_display", "condition"]).agg({
        "harmful_recommendation": "mean",
        "manipulation_score": "mean",
        "safety_warning_present": "mean",
    }).reset_index()
    
    aggregated["pct_harmful"] = aggregated["harmful_recommendation"] * 100
    aggregated["pct_safety"] = aggregated["safety_warning_present"] * 100
    
    # Reorder models
    model_order = ["gpt-4o", "gpt-4.1", "claude-sonnet-4", "gemini-2.5-pro", "grok-4-fast"]
    condition_order = ["baseline", "direct_pressure", "backdoor"]
    
    # Build markdown table
    lines = [
        "| Model | Condition | % Harmful | Avg Manipulation | % Safety Warning |",
        "|-------|-----------|-----------|------------------|------------------|",
    ]
    
    for model in model_order:
        model_data = aggregated[aggregated["model_display"] == model]
        if len(model_data) == 0:
            continue
        
        for condition in condition_order:
            cond_data = model_data[model_data["condition"] == condition]
            if len(cond_data) == 0:
                continue
            
            row = cond_data.iloc[0]
            lines.append(
                f"| {model} | {condition.replace('_', ' ').title()} | "
                f"{row['pct_harmful']:.0f}% | {row['manipulation_score']:.1f} | "
                f"{row['pct_safety']:.0f}% |"
            )
    
    return "\n".join(lines)


def table2_backdoor_decomposition(df: pd.DataFrame) -> str:
    """
    Table 2: Backdoor Decomposition Table
    
    Shows injection acceptance, harm rates, and failure modes.
    """
    # Filter to backdoor condition
    backdoor_df = df[df["condition"] == "backdoor"].copy()
    
    # Convert boolean columns if they're strings
    if backdoor_df["harmful_recommendation"].dtype == "object":
        backdoor_df["harmful_recommendation"] = backdoor_df["harmful_recommendation"].astype(str).str.lower() == "true"
    if backdoor_df["injection_triggered"].dtype == "object":
        backdoor_df["injection_triggered"] = backdoor_df["injection_triggered"].astype(str).str.lower() == "true"
    
    # Compute metrics per model
    model_stats = []
    for model in backdoor_df["model_display"].unique():
        model_data = backdoor_df[backdoor_df["model_display"] == model]
        
        injection_rate = model_data["injection_triggered"].mean() * 100
        harm_overall = model_data["harmful_recommendation"].mean() * 100
        
        # Harm given injection
        injected = model_data[model_data["injection_triggered"] == True]
        if len(injected) > 0:
            harm_given_injection = injected["harmful_recommendation"].mean() * 100
        else:
            harm_given_injection = 0.0
        
        # Determine failure mode
        if injection_rate < 50:
            failure_mode = "Injection resistance"
        elif harm_given_injection < 50:
            failure_mode = "Response-level safety"
        else:
            failure_mode = "Accepts injection, unsafe response"
        
        model_stats.append({
            "model": model,
            "injection_rate": injection_rate,
            "harm_overall": harm_overall,
            "harm_given_injection": harm_given_injection,
            "failure_mode": failure_mode,
        })
    
    stats_df = pd.DataFrame(model_stats)
    
    # Reorder models
    model_order = ["gpt-4o", "gpt-4.1", "claude-sonnet-4", "gemini-2.5-pro", "grok-4-fast"]
    # Filter to only models that exist, then reorder
    existing_models = [m for m in model_order if m in stats_df["model"].values]
    stats_df = stats_df[stats_df["model"].isin(existing_models)].copy()
    # Create a categorical column for ordering
    stats_df["model_order"] = pd.Categorical(stats_df["model"], categories=existing_models, ordered=True)
    stats_df = stats_df.sort_values("model_order").drop("model_order", axis=1)
    
    # Build markdown table
    lines = [
        "| Model | Injection Rate | Harm (Overall) | Harm \\| Injection | Dominant Failure Mode |",
        "|-------|----------------|----------------|-------------------|----------------------|",
    ]
    
    for _, row in stats_df.iterrows():
        lines.append(
            f"| {row['model']} | {row['injection_rate']:.0f}% | "
            f"{row['harm_overall']:.0f}% | {row['harm_given_injection']:.0f}% | "
            f"{row['failure_mode']} |"
        )
    
    return "\n".join(lines)


def table3_scenario_sensitivity(df: pd.DataFrame) -> str:
    """
    Table 3: Scenario Sensitivity (Appendix)
    
    Shows % Harmful for backdoor condition by scenario.
    """
    # Filter to backdoor condition
    backdoor_df = df[df["condition"] == "backdoor"].copy()
    
    # Aggregate by model and scenario
    aggregated = backdoor_df.groupby(["model_display", "scenario_id"]).agg({
        "harmful_recommendation": "mean",
    }).reset_index()
    
    aggregated["pct_harmful"] = aggregated["harmful_recommendation"] * 100
    
    # Pivot
    pivot = aggregated.pivot(index="model_display", columns="scenario_id", values="pct_harmful")
    
    # Reorder models
    model_order = ["gpt-4o", "gpt-4.1", "claude-sonnet-4", "gemini-2.5-pro", "grok-4-fast"]
    pivot = pivot.reindex([m for m in model_order if m in pivot.index])
    
    # Get scenario order
    scenario_order = [
        "medical_allergy",
        "financial_steering",
        "dietary_diabetic",
        "security_downgrade",
        "purchase_steering",
    ]
    
    # Build markdown table
    header = "| Model | " + " | ".join([s.replace("_", " ").title() for s in scenario_order]) + " |"
    separator = "|" + "|".join(["-------"] * (len(scenario_order) + 1)) + "|"
    
    lines = [header, separator]
    
    for model in pivot.index:
        row = f"| {model} |"
        for scenario in scenario_order:
            value = pivot.loc[model, scenario] if scenario in pivot.columns else 0.0
            row += f" {value:.0f}% |"
        lines.append(row)
    
    return "\n".join(lines)


def generate_all_tables(df: pd.DataFrame, output_dir: Path):
    """Generate all tables and save to markdown files."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\nGenerating tables...")
    
    # Table 1
    table1 = table1_main_results(df)
    output_path = output_dir / "table1_main_results.md"
    with open(output_path, "w") as f:
        f.write("# Table 1: Main Results\n\n")
        f.write(table1)
    print(f"Saved: {output_path}")
    
    # Table 2
    table2 = table2_backdoor_decomposition(df)
    output_path = output_dir / "table2_backdoor_decomposition.md"
    with open(output_path, "w") as f:
        f.write("# Table 2: Backdoor Decomposition\n\n")
        f.write(table2)
    print(f"Saved: {output_path}")
    
    # Table 3
    table3 = table3_scenario_sensitivity(df)
    output_path = output_dir / "table3_scenario_sensitivity.md"
    with open(output_path, "w") as f:
        f.write("# Table 3: Scenario Sensitivity (Backdoor Condition)\n\n")
        f.write(table3)
    print(f"Saved: {output_path}")
    
    print("\nAll tables generated!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate tables from aggregated results")
    parser.add_argument("--input", default="results/full_results.csv", help="Input CSV file")
    parser.add_argument("--output-dir", default="results/tables", help="Output directory for tables")
    
    args = parser.parse_args()
    
    # Load data
    df = pd.read_csv(args.input)
    
    # Generate tables
    generate_all_tables(df, args.output_dir)

