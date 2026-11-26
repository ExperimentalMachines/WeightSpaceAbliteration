# Abliteration method review

**Status: review-only. Not admitted, not frozen, and not evaluated.** `load_method()` remains closed;
merging this document or its implementation does not authorize a candidate run.

## 1. Provenance

This implements the single-direction refusal ablation in Arditi et al., *Refusal in Language Models Is
Mediated by a Single Direction*, arXiv:2406.11717. It does not reproduce later multi-direction, search,
or optimization variants.

**Declared differences from the paper.** The paper's §4.1 orthogonalizes "the embedding matrix, the
positional embedding matrix, attention out matrices, and MLP out matrices … as well as any output
biases" against one direction $\hat{\mathbf r}$. This method differs in two ways, both stated here so it
is not read as a bit-exact reproduction:

1. **Layer-wise direction.** The paper uses one direction for every matrix. This study consumes the
   `direction_derivation` gate's per-layer difference-in-means vectors unchanged — one unit vector per
   residual-stream boundary, index 0 at the embedding output — and applies vector $i+1$ to block $i$'s
   writers. The paper's equivalence between inference-time ablation and weight orthogonalization is
   argued for a single global direction; making the direction layer-specific is a generalization of the
   rule, not a restatement of the paper.
2. **Writers left unchanged.** The embedding matrix, the positional embedding matrix, and all biases,
   including attention and MLP output biases, are not edited. The direction at index 0 corresponds to
   the embedding output, so orthogonalizing the embedding matrix with it would be the consistent
   extension; it is omitted here because the pilot's edits and this module's target list exclude it.
   Adding it is a different candidate with a different manifest, and must be declared as one. The
   `tensor_inventory` entry records, for each of the three, whether the checkpoint actually contains
   the tensor and whether the word embeddings are tied, so "absent" and "deliberately skipped" stay
   distinguishable in the evidence.

The consequence is the method reviewed here: **single-direction refusal ablation applied layer-wise to
the output projection of every residual-writing block writer — the mixer's output projection and the
MLP's output projection — with embedding, positional and bias writers excluded.** The target rule is
functional ("the matrix that writes this block's mixer or MLP output into the residual stream") rather
than architectural, so it covers softmax attention and gated linear attention under the same rule. It
fails closed on any model whose blocks it cannot enumerate.

## 2. Direction contract

The method consumes the `direction` array from `direction_derivation` unchanged. It validates the
per-layer unit vectors but does not recalculate activations, renormalize a vector, filter prompts, or
use any endpoint behaviour. Direction index zero is the embedding output; transformer block `i` uses
index `i + 1`.

## 3. Targets

In every block the modified tensors are the attention output projection and the MLP output projection:

| Family | Tensor name | Notes |
|---|---|---|
| Attention (full) | `model.layers.<i>.self_attn.o_proj.weight` | one attention writer is required in every block |
| Attention (linear) | `model.layers.<i>.linear_attn.out_proj.weight` | the equivalent output projection in linear-attention blocks (Qwen3.5 hybrid layers); a block has this **or** `self_attn.o_proj`, never both |
| MLP, dense | `model.layers.<i>.mlp.down_proj.weight` | |
| MLP, one module per expert | `model.layers.<i>.mlp.experts.<E>.down_proj.weight` | one rank-1 update per expert; indices must be contiguous from 0 |
| MLP, fused experts | `model.layers.<i>.mlp.experts.down_proj` (3-D, `[experts, hidden, in]`) | one rank-1 update per expert slice |

A block must have exactly one attention writer and exactly one MLP family; blocks of one model may differ (full and
linear attention, dense and expert MLPs). Routers
(`mlp.gate`), q/k/v projections, MLP up/gate projections, norms, embeddings and the LM head are unchanged.
The implementation rejects missing, noncontiguous, mixed, malformed, or dimension-incompatible targets.

**Known gaps (the method fails closed on these; it does not skip them):**
- **Linear-attention output projections are in scope.** Decided 2026-11-24, with the consultation and
  source checks in `docs/protocol/consultation_20261124/`. `linear_attn.out_proj` is the mixer output
  projection in the 18 gated linear-attention blocks of Qwen3.5-0.8B; it replaces `self_attn.o_proj`
  rather than adding a second writer, so including it keeps the six registered architectures under one
  rule instead of dropping a registered model. Excluding it made the module fail closed on that model.
  The tensor name and shape (`[1024, 2048]`) were read from Qwen3.5-0.8B @ `2fc06364` as loaded in the
  pilot; the pinned-toolchain re-read belongs to the `tensor_inventory` entry.
  A reviewer should note the risk this carries: recurrent state in linear-attention blocks may respond
  more strongly to a rank-1 projection than softmax attention does, so per-model edited-parameter
  fractions are reported with the candidate's results.
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

**Code-enforced:** `require_compute_evidence` in `harness/preflight.py` refuses method admission
until a `compute_evidence` ledger entry exists. See `docs/PROVENANCE.md` § Compute evidence.

## 9. Failure behaviour

The implementation fails closed if the direction is not a finite rank-2 array of unit nonzero vectors,
if its vector count or width conflicts with the model, if `scale` is not a finite number in (0, 1], if a
required residual writer is absent, if a block mixes MLP families or has gaps in its expert indices, or if
the projection would make no representable weight change. It returns no partial candidate.

## 10. Tensor inventory

**Not yet recorded.** The expert layouts in §3 are tested on synthetic state dictionaries only. The
actual state-dict key names for each registered model (Qwen3.5-0.8B, Qwen3-30B-A3B, and the other
three named in the pre-registration) must be dumped from the pinned `transformers` version and
recorded as a `tensor_inventory` ledger entry before admission.

`scripts/record_tensor_inventory.py --run runs/<id>` produces that entry: the resolved target names,
shapes and dtypes, the per-kind counts, the edited and total parameter counts with the edited
fraction, the tied-embedding flag, and a census of the three excluded writers (embedding, positional,
biases) with their actual shapes. It fails rather than recording a partial target set, a block count
that disagrees with the model's declared layers, or a second inventory for the same run.

**Code-enforced:** `require_tensor_inventory` in `harness/preflight.py` refuses method admission
until this entry exists. See `docs/PROVENANCE.md` § Tensor inventory.

## Review prerequisites not supplied by this module

- The owner must resolve the candidate-admission cycle before candidate gates can run.
- A reviewed materializer must bind the method source hash, parent revision, direction artifact digest,
  candidate checksum, and manifest to the ledger before endpoint results are read.
- The parent baseline must be measured before any candidate result, as required by the frozen protocol.
- Compute evidence and tensor inventory must be recorded before admission (now code-enforced; see
  `docs/PROVENANCE.md`).
- Any blocking upstream issues must have a recorded workaround (see `docs/upstream_issues/README.md`).
