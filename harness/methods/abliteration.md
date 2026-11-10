# Abliteration method review

**Status: review-only. Not admitted, not frozen, and not evaluated.** `load_method()` remains closed;
merging this document or its implementation does not authorize a candidate run.

## 1. Provenance

This implements the single-direction refusal ablation in Arditi et al., *Refusal in Language Models Is
Mediated by a Single Direction*, arXiv:2406.11717. It does not reproduce later multi-direction, search,
or optimization variants.

## 2. Direction contract

The method consumes the `direction` array from `direction_derivation` unchanged. It validates the
per-layer unit vectors but does not recalculate activations, renormalize a vector, filter prompts, or
use any endpoint behaviour. Direction index zero is the embedding output; transformer block `i` uses
index `i + 1`.

## 3. Targets

In every block the modified tensors are the attention output projection and the MLP output projection:

| Family | Tensor name | Notes |
|---|---|---|
| Attention | `model.layers.<i>.self_attn.o_proj.weight` | required in every block |
| MLP, dense | `model.layers.<i>.mlp.down_proj.weight` | |
| MLP, one module per expert | `model.layers.<i>.mlp.experts.<E>.down_proj.weight` | one rank-1 update per expert; indices must be contiguous from 0 |
| MLP, fused experts | `model.layers.<i>.mlp.experts.down_proj` (3-D, `[experts, hidden, in]`) | one rank-1 update per expert slice |

A block must have exactly one MLP family; blocks of one model may differ (some dense, some expert). Routers
(`mlp.gate`), q/k/v projections, MLP up/gate projections, norms, embeddings and the LM head are unchanged.
The implementation rejects missing, noncontiguous, mixed, malformed, or dimension-incompatible targets.

**Known gaps (the method fails closed on these; it does not skip them):**
- **Linear-attention blocks.** Qwen3.5's linear-attention layers have `linear_attn.out_proj` and no `self_attn.o_proj`, so this module raises on Qwen3.5-0.8B (registered after this module was written). Covering it is a definition question for the owner (the pilot's own edits included `linear_attn.out_proj`).
- **Expert layouts are tested on toy tensors only.** The two layouts above are exercised with synthetic state dictionaries. They have **not** been checked against the pinned `Qwen/Qwen3-30B-A3B` checkpoint as loaded by the pinned `transformers`, whose state-dict names may differ by version. A reviewer should list the actual tensor names for each registered model before admission.
- Gemma-4-E2B and MiniCPM5 layouts have not been inspected.

## 4. Rank and scale

Each target receives one rank-1 update (per matrix, or per expert slice for a fused tensor):

$$W' = W - s\, r(r^T W).$$

`s` is the constructor parameter `scale`, default and study value **1.0**. It is a real parameter: values must be
finite and in (0, 1]; anything else raises, and the manifest records the value actually used. A different
value is a different candidate and must be declared as one. There is no layer choice, strength sweep,
validation choice, or optimizer. (An earlier version declared `scale` in the spec but never used it, so it was
byte-identical at 0.0 and 1.0; fixed, with regression tests.)

## 5. Objective

None. This is an analytic projection of the precomputed direction, not an optimization against refusal,
KL, capability, or any other score.

## 6. Reproducibility

The method has no random draws and no seed. Given identical parent checkpoint bytes, direction tensor,
target layout, `scale`, torch build, and hardware, it performs the same sequence of tensor operations. The
materializer must record the parent revision, direction artifact digest, torch version, CUDA version
when present, and candidate checksum. The module itself writes no files and does not mutate the parent.

## 7. Manifest

`apply()` returns a new state-dictionary mapping plus a manifest with the method and the `scale` used,
direction-tensor digest and shape, and per-target tensor name, layer, kind, expert index (null unless a
per-expert tensor), shape, direction index, rank, weight norm, update norm, relative update norm, total
elements, and changed elements. Its aggregate records the number of matrices and elements changed, the
combined update norm and the target kinds touched.

## 8. Compute

**Not yet measured.** The review checklist requires observed GPU-hours and hardware for one run. This
module has not been run on any real model; the timings from the Qwen3.5-0.8B pilot belong to different code
and are not evidence for it. This method must not be admitted until a reproducibility run records the
measurement. No estimate is being substituted for evidence.

## 9. Failure behaviour

The implementation fails closed if the direction is not a finite rank-2 array of unit nonzero vectors,
if its vector count or width conflicts with the model, if `scale` is not a finite number in (0, 1], if a
required residual writer is absent, if a block mixes MLP families or has gaps in its expert indices, or if
the projection would make no representable weight change. It returns no partial candidate.

## Review prerequisites not supplied by this module

- The owner must resolve the candidate-admission cycle before candidate gates can run.
- A reviewed materializer must bind the method source hash, parent revision, direction artifact digest,
  candidate checksum, and manifest to the ledger before endpoint results are read.
- The parent baseline must be measured before any candidate result, as required by the frozen protocol.
