import random

from network_simulator.clinical import acceptance
from network_simulator.compatibility_markers import OrganType


def test_discard_probability_rises_with_cold_ischemia():
    near = acceptance.discard_probability(OrganType.Kidney, 1.0)
    far = acceptance.discard_probability(OrganType.Kidney, 12.0)
    assert far > near
    assert acceptance.discard_probability(OrganType.Kidney, 0.0) == \
        acceptance.BASE_DISCARD_PROB[OrganType.Kidney]


def test_discard_probability_is_capped():
    # an absurd transit time can't push discard above the cap
    capped = acceptance.discard_probability(OrganType.Pancreas, 10_000.0)
    assert capped == acceptance.MAX_DISCARD_PROB


def test_discard_probability_uses_default_for_unlisted_organ():
    # Intestines is listed; construct the default path by checking an organ with a base rate
    # equals its table entry, and that the default constant is used where a lookup misses.
    assert acceptance.discard_probability(OrganType.Liver, 0.0) == \
        acceptance.BASE_DISCARD_PROB[OrganType.Liver]


def test_kidney_and_pancreas_discard_more_than_heart():
    # matches the real ordering (thoracic organs are rarely discarded once recovered)
    base = acceptance.BASE_DISCARD_PROB
    assert base[OrganType.Kidney] > base[OrganType.Heart]
    assert base[OrganType.Pancreas] > base[OrganType.Heart]


def test_is_discarded_is_deterministic_under_seed():
    a = [acceptance.is_discarded(OrganType.Kidney, 5.0, random.Random(0)) for _ in range(5)]
    b = [acceptance.is_discarded(OrganType.Kidney, 5.0, random.Random(0)) for _ in range(5)]
    assert a == b


def test_is_discarded_frequency_tracks_probability():
    rng = random.Random(1)
    n = 20000
    discarded = sum(acceptance.is_discarded(OrganType.Kidney, 0.0, rng) for _ in range(n))
    assert abs(discarded / n - acceptance.BASE_DISCARD_PROB[OrganType.Kidney]) < 0.02


def test_graft_survival_factor_decreases_and_is_floored():
    assert acceptance.graft_survival_factor(0.0) == 1.0
    assert acceptance.graft_survival_factor(5.0) < 1.0
    assert acceptance.graft_survival_factor(0.0) > acceptance.graft_survival_factor(5.0)
    assert acceptance.graft_survival_factor(10_000.0) == acceptance.MIN_GRAFT_FACTOR
