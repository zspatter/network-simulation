import network_simulator.Patient as p
import network_simulator.Organ as o


def test__init__():
    test_patient1 = p.Patient(patient_name='patient a', illness='diabetes',
                              organ_needed=o.Organ.KIDNEY, wait_time=100, location=1)
    test_patient2 = p.Patient(patient_name='patient a', illness='diabetes',
                              organ_needed=o.Organ.KIDNEY, wait_time=100, location=1)

    assert p.Patient.patient_count is 2

    assert test_patient1.patient_id is 1
    assert test_patient2.patient_id is 2
