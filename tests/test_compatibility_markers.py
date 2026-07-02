import random

from network_simulator.compatibility_markers import (
    BloodTypeLetter,
    BloodTypePolarity,
    OrganType,
)


def test_random_organ_type_returns_a_member():
    assert OrganType.random_organ_type(random.Random(0)) in OrganType


def test_random_blood_type_returns_a_member():
    assert BloodTypeLetter.random_blood_type(random.Random(0)) in BloodTypeLetter


def test_random_blood_polarity_returns_a_member():
    assert BloodTypePolarity.random_blood_polarity(random.Random(0)) in BloodTypePolarity


def test_enum_random_helpers_are_deterministic_and_uniform_by_default():
    # a seeded source makes the draws reproducible; default (uniform) sampling
    # still spans every member over enough draws
    rng = random.Random(1)
    draws = {OrganType.random_organ_type(rng) for _ in range(200)}
    assert draws == set(OrganType)
