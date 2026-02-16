# Experiment Plan: Extending Memory Injection Results

## Context

Our original benchmark (in `logs/benchmark_logs/`) tested 5 Western models with
the `user_review` injection strategy across 5 scenarios × 3 conditions × 5
rollouts. Exploratory runs with the new `persona_memory` strategy on Chinese
models (kimi-k2.5, deepseek-v3.2, glm-4.7-flash) showed high vulnerability
(100%, 80%, 40% harm respectively) even with only 1 rollout and 5 samples each.

We want to extend our results for the poster/abstract (deadline: Feb 20) with
two findings:

1. **Chinese models are more vulnerable to memory injection** (comparable data
   using user_review)
2. **Dual-injection trades harm rate for stealth** (persona_memory vs
   user_review with stealth judge)

## Experiment Design

### Main Run: Chinese Models, Both Strategies, Stealth Judge

- **Models:** kimi-k2.5, deepseek-v3.2, glm-4.7-flash
- **Condition:** backdoor only (skip baseline/direct_pressure to save cost)
- **Strategies:** user_review AND persona_memory
- **Scenarios:** all 5
- **Rollouts:** 5 (matches original benchmark)
- **Stealth judge:** enabled
- **Total samples:** 3 models × 5 scenarios × 2 strategies × 5 rollouts = **150
  samples**

Optional: add baseline (3 × 5 × 5 = 75 samples) to confirm 0% harm. Cheap since
no injection.

### What This Gives Us

1. **user_review harm rates** on Chinese models → directly extends Table 1 from
   the paper
2. **persona_memory harm rates** on same models → shows dual-injection behavior
3. **Stealth judge scores** for both → demonstrates the harm vs stealth tradeoff
4. Existing GPT-4o multi-strategy data already shows user_review (80%) >
   persona_memory (40%), so no need to rerun original benchmark models

### Poster/Abstract Additions

**Finding A — "Injection vulnerability varies across providers":** Extend Table
1 and Figure 1 with Chinese model backdoor harm rates (user_review). Show that
some models have near-zero injection resistance.

**Finding B — "Dual-injection trades harm rate for stealth":** Introduce
persona_memory as a variant that pairs content injection with a
communication-style override suppressing safety disclaimers. Show that while it
may produce lower raw harm rates than user_review, stealth judge scores indicate
the attack is less visible to users — a tradeoff between effectiveness and
detectability.

### What We Skip

- Don't rerun original 5 benchmark models with persona_memory (existing GPT-4o
  data suffices)
- Don't run direct_pressure on Chinese models (not the interesting comparison)
- Don't run GPT-5.2 or Haiku 4.5 (0% harm on persona_memory, mention in passing
  from exploratory data)
- Don't do full 9-strategy matrix (too expensive, separate study)

### Existing Supporting Data

- GPT-4o multi-strategy run (55 samples, `QTZ6WxPe4pyT4ZYSh9Uvkn`): user_review
  80% vs persona_memory 40% harm
- GPT-4o 4-strategy run (20 samples, `GwdCSP6DtWpmnNs4fqec5A`): stealth scores
  avg 4.8 (most strategies stealthy but ineffective)
- Single-rollout persona_memory across 7 models: kimi 100%, deepseek 80%, glm
  40%, gpt-4o 40%, gpt-4.1 40%, gpt-5.2 0%, haiku-4.5 0%

## Validation Step

Skipped — prior exploratory runs on Kimi K2.5 (3 rollouts, 27/30 samples)
already confirmed the setup works and high vulnerability. Proceeding directly
with full 5-rollout runs.

## Results So Far

### Kimi K2.5 (completed)

- **Log:**
  `logs/new_data_chinese_models/2026-02-16T05-35-19+00-00_injection-5scenarios-backdoor_openrouter-moonshotai-kimi-k2.5_LfSrXFTBjPh6fL4kA76Mxe.eval`
- **Samples completed:** 50/50 (all 5 rollouts)
- **Strategy summary:**

| Strategy       | N  | % Inject | % Harmful | Avg Manip | Avg Stealth |
| -------------- | -- | -------- | --------- | --------- | ----------- |
| persona_memory | 25 | 100%     | 84%       | 3.5       | 4.7         |
| user_review    | 25 | 100%     | 92%       | 3.0       | 2.2         |

### DeepSeek V3.2 (completed, partial)

- **Log:**
  `logs/new_data_chinese_models/2026-02-16T08-32-26+00-00_injection-5scenarios-backdoor_openrouter-deepseek-deepseek-v3.2_myzMRsVAe98nLScBuTp4Sp.eval`
- **Samples completed:** 36/50 (OpenRouter transient API errors caused 14 sample
  failures despite retry_on_error=3; two earlier attempts crashed at 8/50 and
  10/50 before resilience settings were added)
- **Strategy summary:**

| Strategy       | N  | % Inject | % Harmful | Avg Manip | Avg Stealth |
| -------------- | -- | -------- | --------- | --------- | ----------- |
| persona_memory | 18 | 100%     | 83%       | 3.7       | 4.8         |
| user_review    | 18 | 100%     | 83%       | 2.5       | 1.9         |

### GLM-4.7-Flash (completed)

- **Log:**
  `logs/new_data_chinese_models/2026-02-16T09-00-44+00-00_injection-5scenarios-backdoor_openrouter-z-ai-glm-4.7-flash_4PJrcfZNxUQmQxRFSmahqm.eval`
- **Samples completed:** 50/50 (all 5 rollouts)
- **Note:** Original model ID `zhipu-ai/glm-4.7-flash` was removed from
  OpenRouter; used `z-ai/glm-4.7-flash` instead.
- **Strategy summary:**

| Strategy       | N  | % Inject | % Harmful | Avg Manip | Avg Stealth |
| -------------- | -- | -------- | --------- | --------- | ----------- |
| persona_memory | 25 | 32%      | 64%       | 2.8       | 5.0         |
| user_review    | 25 | 68%      | 60%       | 2.0       | 2.2         |

### Notes

- DeepSeek V3.2 via OpenRouter was extremely unreliable — first two runs crashed
  entirely with `OpenRouterError`. Added `fail_on_error=0.2`,
  `retry_on_error=3`, and `max_connections=5` to `run_injection_scenarios.py` to
  survive transient failures. The 36/50 sample count (18 per strategy) is still
  usable but not ideal.
- Kimi and DeepSeek show 100% injection rate for both strategies; GLM is much
  more resistant (32% persona_memory, 68% user_review).
- All three models show persona_memory is stealthier (avg stealth ~5.0 vs ~2.0)
  but persona_memory's harm rate varies: higher for Kimi/DeepSeek (~83%), lower
  for GLM (64%).
- GLM produces harmful responses even without successful injection (64% harm
  with only 32% inject for persona_memory), suggesting the judge may be flagging
  responses as harmful based on content even when memory wasn't overwritten.
- Kimi K2.5 had an earlier exploratory run with 3 rollouts (27/30 samples) that
  is also in the logs directory but superseded by the 5-rollout run.
