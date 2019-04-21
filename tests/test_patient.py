import network_simulator.BloodType as bT
import network_simulator.Patient as p
from network_simulator.CompatibilityMarkers import OrganType, BloodTypeLetter, BloodTypePolarity

blood_type = bT.BloodType(BloodTypeLetter.A, BloodTypePolarity.POS)
patient1 = p.Patient('name', 'N/A', OrganType.Pancreas.value, blood_type, 125, 1)
patient2 = p.Patient('name', 'N/A', OrganType.Pancreas.value, blood_type, 125, 1)
patient2.patient_id = patient1.patient_id


def test__eq__():
    assert patient1.__eq__(patient2)
    assert patient2.__eq__(patient2)


def test__ne__():
    assert patient1.__ne__(patient2)
    assert patient2.__ne__(patient1)


def test__lt__():
    assert patient2.__lt__(patient1)
    assert not patient1.__lt__(patient2)


def test_le__():
    assert patient2.__le__(patient1)
    assert patient2.__le__(patient2)
    assert not patient1.__le__(patient2)


def test__gt__():
    assert patient1.__gt__(patient2)
    assert not patient2.__gt__(patient1)


def test__ge__():
    assert patient1.__ge__(patient2)
    assert patient1.__ge__(patient1)
    assert not patient2.__ge__(patient1)
