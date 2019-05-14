import copy

from network_simulator.BloodType import BloodType
from network_simulator.Patient import Patient
from network_simulator.compatibility_markers import OrganType, BloodTypeLetter, BloodTypePolarity

blood_type = BloodType(BloodTypeLetter.A, BloodTypePolarity.POS)
patient1 = Patient('name', 'N/A', OrganType.Pancreas.value, blood_type, 200, 1)
patient2 = Patient('name', 'N/A', OrganType.Pancreas.value, blood_type, 100, 1)
patient2.patient_id = patient1.patient_id


def test__eq__():
    patient2_clone = copy.deepcopy(patient2)
    patient2_clone.patient_id = patient1.patient_id
    patient2_clone.priority = patient1.priority

    assert patient1 == patient2_clone
    assert patient2_clone == patient2_clone
    assert not patient2 == patient2_clone
    assert not patient1 == 3.14


def test__ne__():
    assert patient1 != patient2
    assert patient2 != patient1
    assert not patient1 != patient1
    assert patient1 != 3.14


def test__lt__():
    assert patient2 < patient1
    assert not patient1 < patient2


def test_le__():
    assert patient2 <= patient1
    assert patient2 <= patient2
    assert not patient1 <= patient2


def test__gt__():
    assert patient1 > patient2
    assert not patient2 > patient1


def test__ge__():
    assert patient1 >= patient2
    assert patient1 >= patient1
    assert not patient2 >= patient1
