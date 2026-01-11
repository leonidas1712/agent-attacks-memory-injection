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

logs/                   # InspectAI evaluation logs (.eval files)

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

## Running Experiments

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

## Analysis

After running experiments, generate charts and tables:

```bash
uv run python results/scripts/run_analysis.py
```

This will:
1. Extract results from `.eval` logs
2. Generate charts (saved to `results/charts/`)
3. Generate tables (saved to `results/tables/`)

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

