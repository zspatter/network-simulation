import sys
from os.path import abspath, dirname, join

import pytest

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

from benchmark_strategies import (  # noqa: E402
    AggregatedMetrics,
    SignificanceResult,
    TrialMetrics,
    compare_to_reference,
    print_report,
    print_significance_report,
    run_benchmark,
    run_trial,
)

from organflow.allocation import STRATEGIES  # noqa: E402
from organflow.GraphBuilder import GraphBuilder  # noqa: E402
from organflow.OrganGenerator import OrganGenerator  # noqa: E402
from organflow.PatientGenerator import PatientGenerator  # noqa: E402


def test_run_trial_accounts_for_every_organ():
    metrics = run_trial(seed=1, strategy=STRATEGIES['baseline'], num_nodes=10, rounds=3,
                        patients_per_round=8, harvests_per_round=3)

    assert isinstance(metrics, TrialMetrics)
    # every harvested organ is either transplanted or wasted - none simply
    # vanish. At most 7 organs per donor (6 types, but kidney yields 2).
    total_organs = metrics.organs_transplanted + metrics.organs_wasted
    assert 0 < total_organs <= 7 * 3 * 3  # max organs/donor * harvests_per_round * rounds
    assert metrics.runtime_seconds >= 0


def test_run_trial_realistic_outcomes_discards_some_organs_and_keeps_those_patients():
    # with realistic_outcomes some matched organs are declined/discarded (counted as wasted,
    # not transplanted) and their would-be recipients keep waiting
    off = run_trial(seed=3, strategy=STRATEGIES['real_world_circle'], num_nodes=12, rounds=6,
                    patients_per_round=20, harvests_per_round=6)
    on = run_trial(seed=3, strategy=STRATEGIES['real_world_circle'], num_nodes=12, rounds=6,
                   patients_per_round=20, harvests_per_round=6, realistic_outcomes=True)

    assert off.organs_discarded == 0
    assert on.organs_discarded > 0
    # discards are a subset of wasted organs, and modeling them can only reduce transplants
    assert on.organs_discarded <= on.organs_wasted
    assert on.organs_transplanted <= off.organs_transplanted


def test_run_trial_conserves_every_patient_across_all_exits():
    # Conservation invariant: every patient who arrives must end the trial as exactly one of
    # {still waiting, deceased-donor transplanted, living-donor transplanted, died, removed}.
    # None may be lost or double-counted - this guards the removal / living-donor / discard
    # channels against silently dropping or duplicating patients.
    rounds, patients_per_round = 8, 14
    metrics = run_trial(seed=5, strategy=STRATEGIES['real_world_circle'], num_nodes=12,
                        rounds=rounds, patients_per_round=patients_per_round,
                        harvests_per_round=5, snapshot_interval_rounds=rounds,
                        other_removal_annual_rate=0.05, living_donors_per_round=2,
                        realistic_outcomes=True)

    arrivals = patients_per_round * rounds
    final_waiting = metrics.wait_list_size_snapshots[-1][1]
    accounted = (final_waiting + metrics.organs_transplanted
                 + metrics.living_donor_transplants + metrics.waitlist_deaths
                 + metrics.other_removals)
    assert accounted == arrivals


def test_run_trial_extra_outflows_are_off_by_default():
    metrics = run_trial(seed=4, strategy=STRATEGIES['baseline'], num_nodes=10, rounds=4,
                        patients_per_round=10, harvests_per_round=3)
    assert metrics.organs_discarded == 0
    assert metrics.other_removals == 0
    assert metrics.living_donor_transplants == 0


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


def test_run_trial_uses_a_provided_network_instead_of_building_a_synthetic_one(monkeypatch):
    import benchmark_strategies

    real_network = GraphBuilder.graph_builder(6)  # built before patching, with the real method

    def _fail_if_called(*_args, **_kwargs):
        raise AssertionError('GraphBuilder.graph_builder should not be called when a '
                             'network is passed to run_trial')

    monkeypatch.setattr(benchmark_strategies.GraphBuilder, 'graph_builder', _fail_if_called)

    metrics = run_trial(seed=1, strategy=STRATEGIES['baseline'], rounds=2,
                        patients_per_round=5, harvests_per_round=2, network=real_network)

    assert isinstance(metrics, TrialMetrics)


