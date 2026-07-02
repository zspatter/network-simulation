import random
from collections import Counter

from network_simulator.clinical.hla import (
    ANTIGEN_POOL_SIZE,
    DONOR_ANTIGEN_COUNT,
    cpra,
    crossmatch_positive,
    donor_antigens,
    patient_unacceptable_antigens,
)


def test_donor_antigens_size_and_range():
    antigens = donor_antigens(random.Random(0))
    assert len(antigens) == DONOR_ANTIGEN_COUNT
    assert all(0 <= a < ANTIGEN_POOL_SIZE for a in antigens)


def test_crossmatch_positive_iff_intersection():
    assert crossmatch_positive(frozenset({1, 2, 3}), frozenset({3, 4})) is True
    assert crossmatch_positive(frozenset({1, 2, 3}), frozenset({4, 5})) is False
    assert crossmatch_positive(frozenset({1, 2, 3}), frozenset()) is False


def test_cpra_zero_when_unsensitized():
    assert cpra(frozenset()) == 0.0


def test_cpra_is_one_when_broadly_sensitized():
    # rejecting all but fewer than a donor's antigen count leaves no compatible donor
    unacceptable = frozenset(range(ANTIGEN_POOL_SIZE - 1))
    assert cpra(unacceptable) == 1.0


def test_cpra_increases_with_sensitization():
    low = cpra(frozenset(range(2)))
    mid = cpra(frozenset(range(10)))
    high = cpra(frozenset(range(25)))
    assert 0.0 < low < mid < high < 1.0


def test_patient_sensitization_distribution_is_mostly_low_with_a_tail():
    rng = random.Random(3)
    cpras = [cpra(patient_unacceptable_antigens(rng)) for _ in range(5000)]

    unsensitized = sum(1 for c in cpras if c == 0.0) / len(cpras)
    highly = sum(1 for c in cpras if c > 0.9) / len(cpras)

    # most patients unsensitized; a small highly-sensitized tail
    assert 0.6 < unsensitized < 0.8
    assert 0.03 < highly < 0.18


def test_generation_is_deterministic_for_same_seed():
    a = [tuple(sorted(donor_antigens(random.Random(9)))) for _ in range(5)]
    b = [tuple(sorted(donor_antigens(random.Random(9)))) for _ in range(5)]
    assert a == b
    assert Counter(a) == Counter(b)
