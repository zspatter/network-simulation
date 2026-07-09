import random

from organflow.clinical import acceptance
from organflow.clinical.frequencies import (
    POPULATION_MEAN_QUALITY_INDEX,
    random_donor_type,
    random_quality_index,
)
from organflow.compatibility_markers import OrganType
from organflow.Organ import NEUTRAL_QUALITY_INDEX


def test_discard_probability_rises_with_cold_ischemia():
    near = acceptance.discard_probability(OrganType.Kidney, 1.0)
    far = acceptance.discard_probability(OrganType.Kidney, 12.0)
    assert far > near
    # an average-quality organ (the default index) multiplies the base rate by 1.0, so with no
    # transit the discard probability is exactly the observed base rate
    assert acceptance.discard_probability(OrganType.Kidney, 0.0) == \
        acceptance.BASE_DISCARD_PROB[OrganType.Kidney]


def test_discard_probability_is_capped():
    # an absurd transit time can't push discard above the cap
    capped = acceptance.discard_probability(OrganType.Pancreas, 10_000.0)
    assert capped == acceptance.MAX_DISCARD_PROB


def test_average_quality_organ_discards_at_the_base_rate():
    # at the neutral (population-mean) quality index the multiplier is 1.0, so a listed organ's
    # zero-transit discard probability equals its base rate exactly
    assert acceptance.discard_probability(OrganType.Liver, 0.0) == \
        acceptance.BASE_DISCARD_PROB[OrganType.Liver]


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
    # default index is neutral, so the expected rate is just the base rate
    expected = acceptance.BASE_DISCARD_PROB[OrganType.Kidney]
    assert abs(discarded / n - expected) < 0.02


def test_graft_survival_factor_decreases_and_is_floored():
    assert acceptance.graft_survival_factor(0.0) == 1.0
    assert acceptance.graft_survival_factor(5.0) < 1.0
    assert acceptance.graft_survival_factor(0.0) > acceptance.graft_survival_factor(5.0)
    assert acceptance.graft_survival_factor(10_000.0) == acceptance.MIN_GRAFT_FACTOR


def test_marginal_organs_are_discarded_more_than_pristine():
    pristine = acceptance.discard_probability(OrganType.Kidney, 2.0, quality_index=20.0)
    average = acceptance.discard_probability(OrganType.Kidney, 2.0)
    marginal = acceptance.discard_probability(OrganType.Kidney, 2.0, quality_index=80.0)
    assert pristine < average < marginal
    # the default (no index) call is the average-quality path
    assert average == acceptance.discard_probability(
            OrganType.Kidney, 2.0, quality_index=POPULATION_MEAN_QUALITY_INDEX)


def test_marginal_organs_graft_worse_than_pristine():
    pristine = acceptance.graft_survival_factor(3.0, quality_index=20.0)
    marginal = acceptance.graft_survival_factor(3.0, quality_index=80.0)
    assert marginal < pristine
    # organs at or better than the population mean graft at full quality (only transit penalizes)
    assert acceptance.quality_graft_factor(20.0) == 1.0
    assert acceptance.quality_graft_factor(80.0) < 1.0


def test_neutral_quality_index_is_a_no_op():
    # the population-mean index must multiply discard by exactly 1.0 and graft by exactly 1.0,
    # so an average organ is neither penalized nor rewarded (keeps BASE_DISCARD_PROB calibrated)
    assert acceptance.quality_discard_multiplier(POPULATION_MEAN_QUALITY_INDEX) == 1.0
    assert acceptance.quality_graft_factor(POPULATION_MEAN_QUALITY_INDEX) == 1.0


def test_quality_discard_multiplier_is_monotonic():
    grid = [0.0, 25.0, 50.0, 75.0, 100.0]
    multipliers = [acceptance.quality_discard_multiplier(q) for q in grid]
    assert multipliers == sorted(multipliers)
    assert multipliers[0] < 1.0 < multipliers[-1]


def test_quality_discard_multiplier_is_mean_preserving_over_the_population():
    # drawing the full donor population (57/43 DBD/DCD split, each with its quality distribution)
    # and averaging the discard multiplier must recover ~1.0, so the continuous index only
    # redistributes discard toward marginal organs rather than inflating the calibrated total
    rng = random.Random(7)
    n = 40000
    total = 0.0
    for _ in range(n):
        donor_type = random_donor_type(rng)
        q = random_quality_index(donor_type, rng)
        total += acceptance.quality_discard_multiplier(q)
    assert abs(total / n - 1.0) < 0.02


def test_organ_neutral_default_matches_the_population_mean():
    # the base-entity default and the generation population mean must be the same number, or a
    # hand-built organ would not be quality-neutral and BASE_DISCARD_PROB would drift
    assert NEUTRAL_QUALITY_INDEX == POPULATION_MEAN_QUALITY_INDEX
