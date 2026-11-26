# What did the two HarmBench judges receive? — 2026-11-18 UTC

**Finding:** the harness supplies the primary Llama classifier's four-rule standard prompt
(non-byte-exact) to **both** judges. The alternate Mistral checkpoint documents a different
wrapper and rubric. The successful tokenizer smoke proved that the words reached the
classifier input, not that the classifier received its documented instructions.

## Which upstream reference?

| Reference | Standard text invocation | Relation to the harness |
|---|---|---|
| [Pinned Llama card](https://huggingface.co/cais/HarmBench-Llama-2-13b-cls/blob/bda705349d1144fa618770bea64d99ce54e3835b/README.md) and [classifier example](https://github.com/centerforaisafety/HarmBench/blob/8e1604d1171fe8a48d8febecd22f600e462bdcdd/notebooks/run_classifier.ipynb) | Llama system wrapper, `Behavior:` and `Generation:`, four rules. Separate template for contextual inputs. | Local standard literal lacks one space at the end of the first rule. Otherwise identical; 896 versus 897 UTF-8 bytes before substitution. |
| [Pinned Mistral validation card](https://huggingface.co/cais/HarmBench-Mistral-7b-val-cls/blob/51182c7cdaf9b2e5f05b745b81b047b67e7384a1/README.md) | Plain `[INST]` instruction without the Llama system block, `[BEHAVIOR]:` and `[GENERATION]:`, seven rules. Separate contextual and multimodal templates. | The difference is substantive: the card gives explicit criteria for warnings/caveats, imperfect attempts, and language/interpretability. Local code uses none of those three extra rules. |
| [Main evaluator](https://github.com/centerforaisafety/HarmBench/blob/8e1604d1171fe8a48d8febecd22f600e462bdcdd/evaluate_completions.py) and [its helper](https://github.com/centerforaisafety/HarmBench/blob/8e1604d1171fe8a48d8febecd22f600e462bdcdd/eval_utils.py#L309-L350) | Defaults to the Llama checkpoint. Its standard template has the Llama wrapper but bracketed field names and a longer, seven-rule rubric. Routes contextual cases separately. | Not the four-rule Llama card/example. Changing `--cls_path` alone does not select the Mistral card's template. Local helper takes only behavior and generation, with no separate context-template branch. We did not establish which historical items, if any, needed contextual routing. |

The [validation notebook](https://github.com/centerforaisafety/HarmBench/blob/8e1604d1171fe8a48d8febecd22f600e462bdcdd/notebooks/run_classifier_val_set.ipynb)
contains standard literals identical to the respective pinned cards. Its text example selects
`classifier_path = val_classifier_path` for prompt selection, yet constructs `LLM(model=test_classifier_path)`.
It is evidence about the literals, not proof the displayed example ran Mistral or that any one
source reconstructs training. No upstream code was executed and no upstream defect is asserted.

## Inputs, decoding, and invalid outputs

- **Truncation:** the main CLI right-clips the generation alone to 512 judge-tokenizer tokens
  by default, decodes it with special tokens skipped, then formats it. It sets its classifier
  tokenizer to left truncation. The HF example specifies left padding/truncation and uses
  `use_fast=False`; its shown encoding call pads without explicitly enabling truncation.
  Our loader does not request `use_fast=False`. The local helper sets left **padding** but
  right-truncates the **combined** prompt at 2,048 with the observed tokenizer defaults.
  For a long input these policies can preserve different text, including the answer cue;
  this audit did not measure a truncation rate on study data.
- **Prediction:** the examples generate one greedy token (`do_sample=False` or temperature
  zero). Local code takes the unrestricted argmax of the final-position forward-pass logits
  and decodes that token. This is not a yes-versus-no logit comparison. Both approaches aim
  at one token, but equivalence across generation settings, tokenizers and engines was not tested.
- **Parsing:** the main helper accepts exact case-insensitive `yes`/`no` and warns/records
  `-1` otherwise (the validation notebook additionally strips whitespace). Its ASR summary
  counts `label == 1`; recording an invalid output is distinct from declaring it `no`.
  Local code strips, lowercases, and tests `startswith("yes")`. It accepts non-exact yes-prefixes
  as positive; every other string is negative, with no invalid category. Inversion then
  turns that negative into the legacy `refusal` flag. No invalid prediction was observed or
  counted here: this is a difference in code paths, not evidence about their frequency.

## Bounded verification

Compared literals by parsing assignments as data, without executing the downloaded sources.
Checked the model cards against the Git blob IDs in the previously captured commit-pinned
Hub trees and four upstream files against the HarmBench Git tree. The preserved historical
remote helper has the same standard literal and matching function statements (excluding
docstrings) for classification/inversion; the captured runner invokes its patch. Those are
later source captures, not retroactive proof of the code used for every historical item.

One local tokenizer-only fixture, `What color is a ripe lemon?` / `A ripe lemon is yellow.`,
was formatted under each source and encoded with the **same pinned local tokenizer within
each row**. These are template-only comparisons, not emulations of the different engines.

| Tokenizer | Local shared template | Its own card template | Main CLI's Llama template |
|---|---:|---:|---:|
| Llama primary | 234 tokens | 235 | 338 |
| Mistral alternate | 225 tokens | 319 | 328 |

The Llama whitespace difference changes the token IDs for this fixture. Both Mistral strings
likewise produce different IDs. Neither result quantifies an effect on a predicted label.
Command: isolated dependency environment's `python -B -I <private-attempt>/tokens.py`;
Windows CPU, Transformers 5.22.2/tokenizers 0.23.3, HF offline, no network attempts recorded.
**06:27:44.752Z–06:28:04.487Z**, elapsed **19.734 s** for one invocation, no warm-up or
repetitions. No model weights, scoring, historical generations, GPU jobs or Modal calls used.
Private sources, code, literal comparisons, token IDs and consultation records are in
`.omp/judge-invocation-review/20261118T062356002375Z/`.

## Interpretation and next decision

Keep the historical κ = 0.816 as **agreement under the implemented invocation**. Do not
relabel it as accuracy, card-faithful agreement, or evidence that a particular number of
verdicts was wrong. The Mistral mismatch bears directly on the alternate comparison; it
does not by itself explain the primary Llama rate. Score effects could be negligible or
could differ by item, arm or judge. Common formatting between parent and a future candidate
would not guarantee cancellation of error. There is no corrected score from this audit.

**Recommendation, not an amendment:** before changing any gate, specify a named reference
for each judge and task, the context and truncation policies, one-token decoding, and the
handling/reporting of invalid outputs and denominators. For the question “what does each
pinned checkpoint document?”, use its own card as the starting point. A main-CLI reproduction
is a distinct comparison, not interchangeable with card fidelity. Separately define and
human-calibrate an explicit-refusal instrument: a valid `no` is still not proof of refusal.
Only after approval consider a paired comparison on the same preserved responses; the
original per-item safe-prompt outputs remain unavailable in the checked stores. Historical
results and thresholds remain untouched. No new baseline or candidate comparison authorized.
