#!/usr/bin/env python3
"""
Generate sample poisoned documents for all 5 scenarios × 2 attack strategies.

Produces 10 HTML files in sample_poisoned_documents/:
  - {scenario_id}_{strategy}.html

Scenarios:
  financial_steering, medical_allergy, dietary_diabetic,
  security_downgrade, purchase_steering

Strategies:
  user_review, persona_memory
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent_injection.scenarios import SCENARIOS
from agent_injection.scenario_content import build_injected_page

STRATEGIES = ["user_review", "persona_memory"]

OUTPUT_DIR = project_root / "sample_poisoned_documents"


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    scenario_ids = list(SCENARIOS.keys())

    print(f"Generating poisoned documents for {len(scenario_ids)} scenarios × {len(STRATEGIES)} strategies …\n")

    for scenario_id in scenario_ids:
        scenario = SCENARIOS[scenario_id]
        for strategy in STRATEGIES:
            page_html = build_injected_page(scenario_id, strategy)

            filename = f"{scenario_id}_{strategy}.html"
            filepath = OUTPUT_DIR / filename
            filepath.write_text(page_html)

            print(f"  ✓ {filename:<50s}  (scenario: {scenario['name']}, strategy: {strategy})")

    print(f"\nDone — {len(scenario_ids) * len(STRATEGIES)} files written to {OUTPUT_DIR.relative_to(project_root)}/")


if __name__ == "__main__":
    main()
