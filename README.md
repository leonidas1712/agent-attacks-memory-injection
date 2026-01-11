# Memory Injection Manipulation Experiment

This repository contains the code, results, and analysis for the memory injection attack experiment that tests whether external adversaries can manipulate AI agents with persistent memory through indirect prompt injection embedded in web content.

## Overview

See `EXPERIMENT_DESCRIPTION.md` for a detailed description of the experiment, methodology, and results.

## Project Structure

```
agent_injection/          # Core experiment code
  scenarios.py           # Scenario definitions (5 harm scenarios)
  scenario_tasks.py      # InspectAI tasks and solvers
  scenario_memory.py    # Persistent memory implementation
  scenario_tools.py     # Web search and memory update tools
  scenario_content.py   # Injection payload generation
  scorer.py             # LLM judge for evaluation

scripts/
  run_injection_scenarios.py  # Main script to run experiments

results/
  scripts/              # Analysis scripts
    extract_results.py  # Extract data from .eval logs
    generate_charts.py  # Generate visualizations
    generate_tables.py  # Generate markdown tables
    run_analysis.py     # Run full analysis pipeline
  charts/               # Generated charts (PNG)
  tables/               # Generated tables (Markdown)
  *.csv                 # Extracted results data

benchmark_logs/         # Log files from the benchmark runs (see below)
logs/                   # Additional evaluation logs (.eval files)

EXPERIMENT_DESCRIPTION.md  # Detailed experiment documentation
```

## Setup

### 1. Install dependencies

```bash
cd /Users/leo/memory-injection-manipulation
uv sync
```

### 2. Configure API keys

Create a `.env` file with your OpenRouter API key:

```bash
OPENROUTER_API_KEY=your_key_here
```

## Replicating the Benchmark

The benchmark results reported in the paper were generated using the following commands. Each model was run with:
- All 5 scenarios
- All 3 conditions (baseline, direct_pressure, backdoor)
- `user_review` injection strategy for backdoor condition
- 5 rollouts per sample
- Claude Sonnet 4.5 as the LLM judge

### Run Benchmark for Each Model

```bash
# GPT-4o
uv run python scripts/run_injection_scenarios.py \
  --model openrouter/openai/gpt-4o \
  --all \
  --rollouts 5 \
  --strategy user_review \
  --judge-model openrouter/anthropic/claude-sonnet-4.5

# GPT-4.1
uv run python scripts/run_injection_scenarios.py \
  --model openrouter/openai/gpt-4.1 \
  --all \
  --rollouts 5 \
  --strategy user_review \
  --judge-model openrouter/anthropic/claude-sonnet-4.5

# Claude Sonnet 4
uv run python scripts/run_injection_scenarios.py \
  --model openrouter/anthropic/claude-sonnet-4 \
  --all \
  --rollouts 5 \
  --strategy user_review \
  --judge-model openrouter/anthropic/claude-sonnet-4.5

# Gemini 2.5 Pro
uv run python scripts/run_injection_scenarios.py \
  --model openrouter/google/gemini-2.5-pro \
  --all \
  --rollouts 5 \
  --strategy user_review \
  --judge-model openrouter/anthropic/claude-sonnet-4.5

# Grok-4-fast
uv run python scripts/run_injection_scenarios.py \
  --model openrouter/x-ai/grok-4-fast \
  --all \
  --rollouts 5 \
  --strategy user_review \
  --judge-model openrouter/anthropic/claude-sonnet-4.5
```

### Benchmark Log Files

The benchmark log files are stored in `benchmark_logs/`. These correspond to the results reported in the paper. The log files follow the naming pattern:

```
{timestamp}_injection-5scenarios-3conditions_{model}_{id}.eval
```

