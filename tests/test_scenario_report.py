import sys
from os.path import abspath, dirname, join

import pytest

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

import import_hospitals  # noqa: E402
import scenario_report  # noqa: E402
from benchmark_strategies import AggregatedMetrics, SignificanceResult, TrialMetrics  # noqa: E402

from network_simulator.allocation import STRATEGIES  # noqa: E402
from network_simulator.GraphBuilder import GraphBuilder  # noqa: E402


def test_resolve_strategy_names_curated_matches_the_documented_tiers():
    names = scenario_report.resolve_strategy_names('curated')

    assert names == [tier.name for tier in scenario_report.CURATED_STRATEGIES]
    assert all(name in STRATEGIES for name in names)


def test_resolve_strategy_names_all_returns_every_strategy():
    assert set(scenario_report.resolve_strategy_names('all')) == set(STRATEGIES.keys())


def test_resolve_strategy_names_explicit_list():
    assert scenario_report.resolve_strategy_names('baseline, real_world_circle') == \
        ['baseline', 'real_world_circle']


def test_resolve_strategy_names_rejects_unknown_names():
    with pytest.raises(ValueError):
        scenario_report.resolve_strategy_names('not_a_real_strategy')


def test_scaled_weekly_rates_scales_down_from_national_figures():
    patients, donors = scenario_report.scaled_weekly_rates(0.1)

    assert patients == round(scenario_report.NATIONAL_WEEKLY_NEW_PATIENTS * 0.1)
    assert donors == round(scenario_report.NATIONAL_WEEKLY_DECEASED_DONORS * 0.1)


def test_scaled_weekly_rates_at_full_scale_matches_national_figures():
    patients, donors = scenario_report.scaled_weekly_rates(1.0)

    assert patients == scenario_report.NATIONAL_WEEKLY_NEW_PATIENTS
    assert donors == scenario_report.NATIONAL_WEEKLY_DECEASED_DONORS


def test_default_seeds_for_horizon_is_smaller_for_longer_horizons():
    one_year = scenario_report.default_seeds_for_horizon(1)
    five_year = scenario_report.default_seeds_for_horizon(5)
    ten_year = scenario_report.default_seeds_for_horizon(10)

    assert one_year == 5
    assert five_year < one_year
    assert ten_year == five_year


def test_parse_args_defaults():
    args = scenario_report.parse_args([])

    assert args.horizon_years == '1,5,10'
    assert args.strategies == 'curated'
    assert args.seeds is None
    assert args.formats == 'markdown,csv'


def test_parse_args_overrides():
    args = scenario_report.parse_args(['--horizon-years', '1', '--seeds', '2',
                                       '--formats', 'markdown,csv,pdf'])

    assert args.horizon_years == '1'
    assert args.seeds == 2
    assert args.formats == 'markdown,csv,pdf'


def test_markdown_table_formats_header_separator_and_rows():
    table = scenario_report._markdown_table(['a', 'b'], [['1', '2'], ['3', '4']])

    lines = table.splitlines()
    assert lines[0] == '| a | b |'
    assert lines[1] == '| --- | --- |'
    assert lines[2] == '| 1 | 2 |'
    assert lines[3] == '| 3 | 4 |'


def test_final_wait_list_size_mean_averages_the_last_snapshot_across_trials():
    trials = [
        TrialMetrics(wait_list_size_snapshots=[(52, 100), (104, 150)]),
        TrialMetrics(wait_list_size_snapshots=[(52, 90), (104, 130)]),
    ]

    assert scenario_report._final_wait_list_size_mean(trials) == 140.0  # mean(150, 130)


def test_final_wait_list_size_mean_is_zero_with_no_snapshots():
    assert scenario_report._final_wait_list_size_mean([TrialMetrics()]) == 0.0


def test_trajectory_rows_averages_across_seeds_per_year():
    trials_by_strategy = {
        'real_world_circle': [
            TrialMetrics(wait_list_size_snapshots=[(52, 100), (104, 200)]),
            TrialMetrics(wait_list_size_snapshots=[(52, 120), (104, 220)]),
        ],
    }

    rows = scenario_report._trajectory_rows(trials_by_strategy)

    assert rows == [['real_world_circle', '1', '110'], ['real_world_circle', '2', '210']]


