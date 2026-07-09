import random

from organflow.BloodType import BloodType
from organflow.clinical.progression import initialize_urgency, simulate_round_progression
from organflow.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from organflow.Patient import Patient
from organflow.WaitList import WaitList

o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)


def _liver_patient(wait_list, meld=20.0):
    p = Patient('p', 'n/a', OrganType.Liver, o_neg, 100, 1, wait_list)
    p.raw_urgency = meld
    p.acuity = 0.0
    return p


def test_initialize_urgency_sets_native_and_acuity():
    patient = Patient('p', 'n/a', OrganType.Liver, o_neg, 100, 1)
    initialize_urgency(patient, random.Random(0))
    assert 6 <= patient.raw_urgency <= 40
    assert patient.acuity > 0.0


def test_progression_advances_acuity_for_survivors():
    wait_list = WaitList()
    patient = _liver_patient(wait_list, meld=20.0)
    acuity_before = patient.acuity

    # a low-acuity liver patient is very unlikely to die in one round; acuity should rise
    simulate_round_progression(wait_list, random.Random(0))
    if patient in wait_list.wait_list:
        assert patient.raw_urgency >= 20.0
        assert patient.acuity >= acuity_before


def test_progression_removes_and_returns_the_dead():
    wait_list = WaitList()
    # a large cohort of the sickest liver patients: some will die this round
    for _ in range(200):
        _liver_patient(wait_list, meld=40.0)
    start = len(wait_list.wait_list)

    dead = simulate_round_progression(wait_list, random.Random(1))

    assert len(dead) > 0
    assert len(wait_list.wait_list) == start - len(dead)
    for patient in dead:
        assert patient not in wait_list.wait_list


def test_progression_is_deterministic_for_same_seed():
    def run(seed):
        wait_list = WaitList()
        for _ in range(100):
            _liver_patient(wait_list, meld=35.0)
        dead = simulate_round_progression(wait_list, random.Random(seed))
        return len(dead)

    assert run(7) == run(7)
