"""check_probe_train must choose its layer without looking at the held-out categories.

The earlier version chose the layer with the highest held-out-category AUC and reported that same AUC, so the
held-out categories selected the layer and the reported number was the maximum of many noisy estimates. These tests
use synthetic activations where the in-distribution signal is strongest at layer 1 and the held-out positives
separate best at layer 3: a correct selection picks layer 1, and changing only the held-out arm cannot move it.
"""

from __future__ import annotations

import numpy as np
import pytest

torch = pytest.importorskip("torch")

from harness.gates import (  # noqa: E402
    PROBE_BOOTSTRAP,
    PROBE_PERMUTATIONS,
    PROBE_RANDOM_DIRECTIONS,
    PROBE_VALIDATION_FRACTION,
    probe_report,
)

LAYERS, DIM = 4, 6
SEEDS = [0, 1]
FAST = 20  # shuffles in tests that do not check the permutation count


def _arms(held_layer: int = 3, held_strength: float = 4.0):
    rng = np.random.default_rng(123)
    pos = rng.normal(size=(60, LAYERS, DIM)).astype(np.float32)
    neg = rng.normal(size=(60, LAYERS, DIM)).astype(np.float32)
    held = rng.normal(size=(30, LAYERS, DIM)).astype(np.float32)
    pos[:, 1, 0] += 3.0  # strong in-distribution signal at layer 1
    pos[:, 3, 0] += 0.4  # weak in-distribution signal at layer 3
    held[:, held_layer, 0] += held_strength  # held-out positives separate best at held_layer
    return pos, neg, held


def test_the_layer_is_chosen_on_validation_not_on_the_held_out_categories():
    report = probe_report(*_arms(), seeds=SEEDS, train_fraction=0.8, permutations=FAST, bootstrap=FAST)
    assert report["layer_selection"]["chosen_layer"] == 1
    per_layer = report["per_layer_descriptive"]
    holdout_by_layer = {int(k): v["category_holdout_mean"] for k, v in per_layer.items()}
    assert max(holdout_by_layer, key=holdout_by_layer.get) == 3  # what the old code would have picked
    chosen = report["at_chosen_layer"]
    assert chosen["category_holdout_auc_mean"] == holdout_by_layer[1]
    assert chosen["category_holdout_auc_mean"] < max(holdout_by_layer.values())


def test_changing_only_the_held_out_arm_cannot_move_the_chosen_layer():
    first = probe_report(*_arms(held_layer=3), seeds=SEEDS, train_fraction=0.8, permutations=FAST, bootstrap=FAST)
    second = probe_report(*_arms(held_layer=2, held_strength=8.0), seeds=SEEDS, train_fraction=0.8, permutations=FAST, bootstrap=FAST)
    assert first["layer_selection"] == second["layer_selection"]
    for key in ("validation_mean", "in_distribution_mean"):
        assert [v[key] for v in first["per_layer_descriptive"].values()] == \
               [v[key] for v in second["per_layer_descriptive"].values()]


def test_validation_test_and_fit_items_do_not_overlap():
    report = probe_report(*_arms(), seeds=SEEDS, train_fraction=0.8, permutations=FAST, bootstrap=FAST)
    sizes = report["split_sizes"]
    assert sizes["pos"]["fit"] + sizes["pos"]["validation"] + sizes["pos"]["test"] == 60
    assert sizes["neg"]["fit"] + sizes["neg"]["validation"] + sizes["neg"]["evaluation_pool"] == 60
    assert sizes["neg"]["evaluation_pool"] == round(60 * 0.2)
    assert sizes["pos"]["validation"] == int(int(60 * 0.8) * PROBE_VALIDATION_FRACTION)


def test_when_every_layer_reaches_validation_auc_1_log_loss_chooses_and_the_ties_are_counted():
    pos, neg, held = _arms()
    for layer in range(LAYERS):
        pos[:, layer, 0] += 6.0  # every layer separates perfectly
    report = probe_report(pos, neg, held, seeds=SEEDS, train_fraction=0.8, permutations=FAST, bootstrap=FAST)
    selection = report["layer_selection"]
    assert [v["validation_mean"] for v in report["per_layer_descriptive"].values()] == [1.0] * LAYERS
    assert selection["layers_tied_at_top_validation_auc"] == LAYERS
    losses = [v["validation_log_loss_mean"] for v in report["per_layer_descriptive"].values()]
    # Every layer ties at AUC 1.0, so log-loss decides among them.
    assert selection["chosen_layer"] == losses.index(min(losses))
    assert "log-loss" in selection["rule"] and "tied exactly" in selection["rule"]