def test_significance_rows_marks_significant_results():
    results = [
        SignificanceResult(strategy_name='optimal_acuity', metric='waitlist_deaths',
                          mean_diff=-1.5, ci_low=-2.0, ci_high=-1.0, effect_size=0.8,
                          p_value=0.001, adjusted_p_value=0.004),
        SignificanceResult(strategy_name='baseline', metric='waitlist_deaths',
                          mean_diff=0.1, ci_low=-0.5, ci_high=0.7, effect_size=0.05,
                          p_value=0.9, adjusted_p_value=1.0),
    ]

    rows = scenario_report._significance_rows(results)

    assert rows[0][-1] == '*'
    assert rows[1][-1] == ''


def _fake_aggregated(strategy_name, **overrides):
    defaults = dict(strategy_name=strategy_name, transplanted_mean=10.0, transplanted_stdev=1.0,
                    wasted_mean=2.0, deaths_mean=1.0, deaths_high_acuity_mean=0.5,
                    median_wait_mean=1.0, life_years_mean=100.0, priority_served_mean=50.0,
                    fairness_spread_mean=0.1, runtime_mean=0.01)
    defaults.update(overrides)
    return AggregatedMetrics(**defaults)


def test_build_markdown_report_includes_methodology_and_every_horizon_section():
    trials = {'real_world_circle': [TrialMetrics(wait_list_size_snapshots=[(52, 100)])]}
    result = scenario_report.HorizonResult(
            years=1, seeds=1, aggregated=[_fake_aggregated('real_world_circle')],
            trials_by_strategy=trials, significance=[])

    report = scenario_report.build_markdown_report(
            [result], network_node_count=300, transplant_hospital_count=250, opo_count=50,
            scale=0.1, patients_per_round=136, harvests_per_round=33)

    assert '## Methodology' in report
    assert '1-Year Horizon' in report
    assert 'real_world_circle' in report
    assert 'Wait-List Size Trajectory' in report
    assert '300 real nodes' in report


def test_write_csv_outputs_writes_all_three_files_with_headers(tmp_path):
    trials = {'real_world_circle': [TrialMetrics(wait_list_size_snapshots=[(52, 100)])]}
    significance = [SignificanceResult(strategy_name='baseline', metric='waitlist_deaths',
                                       mean_diff=1.0, ci_low=0.0, ci_high=2.0, effect_size=0.3,
                                       p_value=0.2, adjusted_p_value=0.4)]
    result = scenario_report.HorizonResult(
            years=1, seeds=1, aggregated=[_fake_aggregated('real_world_circle')],
            trials_by_strategy=trials, significance=significance)

    scenario_report.write_csv_outputs([result], tmp_path)

    summary = (tmp_path / 'summary.csv').read_text()
    assert 'horizon_years' in summary and 'real_world_circle' in summary

    trajectory = (tmp_path / 'trajectory.csv').read_text()
    assert 'wait_list_size' in trajectory

    significance_csv = (tmp_path / 'significance.csv').read_text()
    assert 'baseline' in significance_csv


def test_run_horizon_computes_significance_only_with_multiple_seeds():
    network = GraphBuilder.graph_builder(10)

    single_seed = scenario_report.run_horizon(
            years=1, strategy_names=['baseline', 'real_world_circle'], seeds=1, network=network,
            patient_nodes=None, organ_nodes=None, patients_per_round=10, harvests_per_round=3)
    assert single_seed.significance == []

    multi_seed = scenario_report.run_horizon(
            years=1, strategy_names=['baseline', 'real_world_circle'], seeds=2, network=network,
            patient_nodes=None, organ_nodes=None, patients_per_round=10, harvests_per_round=3)
    assert len(multi_seed.significance) > 0


def test_build_network_uses_the_import_hospitals_pipeline(monkeypatch, tmp_path):
    csv_path = tmp_path / 'membership.csv'
    csv_path.write_text(
            'region,organizationType,membershipStatus,accountName,address1,city,state,'
            'zipCode\n'
            '4,Transplant Hospital,Approved,Test Hospital,100 Main St,Austin,TX,78701\n'
            '4,Independent OPO,Approved,Test OPO,200 Oak Ave,Austin,TX,78702\n')
    monkeypatch.setattr(import_hospitals, 'geocode_addresses',
                        lambda rows: {0: (30.27, -97.74), 1: (30.28, -97.75)})

    network, transplant_hospital_ids, opo_ids = scenario_report.build_network(str(csv_path))

    assert len(network.network_dict) == 2
    assert transplant_hospital_ids == {1}
    assert opo_ids == {2}
