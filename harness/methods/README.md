# Method review — what has to be true before a method is frozen

The pre-registration in `.gdkit/project.yaml` is frozen and must not change. The **method is not**.
It is deliberately unimplemented: `harness/methods/base.py` defines the contract and `load_method()`
refuses every name, so nothing can quietly become "the method" by being merged.

A method becomes the method by a ledger entry. Until that entry exists, the study has no candidates
and no results.

## What is already fixed and cannot be renegotiated by the method

- The split, its exclusions and their hashes (`runs/<id>/splits/manifest.json`).
- The direction's source: the `direction_derivation` gate, computed on `derivation.jsonl`.
- The endpoints: `primary` (313) and `large` (16,612), and the decision rules in the pre-registration.
- The judges and their revisions.
- The capability suite and the margin.

A method may change weights. It may not change what is measured.

## Checklist for the reviewer

Answer each of these in the method's own document, not in conversation.

1. **Provenance.** Which published method does it reproduce? Give an arXiv id, or state plainly that
   it is novel and what it is novel relative to. An empty `basis` field is an assertion, not a gap.
2. **Direction contract.** Does it consume the `direction_derivation` output unchanged, or does it
   derive its own? If its own, that is a different method and needs its own gate.
3. **Targets.** Which tensors does it modify — every attention `o_proj`/`v_proj`, every MLP
   `down_proj`, norms, embeddings? List them. A method that touches "whatever looks right" cannot be
   reviewed.
4. **Rank and scale.** Is the edit rank-1 per tensor, or higher? What is the scale, and how was it
   chosen — fixed, searched, or optimised against an objective?
5. **Objective.** If it optimises, against what? A refusal count, a KL penalty, both? State the
   weights. An optimiser tuned on the evaluation set is disqualified by the split protocol.
6. **Reproducibility.** Same inputs, same checkpoint hash? Determinism must be stated, including
   seeds and any nondeterministic kernels.
7. **Manifest.** Does `apply()` return what changed — tensor names, edit magnitude, rank? The ledger
   entry records this; without it the method's effect is unverifiable.
8. **Compute.** What does one run cost in GPU-hours, and on what hardware? **Code-enforced:**
   `require_compute_evidence` refuses admission until a `compute_evidence` ledger entry exists
   recording GPU model, wall-clock seconds, and peak memory for one `apply()` call.
9. **Failure behaviour.** What does it do when the direction is near-zero or the layer is missing?
10. **Tensor inventory.** Have the target tensor names been verified against the actual state-dict
    keys of every registered model, loaded by the pinned `transformers` version? **Code-enforced:**
    `require_tensor_inventory` refuses admission until a `tensor_inventory` ledger entry exists.

## What the reviewer runs before saying yes

```
python -m harness.gates --run runs/<id> --gate direction_derivation
python -m harness.gates --run runs/<id> --gate refusal_eval      # parent first, then candidate
python -m harness.gates --run runs/<id> --gate probe_train
python -m harness.gates --run runs/<id> --gate capability_suite
python -m harness.gates --run runs/<id> --gate kl_divergence
```

The parent is measured first and its numbers recorded. A candidate that cannot be compared to a
measured parent is not a result.

## How it gets frozen

One ledger entry, `method_selected`, written when the reviewer signs off. It records:

- the method name and its `MethodSpec`,
- the sha256 of the method's source file, so the code that ran is identifiable,
- the receipt hashes of the gates that produced the candidate's numbers,
- the reviewer's name.

After that entry, changing the method means a new run. The same rule that froze the answers freezes
the method: not because it cannot be improved, but because a study whose method moved underneath its
results is not a study.

## Admission is enforced, not promised

`require_admitted()` in `harness/gates.py` refuses to evaluate a candidate unless the run's ledger
contains a `method_selected` entry. It fires only when `harness.json` sets `"stage": "candidate"`; the
parent baseline is exempt, because the parent is measured before any method exists.

Before admission, `require_admitted` also checks two code-enforced prerequisites:

1. **`compute_evidence`** — a ledger entry recording observed GPU-hours, peak memory, and hardware
   for one `apply()` call on the registered model. An estimate is not a measurement.
2. **`tensor_inventory`** — a ledger entry recording the state-dict key names, shapes, and dtypes
   of every target tensor, as loaded by the pinned `transformers` on the pinned model revision.

Both are enforced by `harness/preflight.py` checks called from within `require_admitted`.
See [`docs/PROVENANCE.md`](../../docs/PROVENANCE.md) § Method admission prerequisites.

## Status

| slot | implemented | reviewed | compute evidence | tensor inventory | frozen |
|---|---|---|---|---|---|
| `abliteration` | **yes** (review-only) | in progress | **not recorded** | **not recorded** | no |
| `heretic_style` | no | no | — | — | no |
| `obliteratus_style` | no | no | — | — | no |
