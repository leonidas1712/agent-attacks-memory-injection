"""
Generate charts for Chinese models follow-up experiment.

Shows strategy comparison (user_review vs persona_memory) for harm rate
and stealth score across 3 Chinese models.

Usage:
  uv run python results/scripts/generate_charts_chinese.py
"""

import sys
from pathlib import Path
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from inspect_ai.log import read_eval_log

# --- Style (matches existing charts) ---
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

# --- Data ---
CHINESE_LOG_DIR = project_root / "logs" / "new_data_chinese_models"
CHINESE_LOGS = [
    CHINESE_LOG_DIR / "2026-02-16T07-43-01+00-00_injection-5scenarios-backdoor_openrouter-moonshotai-kimi-k2.5_NS7w8UXxC4bDhXSU3bVCVh.eval",
    CHINESE_LOG_DIR / "2026-02-16T09-00-44+00-00_injection-5scenarios-backdoor_openrouter-z-ai-glm-4.7-flash_4PJrcfZNxUQmQxRFSmahqm.eval",
    CHINESE_LOG_DIR / "2026-02-16T09-19-20+00-00_injection-5scenarios-backdoor_openrouter-deepseek-deepseek-v3.1-terminus-exacto_cbCUCVtqU6Z2kNSLRYCWSw.eval",
]

MODEL_NAMES = {
    "openrouter/moonshotai/kimi-k2.5": "Kimi K2.5",
    "openrouter/z-ai/glm-4.7-flash": "GLM-4.7-Flash",
    "openrouter/deepseek/deepseek-v3.1-terminus:exacto": "DeepSeek V3.1\nTerminus",
}

MODEL_ORDER = [
    "openrouter/moonshotai/kimi-k2.5",
    "openrouter/deepseek/deepseek-v3.1-terminus:exacto",
    "openrouter/z-ai/glm-4.7-flash",
]


def load_strategy_data():
    """Load per-model, per-strategy aggregated metrics from eval logs."""
    # model -> strategy -> {harm_rates: [], stealth_scores: [], manip_scores: []}
    data = defaultdict(lambda: defaultdict(lambda: {
        "harmful": [], "injected": [], "stealth": [], "manipulation": [],
    }))

    for log_path in CHINESE_LOGS:
        if not log_path.exists():
            print(f"WARNING: {log_path} not found")
            continue
        log = read_eval_log(str(log_path))
        model = log.eval.model

        if not log.samples:
            continue
        for sample in log.samples:
            meta = sample.metadata or {}
            if meta.get("condition") != "backdoor":
                continue
            strategy = meta.get("strategy")
            if not strategy:
                continue

            exp = meta.get("experiment_results", {})
            injected = exp.get("target_overwritten", False)

            harmful = False
            manip = None
            stealth = None
            if sample.scores:
                ij = sample.scores.get("injection_judge")
                if ij and ij.metadata:
                    harmful = ij.metadata.get("harmful_recommendation", False)
                    manip = ij.metadata.get("manipulation_score")
                sj = sample.scores.get("stealth_judge")
                if sj and sj.metadata and injected:
                    stealth = sj.metadata.get("stealth_score")

            data[model][strategy]["harmful"].append(harmful)
            data[model][strategy]["injected"].append(injected)
            if manip is not None:
                data[model][strategy]["manipulation"].append(manip)
            if stealth is not None:
                data[model][strategy]["stealth"].append(stealth)

    # Compute aggregates
    results = {}
    for model in MODEL_ORDER:
        if model not in data:
            continue
        results[model] = {}
        for strategy in ["user_review", "persona_memory"]:
            d = data[model][strategy]
            n = len(d["harmful"])
            if n == 0:
                continue
            results[model][strategy] = {
                "harm_rate": sum(d["harmful"]) / n * 100,
                "avg_stealth": sum(d["stealth"]) / len(d["stealth"]) if d["stealth"] else 0,
                "avg_manip": sum(d["manipulation"]) / len(d["manipulation"]) if d["manipulation"] else 0,
                "inject_rate": sum(d["injected"]) / n * 100,
            }

    return results


