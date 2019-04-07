import network_simulator.Patient as p


def test__init__():
    test_patient1 = p.Patient(patient_name='patient a', illness='diabetes',
                              organ_needed=p.Patient.KIDNEY, blood_type=p.Patient.AB_POS,
                              priority=100, location=1)
    test_patient2 = p.Patient(patient_name='patient a', illness='diabetes',
                              organ_needed=p.Patient.KIDNEY, blood_type=p.Patient.AB_POS,
                              priority=100, location=1)

    assert p.Patient.patient_count is 2

    assert test_patient1.patient_id is 1
    assert test_patient2.patient_id is 2


def test_organ_category_name():
    assert p.Patient.organ_category_name(-1) is None
    assert p.Patient.organ_category_name(0) is 'Heart'
    assert p.Patient.organ_category_name(1) is 'Kidney'
    assert p.Patient.organ_category_name(2) is 'Liver'
    assert p.Patient.organ_category_name(3) is 'Lung'
    assert p.Patient.organ_category_name(4) is 'Pancreas'
    assert p.Patient.organ_category_name(5) is 'Intestines'
    assert p.Patient.organ_category_name(6) is 'Thymus'
    assert p.Patient.organ_category_name(7) is None
