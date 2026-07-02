import sys
from os.path import abspath, dirname, join

import pytest

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

from benchmark_strategies import (  # noqa: E402
    TrialMetrics,
    compare_to_reference,
    run_benchmark,
    run_trial,
)

from network_simulator.allocation import STRATEGIES  # noqa: E402


def test_run_trial_accounts_for_every_organ():
    metrics = run_trial(seed=1, strategy=STRATEGIES['baseline'], num_nodes=10, rounds=3,
                        patients_per_round=8, harvests_per_round=3)

    assert isinstance(metrics, TrialMetrics)
    # every harvested organ is either transplanted or wasted - none simply
    # vanish. At most 7 organs per donor (6 types, but kidney yields 2).
    total_organs = metrics.organs_transplanted + metrics.organs_wasted
    assert 0 < total_organs <= 7 * 3 * 3  # max organs/donor * harvests_per_round * rounds
    assert metrics.runtime_seconds >= 0


def test_run_trial_death_metrics_are_internally_consistent():
    # scarce organs + many rounds so high-acuity patients accumulate and die
    metrics = run_trial(seed=2, strategy=STRATEGIES['baseline'], num_nodes=10, rounds=10,
                        patients_per_round=15, harvests_per_round=1)

    assert metrics.waitlist_deaths > 0
    assert metrics.deaths_high_acuity + metrics.deaths_low_acuity == metrics.waitlist_deaths
    assert sum(metrics.deaths_by_organ.values()) == metrics.waitlist_deaths
    # a transplant credits life-years and records a wait time for each match
    assert len(metrics.wait_times_to_transplant) == metrics.organs_transplanted
    if metrics.organs_transplanted:
        assert metrics.life_years_saved > 0
        assert metrics.median_wait() >= 0


def test_run_trial_is_reproducible_for_the_same_seed():
    kwargs = dict(num_nodes=10, rounds=5, patients_per_round=12, harvests_per_round=2)
    first = run_trial(seed=7, strategy=STRATEGIES['baseline'], **kwargs)
    second = run_trial(seed=7, strategy=STRATEGIES['baseline'], **kwargs)

    assert first.organs_transplanted == second.organs_transplanted
    assert first.total_priority_served == second.total_priority_served
    assert first.waitlist_deaths == second.waitlist_deaths
    assert first.deaths_by_organ == second.deaths_by_organ
    assert first.wait_times_to_transplant == second.wait_times_to_transplant


def test_run_benchmark_aggregates_every_strategy():
    report, trials_by_strategy = run_benchmark(seeds=range(2), num_nodes=10, rounds=4,
                                               patients_per_round=10, harvests_per_round=2)

    assert {row.strategy_name for row in report} == set(STRATEGIES.keys())
    for row in report:
        assert row.transplanted_mean >= 0
        assert row.wasted_mean >= 0
        assert row.deaths_mean >= 0
        assert row.deaths_high_acuity_mean >= 0
        assert row.life_years_mean >= 0

    # trials_by_strategy carries the raw per-seed values the aggregates were computed
    # from - needed for compare_to_reference's paired (same-seed) comparisons
    assert set(trials_by_strategy.keys()) == set(STRATEGIES.keys())
    for trials in trials_by_strategy.values():
        assert len(trials) == 2
        assert all(isinstance(trial, TrialMetrics) for trial in trials)


def test_compare_to_reference_pairs_every_other_strategy_against_the_reference():
    _, trials_by_strategy = run_benchmark(seeds=range(5), num_nodes=10, rounds=4,
                                          patients_per_round=10, harvests_per_round=2)

    results = compare_to_reference(trials_by_strategy, reference='real_world_circle',
                                   metrics=('waitlist_deaths',), num_resamples=200)

    compared_strategies = {r.strategy_name for r in results}
    assert compared_strategies == set(STRATEGIES.keys()) - {'real_world_circle'}
    for result in results:
        assert result.metric == 'waitlist_deaths'
        assert 0.0 <= result.p_value <= 1.0
        assert 0.0 <= result.adjusted_p_value <= 1.0
        assert result.adjusted_p_value >= result.p_value
        assert result.ci_low <= result.ci_high


def test_compare_to_reference_rejects_an_unknown_reference():
    _, trials_by_strategy = run_benchmark(seeds=range(2), num_nodes=10, rounds=2,
                                          patients_per_round=5, harvests_per_round=2)

    with pytest.raises(ValueError):
        compare_to_reference(trials_by_strategy, reference='not_a_real_strategy')
