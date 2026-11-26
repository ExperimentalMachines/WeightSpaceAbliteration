# Consultation 2026-11-24 — method definition and capability seeds

Requested model `gemini-4-neon-high` via `agy` 1.5.16, exit 0, 136 s. Verbatim prompt,
stdout and stderr are beside this file with hashes in `metadata.json`. The answer is a
judgment-bearing recommendation, not evidence. Claims below were checked against primary
sources before being accepted.

## What Neon recommended

- **Q1 (linear-attention output projections): Option C** — include `linear_attn.out_proj`
  and declare the method's scope as "every token-mixer and MLP residual-writing
  projection, fail-closed on unlisted architectures". Reason: `out_proj` *replaces*
  `self_attn.o_proj` in those blocks rather than adding matrices, so including it keeps
  the six registered models comparable; excluding it would drop a registered model.
  Residual risk: recurrent state dynamics in linear-attention blocks may react more
  strongly to a rank-1 projection, inflating capability loss. Suggested reporting the
  edited-parameter fraction per model.
- **Q2 (capability seeds): Option B** — fix the gate to pass a seed per run and execute
  all three, with a deviation entry. Fallback C (one seed, deviation) only if GPU cost is
  prohibitive. Rejected A (three identical runs) and D (data-dependent optional stopping).

## Checks performed here

| Claim | Result |
|---|---|
| Arditi et al. target set includes embeddings and biases | **Confirmed** (arXiv:2406.11717 §4.1: "the embedding matrix, the positional embedding matrix, attention out matrices, and MLP out matrices ... as well as any output biases") |
| `linear_attn.out_proj` substitutes for `self_attn.o_proj` | Consistent with the method document; **not re-verified** against a fresh load of the pinned checkpoint |
| Gated Delta Networks = arXiv:2412.06464 | **Confirmed** (Yang, Kautz, Hatamizadeh, ICLR 2025) |
| Quantifying Variance in Evaluation Benchmarks = arXiv:2406.10229 | **Confirmed** title/authors; the specific "1.5–2.0 pt few-shot" figure **not verified** |
| lm_eval `--seed` arity and default | **Confirmed** on pinned `d6de8164`: one integer or 3–4 slots; default `0,1234,1234,1234`; slot 4 is the few-shot seed |
| Seed changes few-shot exemplars | **Confirmed** in pinned source: `set_fewshot_seed` → `task.fewshot_rnd` → `fewshot_examples(k, rnd)` |
| Current gate passes a seed | **Confirmed absent**: the command in `check_capability_suite` passes no `--seed`, so declared seeds 0–2 would be byte-identical runs |

## Consequence not raised by Neon

The paper's rule is wider than this study's implementation: it also orthogonalizes the
embedding matrix, positional embeddings and output biases. `harness/methods/abliteration.md`
§1 presents the method as an implementation of that paper while §3 keeps norm/embedding
parameters unchanged. That narrowing must be declared in the method document, or the
target set widened. Adopting "every residual-writing matrix" as the rule without
reconciling embeddings and biases would leave the rule applied inconsistently.

Status: both recommendations adopted on 2026-11-24, with the corrections below. The method document
declares the scope and the two differences from the paper; the capability gate passes one seed per
registered seed and the change is recorded as a deviation in both ledgers. No GPU work, no method
entry, no pre-registration change.

Correction to the consultation: Neon's Q1 answer is right about the *reason* to declare scope, but it
did not notice that the paper edits embeddings, positional embeddings and biases as well. Declaring
"every residual-writing matrix" while still skipping those three would apply the rule inconsistently.
The method document therefore names the omission explicitly rather than presenting the target set as
the paper's.
