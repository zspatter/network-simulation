import random
import sys
from os.path import abspath, dirname, join

import pytest

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

from benchmark_stats import (  # noqa: E402
    bootstrap_ci,
    holm_bonferroni,
    paired_effect_size,
    paired_permutation_test,
    required_sample_size,
)


def test_paired_permutation_test_rejects_a_clearly_shifted_sample():
    rng = random.Random(1)
    diffs = [5.0 + rng.gauss(0, 1) for _ in range(30)]

    p = paired_permutation_test(diffs, num_resamples=2000, rng=random.Random(2))

    assert p < 0.01


def test_paired_permutation_test_does_not_reject_identical_paired_samples():
    # identical paired samples -> every difference is exactly 0
    diffs = [0.0] * 20

    assert paired_permutation_test(diffs, num_resamples=500, rng=random.Random(3)) == 1.0


def test_paired_permutation_test_returns_one_for_empty_input():
    assert paired_permutation_test([]) == 1.0


def test_bootstrap_ci_contains_the_known_mean_of_a_synthetic_distribution():
    rng = random.Random(4)
    true_mean = 10.0
    values = [true_mean + rng.gauss(0, 2) for _ in range(200)]

    lo, hi = bootstrap_ci(values, num_resamples=2000, confidence=0.95, rng=random.Random(5))

    assert lo <= true_mean <= hi


def test_bootstrap_ci_on_empty_input_returns_zero_zero():
    assert bootstrap_ci([]) == (0.0, 0.0)


def test_paired_effect_size_is_zero_for_too_few_samples_or_no_variance():
    assert paired_effect_size([]) == 0.0
    assert paired_effect_size([1.0]) == 0.0
    assert paired_effect_size([3.0, 3.0, 3.0]) == 0.0


def test_paired_effect_size_is_positive_when_diffs_consistently_favor_the_strategy():
    assert paired_effect_size([1.0, 2.0, 3.0, 2.0]) > 0


def test_holm_bonferroni_is_monotonically_non_decreasing_in_rank_order():
    p_values = {'a': 0.01, 'b': 0.5, 'c': 0.03, 'd': 0.9, 'e': 0.001}

    adjusted = holm_bonferroni(p_values)

    ranked_names = [name for name, _ in sorted(p_values.items(), key=lambda kv: kv[1])]
    adjusted_in_rank_order = [adjusted[name] for name in ranked_names]
    assert adjusted_in_rank_order == sorted(adjusted_in_rank_order)
    assert all(0.0 <= p <= 1.0 for p in adjusted.values())


def test_holm_bonferroni_never_adjusts_a_p_value_below_its_raw_value():
    p_values = {'a': 0.01, 'b': 0.02, 'c': 0.03}

    adjusted = holm_bonferroni(p_values)

    for name, raw in p_values.items():
        assert adjusted[name] >= raw


def test_required_sample_size_decreases_as_min_effect_grows():
    small_effect_n = required_sample_size(std_diff=2.0, min_effect=0.5)
    large_effect_n = required_sample_size(std_diff=2.0, min_effect=2.0)

    assert large_effect_n < small_effect_n


def test_required_sample_size_rejects_non_positive_inputs():
    with pytest.raises(ValueError):
        required_sample_size(std_diff=0.0, min_effect=1.0)
    with pytest.raises(ValueError):
        required_sample_size(std_diff=1.0, min_effect=0.0)
