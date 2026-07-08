import copy

from network_simulator.BloodType import BloodType
from network_simulator.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from network_simulator.Patient import Patient

blood_type = BloodType(BloodTypeLetter.A, BloodTypePolarity.POS)
patient1 = Patient('name', 'N/A', OrganType.Pancreas.value, blood_type, 200, 1)
patient2 = Patient('name', 'N/A', OrganType.Pancreas.value, blood_type, 100, 1)


def test__eq__is_identity_by_patient_id():
    clone = copy.deepcopy(patient1)  # same patient_id
    assert patient1 == clone
    assert patient1 == patient1
    # a genuinely different patient is not equal, even with identical other fields
    assert not patient1 == patient2
    assert not patient1 == 3.14


def test__ne__():
    assert patient1 != patient2
    assert not patient1 != patient1
    assert patient1 != 3.14


def test__hash__is_consistent_with_equality():
    clone = copy.deepcopy(patient1)
    assert clone == patient1
    assert hash(clone) == hash(patient1)
    assert len({patient1, clone}) == 1


def test__hash__distinguishes_different_patients():
    assert len({patient1, patient2}) == 2


def test_mutable_state_never_changes_identity():
    # equality is by patient_id alone, so any change to mutable per-round state -
    # priority, wait time, or the clinical fields - leaves a patient equal to itself
    clone = copy.deepcopy(patient1)
    clone.priority = 999
    clone.rounds_waited = 40
    clone.acuity = 0.9
    clone.raw_urgency = 38.0
    clone.body_size = 95.0
    clone.unacceptable_antigens = frozenset({1, 2, 3})
    clone.cpra = 0.99

    assert clone == patient1
    assert hash(clone) == hash(patient1)


def test__str__():
    text = str(patient1)

    assert 'Patient' in text
    assert patient1.patient_name in text
    assert patient1.illness in text
    assert str(patient1.priority) in text
    assert f'Rounds waited: {patient1.rounds_waited}' in text
    assert str(patient1.location) in text
