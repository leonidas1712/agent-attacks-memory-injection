#!/usr/bin/env python3
"""
Master script to run complete analysis pipeline.

Extracts data from logs, generates charts, and creates tables.
"""

import sys
from pathlib import Path
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Run the complete analysis pipeline."""
    scripts_dir = Path(__file__).parent
    project_root = scripts_dir.parent.parent
    
    print("=" * 70)
    print("Injection Experiment Analysis Pipeline")
    print("=" * 70)
    
    # Step 1: Extract results
    print("\n[1/3] Extracting results from log files...")
    extract_script = scripts_dir / "extract_results.py"
    result = subprocess.run(
        [sys.executable, str(extract_script), "--logs-dir", "logs"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error extracting results:\n{result.stderr}")
        return 1
    print(result.stdout)
    
    # Step 2: Generate charts
    print("\n[2/3] Generating charts...")
    charts_script = scripts_dir / "generate_charts.py"
    result = subprocess.run(
        [sys.executable, str(charts_script), "--input", "results/full_results.csv"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error generating charts:\n{result.stderr}")
        return 1
    print(result.stdout)
    
    # Step 3: Generate tables
    print("\n[3/3] Generating tables...")
    tables_script = scripts_dir / "generate_tables.py"
    result = subprocess.run(
        [sys.executable, str(tables_script), "--input", "results/full_results.csv"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error generating tables:\n{result.stderr}")
        return 1
    print(result.stdout)
    
    print("\n" + "=" * 70)
    print("Analysis complete!")
    print("=" * 70)
    print("\nOutput files:")
    print("  - results/full_results.csv (sample-level data)")
    print("  - results/aggregated_results.csv (aggregated by model/condition)")
    print("  - results/charts/*.png (visualizations)")
    print("  - results/tables/*.md (markdown tables)")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

