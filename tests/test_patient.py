import network_simulator.Patient as p


def test_organ_category_name():
    assert p.Patient.organ_type_name(-1) is None
    assert p.Patient.organ_type_name(0) is 'Heart'
    assert p.Patient.organ_type_name(1) is 'Kidney'
    assert p.Patient.organ_type_name(2) is 'Liver'
    assert p.Patient.organ_type_name(3) is 'Lung'
    assert p.Patient.organ_type_name(4) is 'Pancreas'
    assert p.Patient.organ_type_name(5) is 'Intestines'
    assert p.Patient.organ_type_name(6) is None


def test_blood_type_name():
    assert p.Patient.blood_type_name(-1) is None
    assert p.Patient.blood_type_name(0) == 'O-'
    assert p.Patient.blood_type_name(1) == 'O+'
    assert p.Patient.blood_type_name(2) == 'A-'
    assert p.Patient.blood_type_name(3) == 'A+'
    assert p.Patient.blood_type_name(4) == 'B-'
    assert p.Patient.blood_type_name(5) == 'B+'
    assert p.Patient.blood_type_name(6) == 'AB-'
    assert p.Patient.blood_type_name(7) == 'AB+'
    assert p.Patient.blood_type_name(8) is None
