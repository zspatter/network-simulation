import random
from collections import Counter

from organflow.clinical.frequencies import (
    DONOR_RECOVERY_PROBABILITIES,
    DONOR_TYPE_WEIGHTS,
    US_BLOOD_TYPE_WEIGHTS,
    US_WAITLIST_ADDITIONS_ORGAN_WEIGHTS,
    US_WAITLIST_ORGAN_WEIGHTS,
    random_arrival_organ,
    random_donor_type,
    random_us_blood_type,
    random_waitlist_organ,
    weighted_choice,
)
from organflow.compatibility_markers import (
    BloodTypeLetter,
    BloodTypePolarity,
    DonorType,
    OrganType,
)


def test_weighted_choice_is_deterministic_for_same_seed():
    items = ['a', 'b', 'c']
    weights = [1.0, 2.0, 3.0]
    first = [weighted_choice(items, weights, random.Random(1)) for _ in range(20)]
    second = [weighted_choice(items, weights, random.Random(1)) for _ in range(20)]
    assert first == second


def test_weighted_choice_respects_weights():
    # a zero-weight item is never chosen; the rest appear roughly proportionally
    rng = random.Random(0)
    counts = Counter(weighted_choice(['x', 'y', 'z'], [0.0, 1.0, 3.0], rng)
                     for _ in range(4000))
    assert counts['x'] == 0
    assert counts['z'] > counts['y']


def test_random_us_blood_type_matches_distribution():
    rng = random.Random(42)
    n = 40000
    counts = Counter((bt.blood_type_letter, bt.blood_type_polarity)
                     for bt in (random_us_blood_type(rng) for _ in range(n)))

    total_weight = sum(US_BLOOD_TYPE_WEIGHTS.values())
    for key, weight in US_BLOOD_TYPE_WEIGHTS.items():
        expected = weight / total_weight
        observed = counts[key] / n
        assert abs(observed - expected) < 0.02

    # O+ is by far the most common; AB- by far the rarest
    o_pos = counts[(BloodTypeLetter.O, BloodTypePolarity.POS)]
    ab_neg = counts[(BloodTypeLetter.AB, BloodTypePolarity.NEG)]
    assert o_pos > ab_neg * 10


def test_random_waitlist_organ_is_kidney_dominant():
    rng = random.Random(7)
    n = 40000
    counts = Counter(random_waitlist_organ(rng) for _ in range(n))

    total_weight = sum(US_WAITLIST_ORGAN_WEIGHTS.values())
    kidney_share = counts[OrganType.Kidney] / n
    assert abs(kidney_share - US_WAITLIST_ORGAN_WEIGHTS[OrganType.Kidney] / total_weight) < 0.03
    # kidney dominates every other organ need combined
    assert counts[OrganType.Kidney] > n / 2


def test_random_arrival_organ_matches_additions_mix():
    rng = random.Random(11)
    n = 40000
    counts = Counter(random_arrival_organ(rng) for _ in range(n))

    total_weight = sum(US_WAITLIST_ADDITIONS_ORGAN_WEIGHTS.values())
    kidney_share = counts[OrganType.Kidney] / n
    assert abs(kidney_share
               - US_WAITLIST_ADDITIONS_ORGAN_WEIGHTS[OrganType.Kidney] / total_weight) < 0.03


def test_arrivals_are_less_kidney_dominated_than_prevalence():
    # the flow (additions) must be less kidney-heavy than the stock (prevalence);
    # sampling arrivals from prevalence is exactly the bug this split fixes
    prevalence_total = sum(US_WAITLIST_ORGAN_WEIGHTS.values())
    additions_total = sum(US_WAITLIST_ADDITIONS_ORGAN_WEIGHTS.values())
    prevalence_kidney = US_WAITLIST_ORGAN_WEIGHTS[OrganType.Kidney] / prevalence_total
    additions_kidney = US_WAITLIST_ADDITIONS_ORGAN_WEIGHTS[OrganType.Kidney] / additions_total
    assert additions_kidney < prevalence_kidney


def test_random_donor_type_matches_the_2024_split():
    rng = random.Random(13)
    n = 40000
    counts = Counter(random_donor_type(rng) for _ in range(n))

    total = sum(DONOR_TYPE_WEIGHTS.values())
    dbd_share = counts[DonorType.DBD] / n
    assert abs(dbd_share - DONOR_TYPE_WEIGHTS[DonorType.DBD] / total) < 0.03
    # DBD is the majority pathway, but DCD is a large minority (~43%)
    assert counts[DonorType.DBD] > counts[DonorType.DCD]
    assert counts[DonorType.DCD] / n > 0.35


def test_donor_recovery_probabilities_are_ordered_and_valid():
    # every probability is a valid probability, and kidney is the most recoverable
    assert all(0.0 <= p <= 1.0 for p in DONOR_RECOVERY_PROBABILITIES.values())
    assert DONOR_RECOVERY_PROBABILITIES[OrganType.Kidney] == max(
            DONOR_RECOVERY_PROBABILITIES.values())
    assert DONOR_RECOVERY_PROBABILITIES[OrganType.Heart] < \
        DONOR_RECOVERY_PROBABILITIES[OrganType.Liver]
