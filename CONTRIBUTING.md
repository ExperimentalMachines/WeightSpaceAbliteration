# Contributing

This repository is a pre-registered study. Two things follow from that, and they shape everything else.

## The pre-registration does not change

`.gdkit/project.yaml` is frozen. Its digest is the first entry of the run's ledger. A change to it is
not a contribution, it is a new run, and a new run starts a new ledger.

If you believe an answer is wrong — the endpoint, the margin, the judges, the uncertainty method — say
so in an issue, with the evidence. The correct outcome is a documented deviation or a successor study,
both of which are more useful than a quiet edit.

## The method is open until it is admitted

`harness/methods/base.py` defines what a weight-space edit must declare. Nothing is implemented.
`load_method()` refuses all three reserved names.

To propose a method:

1. Implement it against the contract: `MethodSpec` plus `apply(model, direction) -> (state_dict, manifest)`.
2. Answer every question in [`harness/methods/README.md`](harness/methods/README.md), in writing.
3. Run it against the frozen split. Report the gate receipts, not a summary.
4. The owner decides. Admission is one ledger entry, `method_selected`, recording the method name, the
   sha256 of its source, the receipt hashes and the reviewer.

Until that entry exists, the study has no candidates and no results.

## What not to send

- **Corpora or splits.** `datasets/_cache/` and `runs/*/splits/*.jsonl` are ignored on purpose. A pull
  request containing harmful prompt text will be closed.
- **Notebook output with generated responses.** Same reason.
- **A method that tunes on the evaluation arm.** The split protocol disqualifies it; the gates will not
  catch it, a reviewer will.

## Style

- Comments explain why, not what.
- No emoji in code, commits or documentation.
- One logical change per commit, with the reason in the message.
- New claims need a number attached to them and a pointer to where it came from.
