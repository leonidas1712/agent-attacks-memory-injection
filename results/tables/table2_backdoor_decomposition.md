# Table 2: Backdoor Decomposition

| Model | Injection Rate | Harm (Overall) | Harm \| Injection | Dominant Failure Mode |
|-------|----------------|----------------|-------------------|----------------------|
| gpt-4o | 83% | 79% | 92% | Accepts injection, unsafe response |
| gpt-4.1 | 16% | 28% | 100% | Injection resistance |
| claude-sonnet-4 | 100% | 84% | 84% | Accepts injection, unsafe response |
| gemini-2.5-pro | 80% | 64% | 60% | Accepts injection, unsafe response |
| grok-4-fast | 92% | 100% | 100% | Accepts injection, unsafe response |