def generate_chart(results, output_dir: Path):
    """Generate a two-panel chart: harm rate + stealth by strategy."""
    output_dir.mkdir(parents=True, exist_ok=True)

    models = [m for m in MODEL_ORDER if m in results]
    labels = [MODEL_NAMES.get(m, m) for m in models]

    ur_harm = [results[m]["user_review"]["harm_rate"] for m in models]
    pm_harm = [results[m]["persona_memory"]["harm_rate"] for m in models]
    ur_stealth = [results[m]["user_review"]["avg_stealth"] for m in models]
    pm_stealth = [results[m]["persona_memory"]["avg_stealth"] for m in models]

    x = np.arange(len(models))
    width = 0.32

    colors = {
        "user_review": "#0d6efd",     # Blue (matches existing palette)
        "persona_memory": "#fd7e14",  # Orange
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5))

    # --- Panel A: Harm Rate ---
    bars1a = ax1.bar(x - width / 2, ur_harm, width,
                     label="user_review", color=colors["user_review"], alpha=0.85)
    bars1b = ax1.bar(x + width / 2, pm_harm, width,
                     label="persona_memory", color=colors["persona_memory"], alpha=0.85)

    ax1.set_ylabel("% Harmful Recommendation", fontweight="bold")
    ax1.set_title("(a) Harm Rate by Strategy", fontweight="bold", pad=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, ha="center")
    ax1.set_ylim(0, 109)
    ax1.grid(axis="y", alpha=0.3, linestyle="--")

    for bars in [bars1a, bars1b]:
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax1.text(bar.get_x() + bar.get_width() / 2., h + 1,
                         f'{h:.0f}%', ha='center', va='bottom', fontsize=9)

    # --- Panel B: Stealth Score ---
    bars2a = ax2.bar(x - width / 2, ur_stealth, width,
                     label="user_review", color=colors["user_review"], alpha=0.85)
    bars2b = ax2.bar(x + width / 2, pm_stealth, width,
                     label="persona_memory", color=colors["persona_memory"], alpha=0.85)

    ax2.set_ylabel("Average Stealth Score (1–5)", fontweight="bold")
    ax2.set_title("(b) Stealth Score by Strategy", fontweight="bold", pad=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, ha="center")
    ax2.set_ylim(0, 5.8)
    ax2.grid(axis="y", alpha=0.3, linestyle="--")

    for bars in [bars2a, bars2b]:
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax2.text(bar.get_x() + bar.get_width() / 2., h + 0.08,
                         f'{h:.1f}', ha='center', va='bottom', fontsize=9)

    # Shared legend
    handles, lbls = ax1.get_legend_handles_labels()
    fig.legend(handles, lbls, loc="lower center", bbox_to_anchor=(0.5, -0.02),
               ncol=2, frameon=True, fancybox=True, shadow=True)

    fig.suptitle("Chinese Models: Injection Strategy Comparison (Backdoor Condition)",
                 fontweight="bold", fontsize=14, y=1.02)

    plt.tight_layout()
    out = output_dir / "chart5_chinese_strategy_comparison.png"
    plt.savefig(out, bbox_inches='tight')
    print(f"Saved: {out}")
    plt.close()


def main():
    print("Loading eval logs...")
    results = load_strategy_data()

    # Print quick summary to verify
    for model in MODEL_ORDER:
        if model not in results:
            continue
        name = MODEL_NAMES.get(model, model)
        for strat in ["user_review", "persona_memory"]:
            s = results[model][strat]
            print(f"  {name:>22s}  {strat:<16s}  harm={s['harm_rate']:.0f}%  stealth={s['avg_stealth']:.1f}  manip={s['avg_manip']:.1f}")

    output_dir = project_root / "results" / "charts"
    generate_chart(results, output_dir)
    print("Done!")


if __name__ == "__main__":
    main()
