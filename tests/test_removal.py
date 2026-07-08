import random

from network_simulator.BloodType import BloodType
from network_simulator.clinical import removal
from network_simulator.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from network_simulator.Patient import Patient
from network_simulator.WaitList import WaitList

o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)


def _wait_list(n: int) -> WaitList:
    wait_list = WaitList()
    for _ in range(n):
        Patient('p', 'n/a', OrganType.Kidney, o_neg, 100, 1, wait_list)
    return wait_list


def test_per_round_removal_prob_is_between_zero_and_one():
    prob = removal.per_round_removal_prob(0.05)
    assert 0.0 < prob < 1.0
    # a higher annual hazard yields a higher per-round probability
    assert removal.per_round_removal_prob(0.20) > prob


def test_per_round_removal_prob_zero_rate_is_zero():
    assert removal.per_round_removal_prob(0.0) == 0.0


def test_simulate_round_removals_zero_rate_removes_nobody():
    wait_list = _wait_list(50)
    removed = removal.simulate_round_removals(wait_list, annual_rate=0.0, rng=random.Random(0))
    assert removed == []
    assert len(wait_list.wait_list) == 50


def test_simulate_round_removals_removes_and_returns_a_realistic_share():
    wait_list = _wait_list(2000)
    rng = random.Random(1)
    removed = removal.simulate_round_removals(wait_list, annual_rate=0.05, rng=rng)

    # removed patients are off the list and returned
    assert len(removed) > 0
    assert len(wait_list.wait_list) == 2000 - len(removed)
    for patient in removed:
        assert patient not in wait_list.wait_list
    # a ~5%/yr weekly hazard removes only a small fraction in one round
    assert len(removed) / 2000 < 0.02


def test_simulate_round_removals_is_deterministic_under_seed():
    a = removal.simulate_round_removals(_wait_list(500), 0.08, random.Random(42))
    b = removal.simulate_round_removals(_wait_list(500), 0.08, random.Random(42))
    assert len(a) == len(b)
