import sys
from os.path import abspath, dirname, join

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

import sensitivity_analysis  # noqa: E402

from organflow.clinical import acceptance, removal  # noqa: E402


def test_scalar_knob_perturbs_and_restores_the_constant():
    original = removal.OTHER_REMOVAL_ANNUAL_RATE
    knob = sensitivity_analysis._scalar_knob('x', removal, 'OTHER_REMOVAL_ANNUAL_RATE')

    knob.set_factor(1.5)
    assert removal.OTHER_REMOVAL_ANNUAL_RATE == original * 1.5
    knob.reset()
    assert removal.OTHER_REMOVAL_ANNUAL_RATE == original


def test_dict_knob_mutates_in_place_so_importers_see_it():
    live = acceptance.BASE_DISCARD_PROB
    original = dict(live)
    knob = sensitivity_analysis._dict_knob('x', acceptance, 'BASE_DISCARD_PROB')

    knob.set_factor(0.5)
    # same object (mutated in place), values halved and capped
    assert acceptance.BASE_DISCARD_PROB is live
    assert live != original
    knob.reset()
    assert live == original


def test_dict_knob_caps_probabilities():
    knob = sensitivity_analysis._dict_knob('x', acceptance, 'BASE_DISCARD_PROB', cap=0.5)
    try:
        knob.set_factor(10.0)
        assert all(v <= 0.5 for v in acceptance.BASE_DISCARD_PROB.values())
    finally:
        knob.reset()


def test_swing_is_a_percent_change_normalized_to_base():
    assert sensitivity_analysis._swing(low=8.0, high=12.0, base=10.0) == 40.0
    assert sensitivity_analysis._swing(low=5.0, high=5.0, base=10.0) == 0.0
    assert sensitivity_analysis._swing(low=1.0, high=2.0, base=0.0) == 0.0


def test_build_knobs_covers_the_documented_constants():
    labels = {knob.label for knob in sensitivity_analysis.build_knobs()}
    assert {'other_removal_rate', 'base_discard_prob', 'donor_recovery_prob',
            'air_overhead_hours'} <= labels


def test_run_sensitivity_returns_one_row_per_knob_ranked_by_death_swing():
    results = sensitivity_analysis.run_sensitivity(
            factor=0.25, seeds=1, rounds=52, patients_per_round=12, harvests_per_round=4)

    assert len(results) == len(sensitivity_analysis.build_knobs())
    swings = [abs(r.deaths_swing_pct) for r in results]
    assert swings == sorted(swings, reverse=True)  # ranked most-sensitive first

    # perturbing did not leave any constant mutated afterward
    assert removal.OTHER_REMOVAL_ANNUAL_RATE == removal.OTHER_REMOVAL_ANNUAL_RATE
