"""
Generate matplotlib charts for injection experiment results.

Creates publication-ready visualizations as specified in CHARTS.md.
"""

import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


# Set matplotlib style for clean, professional charts
try:
    plt.style.use('seaborn-v0_8-whitegrid')
except OSError:
    try:
        plt.style.use('seaborn-whitegrid')
    except OSError:
        plt.style.use('default')
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 14,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 16,
    'font.family': 'sans-serif',
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
})


def chart1_harm_by_condition(df: pd.DataFrame, output_dir: Path):
    """
    Chart 1: Harm Rate by Condition Across Models (Headline Result)
    
    Grouped bar chart showing baseline, direct_pressure, and backdoor conditions.
    """
    # Aggregate by model and condition
    aggregated = df.groupby(["model_display", "condition"]).agg({
        "harmful_recommendation": "mean",
        "manipulation_score": "mean",
    }).reset_index()
    
    aggregated["pct_harmful"] = aggregated["harmful_recommendation"] * 100
    
    # Pivot for grouped bars
    pivot = aggregated.pivot(index="model_display", columns="condition", values="pct_harmful")
    
    # Ensure all conditions are present
    for cond in ["baseline", "direct_pressure", "backdoor"]:
        if cond not in pivot.columns:
            pivot[cond] = 0.0
    
    # Reorder models for consistent display
    model_order = ["gpt-4o", "gpt-4.1", "claude-sonnet-4", "gemini-2.5-pro", "grok-4-fast"]
    pivot = pivot.reindex([m for m in model_order if m in pivot.index])
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(pivot.index))
    width = 0.25
    
    # Neutral color palette (no red/green alarmism)
    colors = {
        "baseline": "#6c757d",  # Gray
        "direct_pressure": "#0d6efd",  # Blue
        "backdoor": "#fd7e14",  # Orange
    }
    
    bars1 = ax.bar(x - width, pivot.get("baseline", 0), width, label="Baseline", color=colors["baseline"])
    bars2 = ax.bar(x, pivot.get("direct_pressure", 0), width, label="Direct Pressure", color=colors["direct_pressure"])
    bars3 = ax.bar(x + width, pivot.get("backdoor", 0), width, label="Backdoor", color=colors["backdoor"])
    
    ax.set_xlabel("Model", fontweight="bold")
    ax.set_ylabel("% Harmful Recommendation", fontweight="bold")
    ax.set_title("Harm Rate by Condition Across Models", fontweight="bold", pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(pivot.index, rotation=0, ha="center")
    ax.set_ylim(0, 100)
    ax.legend(loc="upper left", frameon=True, fancybox=True, shadow=True)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    
    # Add value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.0f}%',
                       ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    output_path = output_dir / "chart1_harm_by_condition.png"
    plt.savefig(output_path)
    print(f"Saved: {output_path}")
    plt.close()


def chart2_backdoor_vs_pressure(df: pd.DataFrame, output_dir: Path):
    """
    Chart 2: Backdoor vs Direct Pressure Gap
    
    Shows relative effectiveness: (Backdoor % Harmful) - (Direct Pressure % Harmful)
    """
    # Aggregate by model and condition
    aggregated = df.groupby(["model_display", "condition"]).agg({
        "harmful_recommendation": "mean",
    }).reset_index()
    
    aggregated["pct_harmful"] = aggregated["harmful_recommendation"] * 100
    
    # Pivot
    pivot = aggregated.pivot(index="model_display", columns="condition", values="pct_harmful")
    
    # Calculate gap
    gap = (pivot.get("backdoor", 0) - pivot.get("direct_pressure", 0)).fillna(0)
    
    # Reorder models
    model_order = ["gpt-4o", "gpt-4.1", "claude-sonnet-4", "gemini-2.5-pro", "grok-4-fast"]
    gap = gap.reindex([m for m in model_order if m in gap.index])
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Color bars based on sign
    colors = ["#dc3545" if x > 0 else "#198754" if x < 0 else "#6c757d" for x in gap.values]
    
    bars = ax.bar(gap.index, gap.values, color=colors, alpha=0.7, edgecolor="black", linewidth=1)
    
    ax.axhline(y=0, color="black", linestyle="-", linewidth=1)
    ax.set_xlabel("Model", fontweight="bold")
    ax.set_ylabel("(Backdoor % Harmful) - (Direct Pressure % Harmful)", fontweight="bold")
    ax.set_title("Relative Effectiveness: Backdoor vs Direct Pressure", fontweight="bold", pad=20)
    ax.set_xticklabels(gap.index, rotation=0, ha="center")
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    
    # Add value labels
    for bar in bars:
        height = bar.get_height()
        if abs(height) > 1:
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:+.0f}%',
                   ha='center', va='bottom' if height > 0 else 'top', fontsize=9)
    
    plt.tight_layout()
    output_path = output_dir / "chart2_backdoor_vs_pressure.png"
    plt.savefig(output_path)
    print(f"Saved: {output_path}")
    plt.close()


