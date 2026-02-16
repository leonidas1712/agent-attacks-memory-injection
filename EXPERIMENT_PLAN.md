# Experiment Plan: Extending Memory Injection Results

## Context

Our original benchmark (in `logs/benchmark_logs/`) tested 5 Western models with the `user_review` injection strategy across 5 scenarios × 3 conditions × 5 rollouts. Exploratory runs with the new `persona_memory` strategy on Chinese models (kimi-k2.5, deepseek-v3.2, glm-4.7-flash) showed high vulnerability (100%, 80%, 40% harm respectively) even with only 1 rollout and 5 samples each.

We want to extend our results for the poster/abstract (deadline: Feb 20) with two findings:

1. **Chinese models are more vulnerable to memory injection** (comparable data using user_review)
2. **Dual-injection trades harm rate for stealth** (persona_memory vs user_review with stealth judge)

## Experiment Design

### Main Run: Chinese Models, Both Strategies, Stealth Judge

- **Models:** kimi-k2.5, deepseek-v3.2, glm-4.7-flash
- **Condition:** backdoor only (skip baseline/direct_pressure to save cost)
- **Strategies:** user_review AND persona_memory
- **Scenarios:** all 5
- **Rollouts:** 3
- **Stealth judge:** enabled
- **Total samples:** 3 models × 5 scenarios × 2 strategies × 3 rollouts = **90 samples**

Optional: add baseline (3 × 5 × 3 = 45 samples) to confirm 0% harm. Cheap since no injection.

### What This Gives Us

1. **user_review harm rates** on Chinese models → directly extends Table 1 from the paper
2. **persona_memory harm rates** on same models → shows dual-injection behavior
3. **Stealth judge scores** for both → demonstrates the harm vs stealth tradeoff
4. Existing GPT-4o multi-strategy data already shows user_review (80%) > persona_memory (40%), so no need to rerun original benchmark models

### Poster/Abstract Additions

**Finding A — "Injection vulnerability varies across providers":**
Extend Table 1 and Figure 1 with Chinese model backdoor harm rates (user_review). Show that some models have near-zero injection resistance.

**Finding B — "Dual-injection trades harm rate for stealth":**
Introduce persona_memory as a variant that pairs content injection with a communication-style override suppressing safety disclaimers. Show that while it may produce lower raw harm rates than user_review, stealth judge scores indicate the attack is less visible to users — a tradeoff between effectiveness and detectability.

### What We Skip

- Don't rerun original 5 benchmark models with persona_memory (existing GPT-4o data suffices)
- Don't run direct_pressure on Chinese models (not the interesting comparison)
- Don't run GPT-5.2 or Haiku 4.5 (0% harm on persona_memory, mention in passing from exploratory data)
- Don't do full 9-strategy matrix (too expensive, separate study)

### Existing Supporting Data

- GPT-4o multi-strategy run (55 samples, `QTZ6WxPe4pyT4ZYSh9Uvkn`): user_review 80% vs persona_memory 40% harm
- GPT-4o 4-strategy run (20 samples, `GwdCSP6DtWpmnNs4fqec5A`): stealth scores avg 4.8 (most strategies stealthy but ineffective)
- Single-rollout persona_memory across 7 models: kimi 100%, deepseek 80%, glm 40%, gpt-4o 40%, gpt-4.1 40%, gpt-5.2 0%, haiku-4.5 0%

## Validation Step

Before running the full 90-sample experiment, run a quick validation on **one Chinese model** (kimi-k2.5, since it showed 100% vulnerability) with both strategies, no baseline, to confirm the setup works and results are worth pursuing.

- **Model:** kimi-k2.5 (via openrouter: `openrouter/moonshotai/kimi-k2.5`)
- **Condition:** backdoor only
- **Strategies:** user_review, persona_memory
- **Scenarios:** all 5
- **Rollouts:** 1
- **Stealth judge:** enabled
- **Samples:** 5 scenarios × 2 strategies × 1 rollout = **10 samples**
