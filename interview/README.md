# `interview/`

**Audience:** someone who wants to know where the pre-registration's questions came from, or to run the
same intake for a different study.

`questions.yaml` is the question set used by `gdkit`'s overfit-clinic. Twenty-two questions in file
order, each with a type, whether it is required in registered mode, and — for the ones that matter — a
`why` line explaining what the answer decides.

The answers were taken one at a time into `.gdkit/project.yaml`, each validated before it was saved, and
the file was re-written after every answer so an interrupted session resumes rather than restarts.

## Why the questions look like this

They force decisions that are easy to defer and expensive to defer:

- `primary_metric` and `kill_criteria` are written before any result exists, and a changed answer is a
  new study.
- `general_capability_margin` has no default, because a margin nobody chose is not a pre-registration.
- `test_access` asks whether anyone looked at the test data before the run — the answer here is *yes*,
  and it says how.
- `uncertainty_method` asks whether the error bar is a standard deviation or a standard error, because
  a proportion on a fixed denominator needs neither: it needs an interval.

## Reusing it

```bash
python -m gdkit.skill_api next --project .gdkit/project.yaml --mode registered
python -m gdkit.skill_api set  --project .gdkit/project.yaml --mode registered --id <qid> --value-file <file>
```

`set` refuses to overwrite an answer already in the file. That is deliberate: answers freeze when a run
starts, and the freeze is the point.