def test_run_trial_threads_patient_and_organ_nodes_through_to_the_generators(monkeypatch):
    import benchmark_strategies

    original_generate_patients = PatientGenerator.generate_patients
    original_generate_organs_to_list = OrganGenerator.generate_organs_to_list
    captured = {}

    def _capture_patients(graph, n, rng, eligible_nodes=None):
        captured['patient_nodes'] = eligible_nodes
        return original_generate_patients(graph, n, rng, eligible_nodes)

    def _capture_organs(graph, n, organ_list, rng, eligible_nodes=None):
        captured['organ_nodes'] = eligible_nodes
        return original_generate_organs_to_list(graph, n, organ_list, rng, eligible_nodes)

    monkeypatch.setattr(benchmark_strategies.PatientGenerator, 'generate_patients',
                       _capture_patients)
    monkeypatch.setattr(benchmark_strategies.OrganGenerator, 'generate_organs_to_list',
                       _capture_organs)

    run_trial(seed=1, strategy=STRATEGIES['baseline'], num_nodes=6, rounds=1,
             patients_per_round=5, harvests_per_round=2,
             patient_nodes=[1, 2], organ_nodes=[3, 4])

    assert captured['patient_nodes'] == [1, 2]
    assert captured['organ_nodes'] == [3, 4]


def test_run_trial_records_wait_list_size_snapshots_at_the_given_interval():
    metrics = run_trial(seed=1, strategy=STRATEGIES['baseline'], num_nodes=10, rounds=6,
                        patients_per_round=10, harvests_per_round=2,
                        snapshot_interval_rounds=2)

    assert [round_number for round_number, _ in metrics.wait_list_size_snapshots] == [2, 4, 6]
    assert all(size >= 0 for _, size in metrics.wait_list_size_snapshots)


def test_run_trial_records_no_snapshots_by_default():
    metrics = run_trial(seed=1, strategy=STRATEGIES['baseline'], num_nodes=10, rounds=6,
                        patients_per_round=10, harvests_per_round=2)

    assert metrics.wait_list_size_snapshots == []


def test_run_benchmark_parallel_matches_sequential_exactly():
    # trials are independent and seeded, so a process-pool run must be bit-for-bit identical
    # to the sequential one - the parallelization is a pure speedup, not a behavior change
    kwargs = dict(strategy_names=['baseline', 'optimal_composite'], seeds=range(3),
                  num_nodes=10, rounds=4, patients_per_round=8, harvests_per_round=3)
    _, sequential = run_benchmark(workers=1, **kwargs)
    _, parallel = run_benchmark(workers=2, **kwargs)

    assert sequential.keys() == parallel.keys()
    for name in sequential:
        assert [t.organs_transplanted for t in sequential[name]] == \
               [t.organs_transplanted for t in parallel[name]]
        assert [t.waitlist_deaths for t in sequential[name]] == \
               [t.waitlist_deaths for t in parallel[name]]


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


def _aggregated_metrics(strategy_name, **overrides):
    defaults = dict(strategy_name=strategy_name, transplanted_mean=10.0, transplanted_stdev=1.0,
                    wasted_mean=2.0, deaths_mean=1.0, deaths_high_acuity_mean=0.5,
                    median_wait_mean=1.0, life_years_mean=100.0, priority_served_mean=50.0,
                    fairness_spread_mean=0.1, runtime_mean=0.01)
    defaults.update(overrides)
    return AggregatedMetrics(**defaults)


def test_print_report_includes_every_strategy_and_its_metrics(capsys):
    aggregated = [_aggregated_metrics('baseline'),
                 _aggregated_metrics('real_world_circle', life_years_mean=120.0)]

    print_report(aggregated)

    out = capsys.readouterr().out
    assert 'baseline' in out
    assert 'real_world_circle' in out
    assert '120.0' in out


def test_print_significance_report_marks_significant_rows_and_not_insignificant_ones(capsys):
    significant = SignificanceResult(strategy_name='optimal_acuity', metric='waitlist_deaths',
                                     mean_diff=-1.5, ci_low=-2.0, ci_high=-1.0, effect_size=0.8,
                                     p_value=0.001, adjusted_p_value=0.004)
    not_significant = SignificanceResult(strategy_name='baseline', metric='waitlist_deaths',
                                         mean_diff=0.1, ci_low=-0.5, ci_high=0.7, effect_size=0.05,
                                         p_value=0.9, adjusted_p_value=1.0)

    print_significance_report([significant, not_significant], alpha=0.05,
                              reference='real_world_circle')

    out = capsys.readouterr().out
    assert 'optimal_acuity' in out
    assert 'baseline' in out
    assert 'real_world_circle' in out  # named as the reference in the header

    lines = {line.split()[0]: line for line in out.splitlines() if line.split()[:1]}
    assert lines['optimal_acuity'].rstrip().endswith('*')
    assert not lines['baseline'].rstrip().endswith('*')
