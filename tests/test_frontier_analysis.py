import sys
from os.path import abspath, dirname, join

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

import frontier_analysis  # noqa: E402


def test_run_frontier_returns_one_point_per_weight():
    points = frontier_analysis.run_frontier(
            proximity_weights=[0.0, 2.0], seeds=1, rounds=52,
            patients_per_round=20, harvests_per_round=6)

    assert [p.proximity_weight for p in points] == [0.0, 2.0]
    for p in points:
        assert p.life_years > 0
        assert 0.0 <= p.discard_rate <= 1.0


def test_higher_proximity_weight_lowers_mean_transit():
    # the core trade-off: emphasizing geography keeps organs local, so mean transit falls
    points = frontier_analysis.run_frontier(
            proximity_weights=[0.0, 8.0], seeds=2, rounds=52 * 2,
            patients_per_round=25, harvests_per_round=7)
    ignore_geo, hyper_local = points
    assert hyper_local.mean_transit < ignore_geo.mean_transit


def test_format_frontier_renders_all_axes():
    points = frontier_analysis.run_frontier(
            proximity_weights=[1.0], seeds=1, rounds=52,
            patients_per_round=20, harvests_per_round=6)
    text = frontier_analysis.format_frontier(points)
    assert 'proximity wt' in text
    assert 'mean transit' in text
    assert 'fairness spread' in text
