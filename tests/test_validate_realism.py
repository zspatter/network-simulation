import sys
from os.path import abspath, dirname, join

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

import validate_realism  # noqa: E402

from organflow.Network import Network  # noqa: E402
from organflow.Node import Node  # noqa: E402


def _coordinate_network() -> Network:
    return Network({1: Node(1, 'A', latitude=41.88, longitude=-87.63),
                    2: Node(2, 'B', latitude=34.05, longitude=-118.24)})


def test_comparison_rows_cover_every_target_metric():
    model = {
        'deceased_transplants_per_year': 40_000.0,
        'living_transplants_per_year': 7_000.0,
        'deaths_per_year': 6_000.0,
        'removals_per_year': 8_000.0,
        'non_use_rate': 0.21,
        'waitlist_final': 100_000.0,
    }
    rows = validate_realism.comparison_rows(model)

    assert len(rows) == 6
    labels = ' '.join(row.metric.lower() for row in rows)
    for token in ('transplant', 'living', 'death', 'removal', 'non-use', 'wait-list'):
        assert token in labels
    # ratio is model / target
    non_use = next(r for r in rows if r.unit == 'rate')
    assert non_use.ratio() == 0.21 / validate_realism.OPTN_2024['overall_non_use_rate']


def test_format_table_renders_rates_and_counts():
    rows = validate_realism.comparison_rows({
        'deceased_transplants_per_year': 40_000.0, 'living_transplants_per_year': 7_000.0,
        'deaths_per_year': 6_000.0, 'removals_per_year': 8_000.0, 'non_use_rate': 0.21,
        'waitlist_final': 100_000.0})
    text = validate_realism._format_table(rows)
    assert 'model (full-scale)' in text
    assert '%' in text  # the rate row renders as a percentage
    assert 'x' in text  # ratio column


def test_run_validation_returns_full_scale_metrics():
    net = _coordinate_network()
    model = validate_realism.run_validation(net, [1, 2], [1, 2], scale=0.01, years=1, seeds=1)

    assert set(model) == {'deceased_transplants_per_year', 'living_transplants_per_year',
                          'deaths_per_year', 'removals_per_year', 'non_use_rate', 'waitlist_final'}
    assert model['deceased_transplants_per_year'] > 0
    assert 0.0 <= model['non_use_rate'] <= 1.0
