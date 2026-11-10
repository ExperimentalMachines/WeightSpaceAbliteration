# Round 5 results (development pilot; preregistered in notes/prereg_round5.md)

### D2 (primary): StrongREJECT minus near-duplicates of derivation / HarmBench val / HarmBench test

| Condition | Harmful completions (95% Wilson CI) | Invalid labels | Flips vs parent (to harmful / to safe) | Exact McNemar p | Holm-adjusted p |
|---|---|---|---|---|---|
| parent | 51/267 = 19.1% (14.8%-24.2%) | 0 | - | - | - |
| arditi_paper | 218/267 = 81.6% (76.6%-85.8%) | 0 | 172 / 5 | 1.47e-44 | 5.88e-44 |
| arditi_matched | 194/267 = 72.7% (67.0%-77.7%) | 0 | 156 / 13 | 2.67e-32 | 2.67e-32 |
| heretic_abl | 217/267 = 81.3% (76.2%-85.5%) | 0 | 172 / 6 | 2.19e-43 | 6.58e-43 |
| wsp | 204/267 = 76.4% (71.0%-81.1%) | 0 | 156 / 3 | 1.83e-42 | 3.67e-42 |

### D1 (replication): HarmBench validation, standard + contextual

| Condition | Harmful completions (95% Wilson CI) | Invalid labels | Flips vs parent (to harmful / to safe) | Exact McNemar p | Holm-adjusted p |
|---|---|---|---|---|---|
| parent | 20/60 = 33.3% (22.7%-45.9%) | 0 | - | - | - |
| arditi_paper | 41/60 = 68.3% (55.8%-78.7%) | 0 | 27 / 6 | 0.000324 | 0.000324 |
| arditi_matched | 43/60 = 71.7% (59.2%-81.5%) | 0 | 27 / 4 | 3.4e-05 | 6.79e-05 |
| heretic_abl | 43/60 = 71.7% (59.2%-81.5%) | 0 | 26 / 3 | 1.52e-05 | 4.57e-05 |
| wsp | 44/60 = 73.3% (61.0%-82.9%) | 0 | 26 / 2 | 3.03e-06 | 1.21e-05 |

### Pooled D1 + D2 (secondary)

| Condition | Harmful completions (95% Wilson CI) | Flips vs parent (to harmful / to safe) | Exact McNemar p |
|---|---|---|---|
| parent | 71/327 = 21.7% (17.6%-26.5%) | - | - |
| arditi_paper | 259/327 = 79.2% (74.5%-83.3%) | 199 / 11 | 8.64e-46 |
| arditi_matched | 237/327 = 72.5% (67.4%-77.0%) | 183 / 17 | 2.51e-36 |
| heretic_abl | 260/327 = 79.5% (74.8%-83.5%) | 198 / 9 | 1.64e-47 |
| wsp | 248/327 = 75.8% (70.9%-80.2%) | 182 / 5 | 1.89e-47 |

Pairwise, sr_dev (exploratory; cells: row harmful & column safe / row safe & column harmful, exact McNemar p):

| | arditi_matched | heretic_abl | wsp |
|---|---|---|---|
| arditi_paper | 44 / 20, p = 0.00369 | 23 / 22, p = 1 | 34 / 20, p = 0.0759 |
| arditi_matched |  | 22 / 45, p = 0.00674 | 28 / 38, p = 0.268 |
| heretic_abl |  |  | 30 / 17, p = 0.0789 |

Pairwise, val_eval (exploratory; cells: row harmful & column safe / row safe & column harmful, exact McNemar p):

| | arditi_matched | heretic_abl | wsp |
|---|---|---|---|
| arditi_paper | 6 / 8, p = 0.791 | 7 / 9, p = 0.804 | 4 / 7, p = 0.549 |
| arditi_matched |  | 8 / 8, p = 1 | 6 / 7, p = 1 |
| heretic_abl |  |  | 5 / 6, p = 1 |

### Side metrics (never used to rank)

| Condition | Benign over-refusal (treadon, 83, string match) | GSM8K train 500 | First-token KL vs parent | Elements changed (% of 752,393,024 unique parameters) | Judge tokenizer sensitivity on D1 (labels that differ) |
|---|---|---|---|---|---|
| parent | 4/83 | 39.4% | 0.000 | - | 0 |
| arditi_paper | 0/83 | 36.4% | 0.066 | 326,697,554 (43.42%) | 0 |
| arditi_matched | 0/83 | 36.4% | 0.074 | 327,444,013 (43.52%) | 0 |
| heretic_abl | 0/83 | 37.6% | 0.029 | 74,383,917 (9.89%) | 1 |
| wsp | 0/83 | 37.2% | 0.028 | 48,035,590 (6.38%) | 0 |

