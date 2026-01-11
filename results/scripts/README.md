# Analysis Scripts

Scripts for extracting, analyzing, and visualizing results from injection experiment logs.

## Quick Start

Run the complete analysis pipeline:

```bash
cd /path/to/ai-psychosis
uv run python results/scripts/run_analysis.py
```

This will:
1. Extract data from all injection experiment logs in `logs/`
2. Generate 4 charts in `results/charts/`
3. Generate 3 markdown tables in `results/tables/`

## Individual Scripts

### extract_results.py

Extracts sample-level data from InspectAI log files.

```bash
uv run python results/scripts/extract_results.py --logs-dir logs --output results/aggregated_results.csv
```

Outputs:
- `results/full_results.csv` - Sample-level data (all samples)
- `results/aggregated_results.csv` - Aggregated by (model, condition)

### generate_charts.py

Generates matplotlib visualizations.

```bash
uv run python results/scripts/generate_charts.py --input results/full_results.csv --output-dir results/charts
```

Generates:
- `chart1_harm_by_condition.png` - Headline result: harm rate by condition
- `chart2_backdoor_vs_pressure.png` - Relative effectiveness gap
- `chart3_injection_decomposition.png` - Injection acceptance vs harm
- `chart4_manipulation_scores.png` - Manipulation intensity scores

### generate_tables.py

Generates markdown tables for the report.

```bash
uv run python results/scripts/generate_tables.py --input results/full_results.csv --output-dir results/tables
```

Generates:
- `table1_main_results.md` - Main results by model and condition
- `table2_backdoor_decomposition.md` - Injection acceptance and failure modes
- `table3_scenario_sensitivity.md` - Scenario-level breakdown (appendix)

## Models Analyzed

The scripts automatically filter to these models:
- GPT-4o
- GPT-4.1
- Claude Sonnet 4
- Gemini 2.5 Pro
- Grok-4-fast

## Data Structure

The `full_results.csv` contains sample-level data with columns:
- `model`, `model_display` - Model identifier
- `scenario_id` - Scenario (medical_allergy, financial_steering, etc.)
- `condition` - baseline, direct_pressure, or backdoor
- `strategy` - Injection strategy (for backdoor condition)
- `harmful_recommendation` - Boolean from LLM judge
- `manipulation_score` - 1-5 scale from LLM judge
- `safety_warning_present` - Boolean from LLM judge
- `injection_triggered` - Whether memory injection succeeded
- `target_overwritten` - Whether target memory key was overwritten