def test_an_exact_log_loss_tie_goes_to_the_lowest_layer():
    pos, neg, held = _arms()
    for array in (pos, neg, held):
        array[:, :, :] = array[:, :1, :]  # every layer identical, so every loss is identical
    report = probe_report(pos, neg, held, seeds=SEEDS, train_fraction=0.8, permutations=FAST, bootstrap=FAST)
    assert report["layer_selection"]["chosen_layer"] == 0


def test_baselines_are_reported_near_chance_and_do_not_shift_the_splits():
    pos, neg, held = _arms()
    report = probe_report(pos, neg, held, seeds=SEEDS, train_fraction=0.8)  # default counts
    baselines = report["baselines_at_chosen_layer"]
    permutation = baselines["permutation_category_holdout_auc"]
    assert permutation["n"] == PROBE_PERMUTATIONS == 1000
    assert permutation["tests"].startswith("held-out AUC above chance only")
    random = baselines["random_direction_category_holdout_auc_folded"]
    assert random["n"] == PROBE_RANDOM_DIRECTIONS == 1000
    assert 0.5 <= random["median"] <= random["q95"] <= random["q975"] <= random["q99"] <= 1.0
    assert report["at_chosen_layer"]["category_holdout_auc_ci95"]["resamples"] == PROBE_BOOTSTRAP == 2000
    assert 0.0 <= permutation["mean"] <= 1.0
    # The baselines use their own random stream: the real numbers match a run with fewer shuffles.
    again = probe_report(pos, neg, held, seeds=SEEDS, train_fraction=0.8, permutations=FAST, bootstrap=FAST)
    for key in ("in_distribution_auc_mean", "category_holdout_auc_mean"):
        assert again["at_chosen_layer"][key] == report["at_chosen_layer"][key]
    assert report["threshold_auc"] == 0.60 and "best_layer_by_holdout" not in report


def test_the_bootstrap_interval_contains_the_estimate_and_narrows_with_more_prompts():
    pos, neg, held = _arms()
    held[:, 1, 0] += 1.0  # a partial signal, so the AUC is not pinned at 0 or 1

    def width(n_held):
        report = probe_report(pos, neg, held[:n_held], seeds=SEEDS, train_fraction=0.8, permutations=FAST,
                              bootstrap=400)
        chosen = report["at_chosen_layer"]
        ci = chosen["category_holdout_auc_ci95"]
        assert ci["low"] <= chosen["category_holdout_auc_mean"] <= ci["high"]
        return ci["high"] - ci["low"]

    assert width(30) < width(8)


def test_the_bootstrap_interval_is_reproducible():
    pos, neg, held = _arms()
    first = probe_report(pos, neg, held, seeds=SEEDS, train_fraction=0.8, permutations=FAST, bootstrap=200)
    second = probe_report(pos, neg, held, seeds=SEEDS, train_fraction=0.8, permutations=FAST, bootstrap=200)
    assert first["at_chosen_layer"]["category_holdout_auc_ci95"] == second["at_chosen_layer"]["category_holdout_auc_ci95"]


# --- the AUC itself ------------------------------------------------------------------------------


def test_auc_is_one_for_a_perfect_ranking_and_zero_for_a_reversed_one():
    from harness.gates import _auc

    labels = torch.tensor([1, 1, 0, 0])
    assert _auc(torch.tensor([3.0, 2.0, 1.0, 0.0]), labels) == 1.0
    assert _auc(torch.tensor([0.0, 1.0, 2.0, 3.0]), labels) == 0.0


