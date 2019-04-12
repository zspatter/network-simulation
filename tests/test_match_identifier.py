import network_simulator.Patient as p
import network_simulator.Organ as o
import network_simulator.MatchIdentifier as mI


def test_is_match():
    patient = p.Patient(patient_name="name",
                        illness="illness",
                        organ_needed=p.Patient.PANCREAS,
                        blood_type=p.Patient.O_NEG,
                        priority=100,
                        location=1)
    organ = o.Organ(organ_type=o.Organ.PANCREAS,
                    blood_type=o.Organ.O_NEG,
                    location=1)

    assert mI.MatchIdentifier.is_match(patient=patient, organ=organ)

    patient.blood_type = p.Patient.O_POS
    assert mI.MatchIdentifier.is_match(patient=patient, organ=organ)

    patient.blood_type = p.Patient.AB_POS
    assert mI.MatchIdentifier.is_match(patient=patient, organ=organ)

    organ.blood_type = o.Organ.AB_POS
    patient.blood_type = p.Patient.AB_NEG
    assert not mI.MatchIdentifier.is_match(patient=patient, organ=organ)

    organ.blood_type = o.Organ.A_NEG
    assert mI.MatchIdentifier.is_match(patient=patient, organ=organ)

    organ.blood_type = o.Organ.O_NEG
    patient.blood_type = p.Patient.A_NEG
    assert mI.MatchIdentifier.is_match(patient=patient, organ=organ)

    organ.blood_type = o.Organ.B_NEG
    patient.blood_type = p.Patient.A_NEG
    assert not mI.MatchIdentifier.is_match(patient=patient, organ=organ)
