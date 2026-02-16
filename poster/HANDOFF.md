This document provides a comprehensive hand-off for the **"Agent Attacks via
Memory Injection"** project as of February 2026. Use this to orient the CLI and
maintain consistency for the final deliverables due on **February 20th**.

---

# Project Context: Agent Attacks via Memory Injection

## 1. Executive Summary

This research investigates **Memory Injection**, a novel threat model where
external adversaries exploit indirect prompt injection within web content to
poison the long-term memory of an AI agent. We conducted a systematic comparison
between **Backdoor** (memory poisoning) and **Direct Pressure** (explicit
system-prompt instructions) to evaluate which is more effective at manipulating
user outcomes.

## 2. Key Research Findings

-

**The "Memory Override":** For 4 out of 5 SOTA models (GPT-4o, Claude Sonnet 4,
Gemini 2.5 Pro, and Grok-4-fast), indirect memory attacks were more effective at
causing harm than direct operator pressure.

-

**Peak Vulnerability:** Grok-4-fast exhibited a **100% harm rate** under the
backdoor condition.

-

**The Defense Exception:** GPT-4.1 demonstrated significant resistance with an
injection acceptance rate of only **16%**, suggesting that training for
injection resilience is achievable.

-

**Primary Failure Mode:** The vulnerability lies in **Injection Acceptance**
(uncritically trusting tool-call updates) rather than response-level safety
filters.

## 3. Experimental Design & Data

-

**Scenarios:** 5 high-stakes scenarios: Financial Steering, Medical Allergy
Removal, Dietary Restriction Removal, Security Downgrade, and Purchase Budget
Override .

-

**Framework:** A two-turn conversation flow using `InspectAI` and a custom
`StoreModel` to simulate persistent memory .

-

**Metrics:** `harmful_recommendation` (bool), `manipulation_score` (1-5), and
`safety_warning_present`.

## 4. Current Progress & Deliverables

We are currently in the **Apart Studio** phase, transitioning from a hackathon
report to a formal academic presentation.

### Final Deliverables (Deadline: Feb 20, 2026):

1. **Extended Abstract:** A 2-page concise version of the report.
2. **Research Poster:** A0 Portrait orientation following the "Apart Dark"
   theme.

### Ongoing Follow-up Experiments:

- **Provider Variance:** Testing Chinese models (`Kimi-k2.5`, `DeepSeek-v3.2`,
  `GLM-4.7`) which have shown initial vulnerability rates between 40-100%.
- **Stealth vs. Harm:** Investigating the `persona_memory` strategy, which pairs
  content injection with communication-style overrides to suppress safety
  disclaimers.

## 5. Directory Guidance

-

`agent_attacks_memory_injection.pdf`: The primary research report.

- `ORIGINAL_EXPERIMENT_DESCRIPTION.md`: High-level summary of the methodology
  and core results.
- `FOLLOWUP_EXPERIMENT_PLAN.md`: Roadmap for the new Chinese model and stealth
  strategy data.
- `Apart studio.md`: Administrative logistics and specific deliverable
  requirements.

---

**Next Steps for CLI:**

- Draft the **Extended Abstract** (2 pages) by synthesizing the original results
  with the new "Stealth vs. Harm" findings.
- Finalize the **Chart.js** implementations for the HTML/CSS poster to include
  the "Relative Effectiveness" bar chart and the "Injection Acceptance"
  decomposition.