def test_auc_matches_a_brute_force_pairwise_count():
    from harness.gates import _auc

    rng = np.random.default_rng(5)
    for _ in range(20):
        scores = rng.normal(size=30)
        labels = rng.integers(0, 2, size=30)
        if labels.min() == labels.max():
            continue
        pos, neg = scores[labels == 1], scores[labels == 0]
        expected = sum(float(p > n) for p in pos for n in neg) / (len(pos) * len(neg))
        assert abs(_auc(torch.tensor(scores), torch.tensor(labels)) - expected) < 1e-6



def test_the_permutation_count_does_not_depend_on_the_number_of_seeds():
    pos, neg, held = _arms()
    for seeds in ([0], [0, 1, 2]):
        report = probe_report(pos, neg, held, seeds=seeds, train_fraction=0.8, permutations=30, bootstrap=FAST)
        assert report["baselines_at_chosen_layer"]["permutation_category_holdout_auc"]["n"] == 30


def test_the_p_value_is_small_for_a_real_signal_and_not_for_none():
    pos, neg, held = _arms()
    held[:, 1, 0] += 3.0  # held-out positives carry the training signal at the chosen layer
    strong = probe_report(pos, neg, held, seeds=SEEDS, train_fraction=0.8, permutations=99, bootstrap=FAST)
    assert strong["layer_selection"]["chosen_layer"] == 1
    assert strong["baselines_at_chosen_layer"]["permutation_category_holdout_auc"]["p_value_upper"] == 1 / 100

    rng = np.random.default_rng(9)
    noise = [rng.normal(size=(n, LAYERS, DIM)).astype(np.float32) for n in (60, 60, 30)]
    none = probe_report(*noise, seeds=SEEDS, train_fraction=0.8, permutations=99, bootstrap=FAST)
    assert none["baselines_at_chosen_layer"]["permutation_category_holdout_auc"]["p_value_upper"] > 0.05



# --- the bootstrap resamples both classes -------------------------------------------------------


def _interval(pos_scores, neg_scores, resamples=2000):
    from harness.gates import bootstrap_auc_interval

    stream = np.random.default_rng([7919, 0])
    return bootstrap_auc_interval([(torch.tensor(pos_scores), torch.tensor(neg_scores))], resamples=resamples,
                                  stream=stream)


def test_the_interval_widens_when_the_negatives_vary():
    """Positives held at one score, so resampling them adds nothing: any width comes from resampling the negatives.

    Identical negatives give an interval of zero width; negatives that vary give a wider one. That shows the
    negatives used in the held-out AUC are resampled, not only the held-out positives.
    """
    rng = np.random.default_rng(4)
    positives = np.full(40, 0.0)
    low, high = _interval(positives, np.full(200, 1.0))
    assert high == low
    low, high = _interval(positives, rng.normal(0.0, 1.0, 200))
    assert high - low > 0.05



def test_the_interval_draw_is_shared_by_every_seed():
    """Two seeds with identical scores must give the same interval as one: one draw, applied to both."""
    rng = np.random.default_rng(6)
    pos_scores, neg_scores = torch.tensor(rng.normal(1.0, 1.0, 30)), torch.tensor(rng.normal(0.0, 1.0, 50))
    from harness.gates import bootstrap_auc_interval

    one = bootstrap_auc_interval([(pos_scores, neg_scores)], resamples=300, stream=np.random.default_rng(1))
    two = bootstrap_auc_interval([(pos_scores, neg_scores)] * 2, resamples=300, stream=np.random.default_rng(1))
    assert one == two


# --- the evaluation pool ------------------------------------------------------------------------


def test_the_pool_is_chosen_by_item_id_stratified_by_source_and_never_fitted_or_validated():
    from harness.gates import evaluation_pool, probe_splits

    ids = [f"item-{i}" for i in range(100)]
    groups = ["a"] * 80 + ["b"] * 20
    pool = evaluation_pool(ids, groups, 0.25)
    assert sum(1 for r in pool if groups[r] == "a") == 20 and sum(1 for r in pool if groups[r] == "b") == 5
    # The same IDs in another row order select the same items.
    order = np.random.default_rng(0).permutation(100)
    moved = evaluation_pool([ids[i] for i in order], [groups[i] for i in order], 0.25)
    assert {ids[order[r]] for r in moved} == {ids[r] for r in pool}
    rest = [r for r in range(100) if r not in set(pool)]
    for parts in probe_splits(40, rest, seeds=[0, 1, 2], train_fraction=0.75):
        used = set(parts["neg"]["fit"].tolist()) | set(parts["neg"]["validation"].tolist())
        assert not used & set(pool)
        assert used == set(rest)


