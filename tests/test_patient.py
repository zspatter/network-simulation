import copy

from network_simulator.BloodType import BloodType
from network_simulator.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from network_simulator.Patient import Patient

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


def test_comparisons_return_notimplemented_for_non_patient():
    # __eq__/__ne__ fall back to identity comparison when NotImplemented is
    # returned (so `== `/`!=` never raise), but the ordering operators have
    # no such fallback and would raise TypeError if compared directly -
    # calling the dunder methods lets us verify the NotImplemented branch
    # itself without tripping that.
    assert patient1.__lt__(3.14) is NotImplemented
    assert patient1.__le__(3.14) is NotImplemented
    assert patient1.__gt__(3.14) is NotImplemented
    assert patient1.__ge__(3.14) is NotImplemented


def test__hash__is_consistent_with_equality():
    clone = copy.deepcopy(patient1)
    assert clone == patient1
    assert hash(clone) == hash(patient1)
    assert len({patient1, clone}) == 1


def test__hash__distinguishes_different_patients():
    assert len({patient1, patient2}) == 2


def test__str__():
    text = str(patient1)

    assert 'Patient' in text
    assert patient1.patient_name in text
    assert patient1.illness in text
    assert str(patient1.priority) in text
    assert f'Rounds waited: {patient1.rounds_waited}' in text
    assert str(patient1.location) in text
