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

For every Qwen transformer block, the only modified tensors are:

- `model.layers.<i>.self_attn.o_proj.weight`
- `model.layers.<i>.mlp.down_proj.weight`

The implementation rejects missing, noncontiguous, malformed, or dimension-incompatible targets. It
leaves q/k/v projections, MLP up/gate projections, norms, embeddings, and the LM head unchanged.

## 4. Rank and scale

Each target receives one rank-1 update at fixed scale 1.0:

$$W' = W - r(r^T W).$$

There is no layer choice, strength sweep, validation choice, or optimizer.

## 5. Objective

None. This is an analytic projection of the precomputed direction, not an optimization against refusal,
KL, capability, or any other score.

## 6. Reproducibility

The method has no random draws and no seed. Given identical parent checkpoint bytes, direction tensor,
target layout, torch build, and hardware, it performs the same sequence of tensor operations. The
materializer must record the parent revision, direction artifact digest, torch version, CUDA version
when present, and candidate checksum. The module itself writes no files and does not mutate the parent.

## 7. Manifest

`apply()` returns a new state-dictionary mapping plus a manifest with the method and fixed parameter,
direction-tensor digest and shape, and per-target tensor name, layer, shape, direction index, rank,
weight norm, update norm, relative update norm, total elements, and changed elements. Its aggregate
records the number of matrices and elements changed and the combined update norm.

## 8. Compute

**Not yet measured.** The review checklist requires observed GPU-hours and hardware for one run. This
method must not be admitted until a reproducibility run records that measurement. No estimate is being
substituted for evidence.

## 9. Failure behaviour

The implementation fails closed if the direction is not a finite rank-2 array of unit nonzero vectors,
if its vector count or width conflicts with the model, if a required residual writer is absent, or if
the projection would make no representable weight change. It returns no partial candidate.

## Review prerequisites not supplied by this module

- The owner must resolve the candidate-admission cycle before candidate gates can run.
- A reviewed materializer must bind the method source hash, parent revision, direction artifact digest,
  candidate checksum, and manifest to the ledger before endpoint results are read.
- The parent baseline must be measured before any candidate result, as required by the frozen protocol.