def test_the_report_counts_the_pool_by_source():
    pos, neg, held = _arms()
    groups = ["x"] * 40 + ["y"] * 20
    report = probe_report(pos, neg, held, seeds=SEEDS, train_fraction=0.8, neg_ids=[f"n{i}" for i in range(60)],
                          neg_groups=groups, permutations=FAST, bootstrap=FAST, random_directions=FAST)
    assert report["evaluation_pool"]["by_source"] == {"x": 8, "y": 4}


# --- the shared shuffle -------------------------------------------------------------------------


def test_an_item_in_several_fit_splits_keeps_one_shuffled_label():
    from harness.gates import shuffled_fit_labels

    true_labels = np.array([1.0] * 10 + [0.0] * 10)
    fit_items = [np.array([0, 1, 2, 12, 13]), np.array([2, 3, 12, 14, 0])]
    for draw in range(20):
        first, second = shuffled_fit_labels(true_labels, fit_items, np.random.default_rng(draw))
        assert first[2] == second[0]  # item 2
        assert first[3] == second[2]  # item 12
        assert first[0] == second[4]  # item 0


# --- the probe fit ------------------------------------------------------------------------------


def test_l2_keeps_the_weights_finite_on_separable_data():
    from harness.gates import _fit_probe

    X = torch.tensor([[-2.0], [-1.0], [1.0], [2.0]])
    y = torch.tensor([0.0, 0.0, 1.0, 1.0])
    w, _ = _fit_probe(X, y)
    assert torch.isfinite(w).all() and abs(w.item()) < 20
    weak, _ = _fit_probe(X, y, l2=1e-4)
    assert abs(weak.item()) > abs(w.item())  # a smaller penalty lets the weight grow


def test_rescaling_a_feature_does_not_change_the_report():
    """Each layer is standardised on its fit split, so a unit change in a feature cannot move any AUC."""
    pos, neg, held = _arms()
    kwargs = dict(seeds=SEEDS, train_fraction=0.8, permutations=FAST, bootstrap=FAST, random_directions=FAST)
    first = probe_report(pos, neg, held, **kwargs)
    scaled = [a.copy() for a in (pos, neg, held)]
    for a in scaled:
        a[:, :, 2] *= 1000.0
    second = probe_report(*scaled, **kwargs)
    assert first["layer_selection"]["chosen_layer"] == second["layer_selection"]["chosen_layer"]
    for key in ("in_distribution_auc_mean", "category_holdout_auc_mean"):
        assert abs(first["at_chosen_layer"][key] - second["at_chosen_layer"][key]) < 1e-3


# --- midranks -----------------------------------------------------------------------------------


def test_auc_with_tied_scores_matches_a_brute_force_count_with_ties_as_half():
    from harness.gates import _auc

    rng = np.random.default_rng(8)
    for _ in range(20):
        scores = rng.integers(0, 4, size=30).astype(float)  # many ties
        labels = rng.integers(0, 2, size=30)
        if labels.min() == labels.max():
            continue
        pos, neg = scores[labels == 1], scores[labels == 0]
        expected = sum(float(p > n) + 0.5 * float(p == n) for p in pos for n in neg) / (len(pos) * len(neg))
        assert abs(_auc(torch.tensor(scores), torch.tensor(labels)) - expected) < 1e-9
    assert _auc(torch.tensor([1.0, 1.0, 1.0, 1.0]), torch.tensor([1, 1, 0, 0])) == 0.5


# --- the random-direction baseline -------------------------------------------------------------


def test_random_directions_are_folded_and_counted():
    pos, neg, held = _arms()
    report = probe_report(pos, neg, held, seeds=SEEDS, train_fraction=0.8, permutations=FAST, bootstrap=FAST,
                          random_directions=200)
    random = report["baselines_at_chosen_layer"]["random_direction_category_holdout_auc_folded"]
    assert random["n"] == 200
    assert 0.5 <= random["median"] <= random["q95"] <= random["q975"] <= random["q99"] <= 1.0
