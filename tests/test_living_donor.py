import random

from network_simulator.BloodType import BloodType
from network_simulator.clinical.living_donor import (
    LIVING_DONOR_ORGAN_WEIGHTS,
    simulate_living_donor_transplants,
)
from network_simulator.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from network_simulator.Patient import Patient
from network_simulator.WaitList import WaitList

o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)


def _wait_list(kidney: int, liver: int, heart: int) -> WaitList:
    wait_list = WaitList()
    for organ, count in ((OrganType.Kidney, kidney), (OrganType.Liver, liver),
                         (OrganType.Heart, heart)):
        for _ in range(count):
            Patient('p', 'n/a', organ, o_neg, 100, 1, wait_list)
    return wait_list


def test_zero_count_transplants_nobody():
    wait_list = _wait_list(10, 10, 10)
    assert simulate_living_donor_transplants(wait_list, 0, random.Random(0)) == []
    assert len(wait_list.wait_list) == 30


def test_recipients_are_removed_and_only_kidney_or_liver():
    wait_list = _wait_list(100, 40, 30)
    rng = random.Random(3)
    recipients = simulate_living_donor_transplants(wait_list, 20, rng)

    assert len(recipients) == 20
    assert len(wait_list.wait_list) == 170 - 20
    for patient in recipients:
        assert patient.organ_needed in LIVING_DONOR_ORGAN_WEIGHTS
        assert patient not in wait_list.wait_list
    # heart candidates are never taken by a living-donor transplant
    assert all(p.organ_needed is not OrganType.Heart for p in recipients)


def test_is_kidney_dominant():
    wait_list = _wait_list(1000, 1000, 0)
    rng = random.Random(5)
    recipients = simulate_living_donor_transplants(wait_list, 400, rng)
    kidney = sum(1 for p in recipients if p.organ_needed is OrganType.Kidney)
    # weighted 0.9 kidney / 0.1 liver, so kidney should dominate despite equal pools
    assert kidney > len(recipients) * 0.7


def test_count_capped_by_eligible_pool():
    wait_list = _wait_list(3, 2, 50)  # only 5 eligible (kidney/liver) despite 55 waiting
    recipients = simulate_living_donor_transplants(wait_list, 20, random.Random(0))
    assert len(recipients) == 5
    # the 50 heart candidates all remain
    assert len(wait_list.wait_list) == 50
