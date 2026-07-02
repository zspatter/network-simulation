import sys
from os.path import abspath, dirname, join

import pytest

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

# reportlab is an optional dependency (pyproject.toml's `report` extra) - CI's `pip install
# -e .[dev]` doesn't install it, so these tests skip cleanly rather than failing to collect.
pytest.importorskip('reportlab')

from benchmark_strategies import AggregatedMetrics, SignificanceResult, TrialMetrics  # noqa: E402
from scenario_report import HorizonResult  # noqa: E402
from scenario_report_pdf import write_pdf_report  # noqa: E402


def _fake_aggregated(strategy_name, **overrides):
    defaults = dict(strategy_name=strategy_name, transplanted_mean=10.0, transplanted_stdev=1.0,
                    wasted_mean=2.0, deaths_mean=1.0, deaths_high_acuity_mean=0.5,
                    median_wait_mean=1.0, life_years_mean=100.0, priority_served_mean=50.0,
                    fairness_spread_mean=0.1, runtime_mean=0.01)
    defaults.update(overrides)
    return AggregatedMetrics(**defaults)


def test_write_pdf_report_produces_a_valid_pdf_file(tmp_path):
    trials = {'real_world_circle': [TrialMetrics(wait_list_size_snapshots=[(52, 100)])]}
    significance = [SignificanceResult(strategy_name='baseline', metric='waitlist_deaths',
                                       mean_diff=1.0, ci_low=0.0, ci_high=2.0, effect_size=0.3,
                                       p_value=0.2, adjusted_p_value=0.4)]
    result = HorizonResult(years=1, seeds=1, aggregated=[_fake_aggregated('real_world_circle')],
                           trials_by_strategy=trials, significance=significance)
    output_path = tmp_path / 'report.pdf'

    write_pdf_report([result], output_path, network_node_count=300,
                     transplant_hospital_count=250, opo_count=50)

    assert output_path.exists()
    assert output_path.read_bytes().startswith(b'%PDF')


def test_write_pdf_report_handles_a_horizon_with_no_significance_table(tmp_path):
    trials = {'real_world_circle': [TrialMetrics(wait_list_size_snapshots=[(52, 100)])]}
    result = HorizonResult(years=1, seeds=1, aggregated=[_fake_aggregated('real_world_circle')],
                           trials_by_strategy=trials, significance=[])
    output_path = tmp_path / 'report.pdf'

    write_pdf_report([result], output_path, network_node_count=300,
                     transplant_hospital_count=250, opo_count=50)

    assert output_path.exists()