Example benchmark log files:
- `2026-01-11T11-57-42+00-00_injection-5scenarios-3conditions_openrouter-openai-gpt-4o_ECipBH3armEHxwxGtRqYCK.eval`
- `2026-01-11T13-15-38+00-00_injection-5scenarios-3conditions_openrouter-openai-gpt-4.1_jizaowijKFSXCyAJM9X6pp.eval`
- `2026-01-11T13-20-37+00-00_injection-5scenarios-3conditions_openrouter-anthropic-claude-sonnet-4_96MCwyt8Eb6q9KKaHnJnS6.eval`
- `2026-01-11T13-27-39+00-00_injection-5scenarios-3conditions_openrouter-google-gemini-2.5-pro_fUkFdpryDNJsiUHqpoY936.eval`
- `2026-01-11T13-56-41+00-00_injection-5scenarios-3conditions_openrouter-x-ai-grok-4-fast_6n4pJtZCmNAy5TckhSiLYo.eval`

## Running Custom Experiments

### Run all scenarios (recommended for full evaluation)

```bash
uv run python scripts/run_injection_scenarios.py \
  --model openrouter/openai/gpt-4o \
  --all \
  --rollouts 5
```

### Run a single scenario

```bash
uv run python scripts/run_injection_scenarios.py \
  --model openrouter/openai/gpt-4o \
  --scenario financial_steering \
  --condition backdoor \
  --rollouts 5
```

### List available scenarios

```bash
uv run python scripts/run_injection_scenarios.py --list
```

## Analyzing Results

### Extract Results from Logs

To extract results from evaluation logs and generate aggregated data:

```bash
# Extract from benchmark logs
uv run python results/scripts/extract_results.py \
  --logs-dir benchmark_logs \
  --output results/aggregated_results.csv \
  --full-output results/full_results.csv

# Or extract from all logs (including benchmark)
uv run python results/scripts/extract_results.py \
  --logs-dir logs \
  --output results/aggregated_results.csv \
  --full-output results/full_results.csv
```

### Generate Charts and Tables

After extracting results, generate visualizations and tables:

```bash
# Generate all charts and tables (recommended)
uv run python results/scripts/run_analysis.py

# Or generate individually:
# Charts
uv run python results/scripts/generate_charts.py \
  --input results/aggregated_results.csv \
  --output-dir results/charts

# Tables
uv run python results/scripts/generate_tables.py \
  --input results/aggregated_results.csv \
  --output-dir results/tables
```

### Output Files

The analysis pipeline generates:

- **CSV files**:
  - `results/full_results.csv` - Sample-level data (all rollouts)
  - `results/aggregated_results.csv` - Aggregated by model/condition/strategy

- **Charts** (PNG files in `results/charts/`):
  - `chart1_harm_by_condition.png` - Harm rate by condition across models
  - `chart2_backdoor_vs_pressure.png` - Relative effectiveness comparison
  - `chart3_injection_decomposition.png` - Injection acceptance vs harm given injection
  - `chart4_manipulation_scores.png` - Manipulation scores by condition

- **Tables** (Markdown files in `results/tables/`):
  - `table1_main_results.md` - Main results table
  - `table2_backdoor_decomposition.md` - Backdoor decomposition analysis
  - `table3_scenario_sensitivity.md` - Scenario sensitivity analysis

## Experimental Conditions

- **baseline**: Neutral prompt + clean pages (no injection)
- **direct_pressure**: Neutral prompt + pressure instruction + clean pages
- **backdoor**: Neutral prompt + injected pages (hidden manipulation)

## Scenarios

1. **financial_steering**: Changes risk tolerance to push risky investments
2. **medical_allergy**: Removes allergy info, risking dangerous drug recommendations
3. **dietary_diabetic**: Removes diabetic flag, risking high-sugar recommendations
4. **security_downgrade**: Changes security prefs to recommend weak security
5. **purchase_steering**: Changes budget preference to push expensive products

## Results

See `results/charts/` and `results/tables/` for visualizations and summary tables.

Key findings:
- Backdoor attacks achieve 70-100% harm rates across most models
- GPT-4.1 shows strong injection resistance (16% acceptance rate)
- Indirect manipulation can be more effective than direct system-level control