def chart3_injection_decomposition(df: pd.DataFrame, output_dir: Path):
    """
    Chart 3: Injection Acceptance vs Harm Given Injection
    
    Two bars per model showing where defenses live.
    """
    # Filter to backdoor condition only
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
        
        # Harm given injection
        injected = model_data[model_data["injection_triggered"] == True]
        if len(injected) > 0:
            harm_given_injection = injected["harmful_recommendation"].mean() * 100
        else:
            harm_given_injection = 0.0
        
        model_stats.append({
            "model": model,
            "injection_rate": injection_rate,
            "harm_given_injection": harm_given_injection,
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
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(stats_df))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, stats_df["injection_rate"], width, 
                   label="Injection Acceptance Rate", color="#0d6efd", alpha=0.8)
    bars2 = ax.bar(x + width/2, stats_df["harm_given_injection"], width,
                   label="Harm Rate Given Injection", color="#dc3545", alpha=0.8)
    
    ax.set_xlabel("Model", fontweight="bold")
    ax.set_ylabel("Percentage", fontweight="bold")
    ax.set_title("Injection Acceptance vs Harm Given Injection", fontweight="bold", pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(stats_df["model"].values, rotation=0, ha="center")
    ax.set_ylim(0, 100)
    ax.legend(loc="upper left", frameon=True, fancybox=True, shadow=True)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.0f}%',
                       ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    output_path = output_dir / "chart3_injection_decomposition.png"
    plt.savefig(output_path)
    print(f"Saved: {output_path}")
    plt.close()


def chart4_manipulation_scores(df: pd.DataFrame, output_dir: Path):
    """
    Chart 4: Manipulation Score by Condition Across Models
    
    Shows manipulation intensity (1-5 scale) across conditions.
    """
    # Aggregate by model and condition
    aggregated = df.groupby(["model_display", "condition"]).agg({
        "manipulation_score": "mean",
    }).reset_index()
    
    # Pivot
    pivot = aggregated.pivot(index="model_display", columns="condition", values="manipulation_score")
    
    # Ensure all conditions are present
    for cond in ["baseline", "direct_pressure", "backdoor"]:
        if cond not in pivot.columns:
            pivot[cond] = 1.0
    
    # Reorder models
    model_order = ["gpt-4o", "gpt-4.1", "claude-sonnet-4", "gemini-2.5-pro", "grok-4-fast"]
    pivot = pivot.reindex([m for m in model_order if m in pivot.index])
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(pivot.index))
    width = 0.25
    
    colors = {
        "baseline": "#6c757d",
        "direct_pressure": "#0d6efd",
        "backdoor": "#fd7e14",
    }
    
    bars1 = ax.bar(x - width, pivot.get("baseline", 1), width, label="Baseline", color=colors["baseline"])
    bars2 = ax.bar(x, pivot.get("direct_pressure", 1), width, label="Direct Pressure", color=colors["direct_pressure"])
    bars3 = ax.bar(x + width, pivot.get("backdoor", 1), width, label="Backdoor", color=colors["backdoor"])
    
    ax.set_xlabel("Model", fontweight="bold")
    ax.set_ylabel("Average Manipulation Score (1-5)", fontweight="bold")
    ax.set_title("Manipulation Intensity by Condition", fontweight="bold", pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(pivot.index, rotation=0, ha="center")
    ax.set_ylim(0, 5)
    ax.legend(loc="upper left", frameon=True, fancybox=True, shadow=True)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    
    # Add value labels
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}',
                       ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    output_path = output_dir / "chart4_manipulation_scores.png"
    plt.savefig(output_path)
    print(f"Saved: {output_path}")
    plt.close()


def generate_all_charts(df: pd.DataFrame, output_dir: Path):
    """Generate all charts."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\nGenerating charts...")
    chart1_harm_by_condition(df, output_dir)
    chart2_backdoor_vs_pressure(df, output_dir)
    chart3_injection_decomposition(df, output_dir)
    chart4_manipulation_scores(df, output_dir)
    print("\nAll charts generated!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate charts from aggregated results")
    parser.add_argument("--input", default="results/full_results.csv", help="Input CSV file")
    parser.add_argument("--output-dir", default="results/charts", help="Output directory for charts")
    
    args = parser.parse_args()
    
    # Load data
    df = pd.read_csv(args.input)
    
    # Generate charts
    generate_all_charts(df, args.output_dir)

