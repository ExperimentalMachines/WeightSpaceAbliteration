# How this repository works, for a reader arriving cold

**Audience:** someone who has cloned the repository, has no context, and wants to know what is already
fixed, what is still open, and where the evidence for each claim lives.

The whole repository exists to make one thing hard: changing your mind after seeing the numbers. The
order below is the order the study actually happened in, and each step wrote something the next step
could not alter.

## 1. The pre-registration

`interview/questions.yaml` holds twenty-two questions. The answers live in `.gdkit/project.yaml` and
were taken one at a time, through a validator, before any corpus was read. The answers are hashed into
the first entry of the run's ledger, and `gdkit` refuses to promote a run whose answers have drifted.

Read this first. Every later decision is downstream of it, including decisions you may disagree with:
the endpoint of 12 refusals in 313 behaviours, the 10% over-refusal ceiling, the 2-point capability
margin, the voice in which the study is written.

- [`.gdkit/project.yaml`](../.gdkit/project.yaml)
- [`interview/questions.yaml`](../interview/questions.yaml)

## 2. The literature basis

Fourteen Papers With Code lookups — six searches, eight paper records — are in the ledger with the
request hash, the response hash, the `pwc` version, and the raw JSON on disk. The adopted basis covers
the refusal direction, its multi-directional counter-argument, shallow safety alignment, probe
null-controls, harmful-text handling, judge-noise correction and statistical power.

- [`runs/<run_id>/paper_lookups/`](../runs/)
- [`datasets/inventory/`](../datasets/inventory/) for the dataset side of the same question

## 3. The split

[`harness/build_splits.py`](../harness/build_splits.py) fetches the pinned corpora, applies the
exclusions the pre-registration names, and writes one JSONL per arm plus a manifest with a sha256 for
every file and for the exclusion list.

The exclusion rule is the part worth reading: an item is dropped when its embedding cosine to the
derivation or endpoint corpora is at least 0.80. That is a semantic rule, not a string rule, and it
removes paraphrases that exact matching cannot see.

- [`runs/<run_id>/splits/manifest.json`](../runs/)
- Method and rationale: [`datasets/README.md`](../datasets/README.md)

## 4. The gates

[`harness/gates.py`](../harness/gates.py) defines eleven gates. Three are cheap and re-run at promotion
time. Eight involve inference or judging and need a signed attestation.

Each gate hashes its own source. Change a gate and the hash changes, which invalidates every receipt it
produced — that is the mechanism, not an inconvenience.

- [`harness/README.md`](../harness/README.md)

## 5. The method

Deliberately empty. [`harness/methods/base.py`](../harness/methods/base.py) defines what a weight-space
edit must declare and return, and `load_method()` refuses all three reserved names. A method becomes
*the* method by review and one ledger entry.

- [`harness/methods/README.md`](../harness/methods/README.md) — the review checklist
`require_admitted()` refuses to evaluate a candidate until the ledger names an admitted method, so an
unreviewed edit cannot become a number by accident.

## 6. Results

None yet. When there are, they will appear as gate receipts and a results directory inside the run,
and the README's status table will say so instead of saying "no result".

## Reading the ledger

```bash
python -c "from gdkit.ledger import verify; print(verify('runs/<run_id>/ledger.jsonl'))"
```

Entry 0 is the pre-registration. Entries 1–14 are paper lookups. Entry 15 is the split build, including
its deviations and their causes. Anything later is a gate receipt or a method selection, and each one
names what it read.
