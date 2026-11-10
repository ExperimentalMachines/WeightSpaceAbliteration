# WSP edits: names, recipes, checksums and results

Both edits were written by an LLM (Claude) in a live Python session over Qwen3.5-0.8B (`Qwen/Qwen3.5-0.8B` @ `2fc06364`): no gradients, 50 forward passes, data from the study's `derivation` and `harmless` arms only.
Each edit is a set of rank-1 projections `W <- W - alpha * r (r^T W)` of writer matrices, stored as bit-exact factors (rebuild checked 100.0% identical to the live weights). Edited weights are not published.

| Name | Old labels | Recipe | Matrices | Elements changed | Factor file (sha256) |
|---|---|---|---|---|---|
| **WSP-Full** | "WSP", "wsp", "WSP-v1", round-5 edit | one shared layer-14 direction (mean activation on harmful minus harmless prompts, last template position), alpha 1, top-20 writers by contribution | 20 | 48,035,590 (6.4% of 752,393,024 unique parameters) | `2f1548c8db228bc6b71516cae5e9fca3d8b59023c7905e7413b9395303eeafe5` |
| **WSP-Compact** | "WSP-v2", round-6 edit | the same ranking, top-12 writers, each projected off its own local harmful-minus-harmless output direction, alpha 1; chosen by judged harmful count on 80 derivation prompts | 12 | 28,676,905 (3.8%) | `74e38dbfd2b3191fd35c16d3fa417530448803b130bb3f9babc8a2ba37eafb44` |

WSP-Full is the edit first made in round 4; round 5 reproduced it exactly (same 20 matrices, same changed elements), so it is a replication, not an improvement.
WSP-Compact was the one improvement attempt (round 6). It did **not** meet the preregistered improvement criterion; it is a smaller, weaker variant.

## Results
| Test set | Parent | WSP-Full | WSP-Compact | Others on the same set |
|---|---|---|---|---|
| StrongREJECT-267 (round 5) | 19.1% | 76.4% | not measured | Arditi paper 81.6%, Arditi matched 72.7%, Heretic 81.3% |
| HarmBench-Val-60 (round 5) | 33.3% | 73.3% | not measured | Arditi paper 68.3%, Arditi matched 71.7%, Heretic 71.7% |
| JBB+MI-98 (round 6) | 9.2% | 78.6% | 67.3% | not measured |

Harmful completions as labelled by the HarmBench classifier (`cais/HarmBench-Llama-2-13b-cls` @ `bda70534`), greedy, 512 new tokens, no system prompt. WSP-Full on JBB+MI-98 minus WSP-Compact: 11.2 points (paired bootstrap 95% CI 1.0 to 21.4; exact McNemar p = 0.061).

| | WSP-Full | WSP-Compact |
|---|---|---|
| First-token KL vs parent | 0.028 | 0.044 |
| GSM8K train 500 (parent 39.4%) | 37.2% | 39.6% |
| Benign over-refusal, 83 prompts (parent 4/83) | 0/83 | 0/83 |
| Factor payload (fp16) | 109 KiB with one shared direction (147 KiB as stored, one direction per matrix) | 87 KiB (one direction per matrix) |

## Matrices
- WSP-Full (20): L1.lin_out, L10.lin_out, L10.mlp_down, L11.attn_o, L11.mlp_down, L12.lin_out, L12.mlp_down, L13.lin_out, L13.mlp_down, L2.lin_out, L3.attn_o, L3.mlp_down, L5.lin_out, L6.lin_out, L6.mlp_down, L7.attn_o, L7.mlp_down, L8.mlp_down, L9.lin_out, L9.mlp_down
- WSP-Compact (12): L10.lin_out, L10.mlp_down, L11.attn_o, L11.mlp_down, L12.lin_out, L12.mlp_down, L13.lin_out, L13.mlp_down, L5.lin_out, L7.attn_o, L9.lin_out, L9.mlp_down

## Limits
Same editor with the same knowledge in every round (not independent discovery); one model, one seed; test sets of 267, 60 and 98 prompts; classifier validity on StrongREJECT and JBB+MI prompts unvalidated and replies are deleted after judging.
WSP-Compact was selected on 80 derivation prompts and generalised worse than WSP-Full on fresh prompts. The preregistered files keep their original labels (`wsp`, `wsp_v1`, `wsp_v2`, D1, D2, D3); this table is the mapping.
