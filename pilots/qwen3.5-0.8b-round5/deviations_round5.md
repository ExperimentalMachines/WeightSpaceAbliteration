# Round 5: deviations from the preregistration and incidents (2026-11-10)

Everything here is what actually happened, in the order it was found. "Effect on results" is my judgement.

| # | What | Effect on results |
|---|---|---|
| 1 | **Infrastructure incident (details removed).** A setup script bug kept a keep-alive loop running; found and fixed by hand. | None on results. |
| 2 | **KL-reference guard added mid-run.** After the parent had started, I saw that an edited condition running before the parent would silently become the KL reference (KL = 0). `kl_to_parent` now takes the condition name and refuses to create the reference for anything but the parent (2 tests). The parent itself ran the earlier code, which differs only in lacking that guard; every other condition ran the guarded code. | None: the parent's KL is 0 by definition and the reference was written by the parent before any other condition measured. |
| 3 | **Concurrency.** The WSP editing session, the Arditi runs, Heretic and the first judge pass shared one GPU. All generation is greedy; results do not depend on timing, but batch composition can change bf16 rounding, so rare one-behaviour label differences between runs of the same model are possible. The judge sensitivity check (original SentencePiece ids vs the runtime tokenizer) differs on 0 labels for the parent, both Arditi variants and WSP, and 1 label for Heretic on D1. | Small and unquantified beyond that. |
| 4 | **Automatic baseline pass.** The editing kernel computes the KL reference at start-up and charges it as pass 1; the session therefore used 27 of 50 passes, one of them automatic. | None. |
| 5 | **Candidate set and recipe.** The nine candidate sets were the same families as round 4 (top-k writers by contribution along one layer-14 direction). The coded rule `choose()` selected the 20-matrix set again (0 refusal flags on harmful_val at KL 0.033), with the same 20 matrices and the same 48,035,590 changed elements as round 4. This is a replication by the same editor with the same knowledge, not an independent discovery; D1 gave 44/60 again. | The WSP result is not independent evidence about LLM editors. |
| 6 | **ARA ran inside its time box.** Heretic's ARA search finished all 100 trials in about 33 minutes, inside the 50-minute box, so the planned resume from the Optuna checkpoint was not needed. | None. |
| 7 | **Connection resets** during monitoring; all work ran detached and was unaffected. | None. |
| 8 | **Round-4 disclosures carried forward:** XSTest-safe (frozen `over_refusal` arm) was measured on candidates in round 4 and is withdrawn; the WSP patch from round 4 was lost with its volume (round 5 saves bit-exact factors). | See `prereg_round5.md` section 0. |

## Limits I could not remove
- D2 is judged by a classifier built for HarmBench behaviours; its labels on StrongREJECT prompts are unvalidated. Replies to harmful prompts are deleted after judging by design, so I cannot hand-check them.
- Heretic tunes under its own default rendering (system prompt "You are a helpful assistant."); the benchmark has none.
- Arditi-paper uses 128 + 32 prompts, the paper's setting; Arditi-matched and the others use 335 + 80.
- OBLITERATUS 0.1.4 refuses this architecture (validated only for one Qwen3.8-27B layout, no opt-in): not run.
