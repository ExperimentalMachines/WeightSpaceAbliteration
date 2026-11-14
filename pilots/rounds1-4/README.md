# `pilots/rounds1-4/`: the earlier Qwen3.5-0.8B pilots (2026-11-05 to 2026-11-10)

Development work that came before rounds 5 to 9. Like everything in `pilots/` it is outside any registered run: no receipts, no admitted method, nothing here is a result of the registered study.
It is added so the pilot record has no gap: rounds 5 and 6 refer to "rounds 1-4" without them being in this repository.

| Round | What | Notes |
|---|---|---|
| 1 | Code-computed edits (stages 0 to 6) to weaken Qwen3.5-0.8B's **over-refusal of harmless prompts** | `notes/all_attempts_and_methods.md` section 3, `notes/results_report.md`, `notes/stage1_report.md`, `results/stage*.json` |
| 2 | The published false-refusal-vector recipe (Wang et al., ICLR 2025), preregistered | `notes/prereg_round2.md`, `notes/results_round2.md`, `results/r2_*.json` |
| 3 | The LLM editor (Claude) writes the weights in a live Python session, 50 forward passes, no gradients | `notes/prereg_round3.md`, `notes/results_round3.md`, `results/r3_final.json`, `results/judge_labels_claude_r3.json` |
| 4 | First four-method **refusal-removal** benchmark on Qwen3.5-0.8B (Arditi, Heretic, OBLITERATUS attempt, WSP-Full), HarmBench-Val-60 | `notes/prereg_round4.md`, `notes/results_round4_benchmark.md`, `notes/audit_round4_gpt.md`, `notes/audit_round4_response.md`, `results/chosen.json`, `results/info.json`, `results/passes.json` |

Rounds 1 to 3 targeted a different guardrail (over-refusal of harmless-but-edgy prompts) than rounds 4 to 9 (refusal of harmful prompts). The original over-refusal gate (XSTest-safe refusal of at least 10%) was never met (4.0%), so rounds 1 to 3 are exploratory. Round 4 is where WSP-Full was first made; round 5 reproduced it exactly (see `../qwen3.5-0.8b/WSP_edits.md`). The round-4 WSP patch was lost with its host storage, so only its digest, size and per-matrix record (`results/info.json`) remain.

## What was left out, and why
- Execution-host and billing details (provider, hardware, prices, spend, host names and storage). Where they appeared in a source line, the line is replaced by a marker or the term is generalised ("host"); nothing else was reworded.
- Editor session logs (`r3_session.log`, `r4/session.log`) because the round-3 log prints an example prompt from an over-refusal corpus; no prompt corpus belongs in this repository (`CONTRIBUTING.md`).
- Generated text, edited weights, rank-1 factors and refusal-direction vectors, and the per-prompt judge key and sample files (consistent with `SECURITY.md`).
- `judge_claude_summary_r3.json` (contains prompt fields).

The files are copied from the authors' working repository; where a note says "files" or paths of the working repository (`results/...`), the same file is in `results/` here under its base name.
