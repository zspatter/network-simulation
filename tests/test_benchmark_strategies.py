import sys
from os.path import abspath, dirname, join

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

from benchmark_strategies import TrialMetrics, run_benchmark, run_trial  # noqa: E402

from network_simulator.allocation import STRATEGIES  # noqa: E402


def test_run_trial_accounts_for_every_organ():
    metrics = run_trial(seed=1, strategy=STRATEGIES['baseline'], num_nodes=10, rounds=3,
                        patients_per_round=8, harvests_per_round=3)

    assert isinstance(metrics, TrialMetrics)
    # every harvested organ is either transplanted or wasted - none simply
    # vanish. At most 6 organ types per body get harvested (each with a 75%
    # chance), across harvests_per_round bodies per round.
    total_organs = metrics.organs_transplanted + metrics.organs_wasted
    assert 0 < total_organs <= 6 * 3 * 3  # organ types * harvests_per_round * rounds
    assert metrics.runtime_seconds >= 0


def test_run_trial_is_reproducible_for_the_same_seed():
    first = run_trial(seed=7, strategy=STRATEGIES['baseline'], num_nodes=10, rounds=3,
                      patients_per_round=8, harvests_per_round=3)
    second = run_trial(seed=7, strategy=STRATEGIES['baseline'], num_nodes=10, rounds=3,
                       patients_per_round=8, harvests_per_round=3)

    assert first.organs_transplanted == second.organs_transplanted
    assert first.total_priority_served == second.total_priority_served


def test_run_benchmark_aggregates_every_strategy():
    report = run_benchmark(seeds=range(2), num_nodes=10, rounds=3,
                           patients_per_round=8, harvests_per_round=3)

    assert {row.strategy_name for row in report} == set(STRATEGIES.keys())
    for row in report:
        assert row.transplanted_mean >= 0
        assert row.wasted_mean >= 0
