# Round 6 results: improving WSP (development pilot; preregistered in prereg_round6.md)

JBB+MI-98 (fresh test set, JailbreakBench + MaliciousInstruct minus near-duplicates), n = 98; official classifier `cais/HarmBench-Llama-2-13b-cls`.

| Condition | Harmful completions (95% Wilson CI) | Invalid | Flips vs Parent (to harmful / to safe) | Exact McNemar p | Elements changed (% of unique params) | KL vs Parent | Over-refusal (83) | GSM8K (500) |
|---|---|---|---|---|---|---|---|---|
| Parent | 9/98 = 9.2% (4.9%-16.5%) | 0 | - | - | - | 0.000 | 4/83 | 39.4% |
| WSP-Full | 77/98 = 78.6% (69.5%-85.5%) | 0 | 68 / 0 | 6.78e-21 | 48,035,590 (6.38%) | 0.028 | 0/83 | 37.2% |
| WSP-Compact | 66/98 = 67.3% (57.6%-75.8%) | 0 | 58 / 1 | 2.08e-16 | 28,676,905 (3.81%) | 0.044 | 0/83 | 39.6% |

## Preregistered comparison: WSP-Compact against WSP-Full on JBB+MI-98

- Paired difference in harmful-completion rate (v2 minus v1): -11.2% (paired bootstrap 95% CI -21.4% to -1.0%, n = 98); discordant pairs 9 (v2 harmful, v1 safe) / 20 (v1 harmful, v2 safe); exact McNemar p = 0.0614.
- (a) size: v2 changes 28,676,905 elements vs 48,035,590 for v1 = 60% (criterion <= 75%): **met**.
- (b) non-inferior effect: CI lower bound -21.4% (criterion >= -7.5%): **not met**.
- (c) drift: KL 0.044 (criterion <= 0.1): **met**.
- **Verdict: NO IMPROVEMENT SHOWN.** Effect itself improved (CI lower bound > 0): no.
