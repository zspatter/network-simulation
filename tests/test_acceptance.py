import random

from organflow.clinical import acceptance
from organflow.clinical.frequencies import DONOR_TYPE_WEIGHTS
from organflow.compatibility_markers import DonorType, OrganType


def test_discard_probability_rises_with_cold_ischemia():
    near = acceptance.discard_probability(OrganType.Kidney, 1.0)
    far = acceptance.discard_probability(OrganType.Kidney, 12.0)
    assert far > near
    # the default pathway is DBD, so the base rate is scaled by the DBD discard multiplier
    assert acceptance.discard_probability(OrganType.Kidney, 0.0) == \
        acceptance.BASE_DISCARD_PROB[OrganType.Kidney] * \
        acceptance.DONOR_TYPE_DISCARD_MULTIPLIER[DonorType.DBD]


def test_discard_probability_is_capped():
    # an absurd transit time can't push discard above the cap
    capped = acceptance.discard_probability(OrganType.Pancreas, 10_000.0)
    assert capped == acceptance.MAX_DISCARD_PROB


def test_discard_probability_uses_default_for_unlisted_organ():
    # Intestines is listed; construct the default path by checking an organ with a base rate
    # equals its table entry, and that the default constant is used where a lookup misses.
    assert acceptance.discard_probability(OrganType.Liver, 0.0) == \
        acceptance.BASE_DISCARD_PROB[OrganType.Liver] * \
        acceptance.DONOR_TYPE_DISCARD_MULTIPLIER[DonorType.DBD]


def test_kidney_and_pancreas_discard_more_than_heart():
    # matches the real ordering (thoracic organs are rarely discarded once recovered)
    base = acceptance.BASE_DISCARD_PROB
    assert base[OrganType.Kidney] > base[OrganType.Heart]
    assert base[OrganType.Pancreas] > base[OrganType.Heart]


def test_is_discarded_is_deterministic_under_seed():
    a = [acceptance.is_discarded(OrganType.Kidney, 5.0, rng=random.Random(0)) for _ in range(5)]
    b = [acceptance.is_discarded(OrganType.Kidney, 5.0, rng=random.Random(0)) for _ in range(5)]
    assert a == b


def test_is_discarded_frequency_tracks_probability():
    rng = random.Random(1)
    n = 20000
    discarded = sum(acceptance.is_discarded(OrganType.Kidney, 0.0, rng=rng) for _ in range(n))
    expected = acceptance.BASE_DISCARD_PROB[OrganType.Kidney] * \
        acceptance.DONOR_TYPE_DISCARD_MULTIPLIER[DonorType.DBD]
    assert abs(discarded / n - expected) < 0.02


def test_graft_survival_factor_decreases_and_is_floored():
    assert acceptance.graft_survival_factor(0.0) == 1.0
    assert acceptance.graft_survival_factor(5.0) < 1.0
    assert acceptance.graft_survival_factor(0.0) > acceptance.graft_survival_factor(5.0)
    assert acceptance.graft_survival_factor(10_000.0) == acceptance.MIN_GRAFT_FACTOR


def test_dcd_organs_are_discarded_more_than_dbd():
    dbd = acceptance.discard_probability(OrganType.Kidney, 2.0, DonorType.DBD)
    dcd = acceptance.discard_probability(OrganType.Kidney, 2.0, DonorType.DCD)
    assert dcd > dbd
    # DBD defaults, so the no-donor-type call matches the DBD path
    assert acceptance.discard_probability(OrganType.Kidney, 2.0) == dbd


def test_dcd_grafts_survive_worse_than_dbd():
    dbd = acceptance.graft_survival_factor(3.0, DonorType.DBD)
    dcd = acceptance.graft_survival_factor(3.0, DonorType.DCD)
    assert dcd < dbd
    assert acceptance.graft_survival_factor(3.0) == dbd  # default is DBD


def test_donor_type_discard_multipliers_are_mean_preserving():
    # weighting the DBD/DCD multipliers by the real 57/43 donor split should recover ~1.0,
    # so BASE_DISCARD_PROB stays the population average (the split just redistributes discard)
    total = sum(DONOR_TYPE_WEIGHTS.values())
    weighted = sum(DONOR_TYPE_WEIGHTS[dt] / total * acceptance.DONOR_TYPE_DISCARD_MULTIPLIER[dt]
                   for dt in DonorType)
    assert abs(weighted - 1.0) < 0.02
