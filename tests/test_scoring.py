from network_simulator.allocation.scoring import CompositeScore, PriorityScore, ScoreWeights
from network_simulator.BloodType import BloodType
from network_simulator.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from network_simulator.Organ import Organ
from network_simulator.Patient import Patient

o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)


def test_priority_score_returns_patient_priority():
    patient = Patient('name', 'n/a', OrganType.Kidney, o_neg, 250, 1)
    organ = Organ(OrganType.Kidney, o_neg, location=1)

    assert PriorityScore().score(patient, organ, transit_hours=3.0) == 250.0


def test_composite_score_combines_urgency_wait_time_and_geography():
    patient = Patient('name', 'n/a', OrganType.Kidney, o_neg, 100, 1)
    patient.rounds_waited = 4
    organ = Organ(OrganType.Kidney, o_neg, location=1)

    weights = ScoreWeights(urgency=1.0, wait_time=2.0, geography=-0.5)
    score = CompositeScore(weights=weights).score(patient, organ, transit_hours=6.0)

    assert score == 1.0 * 100 + 2.0 * 4 - 0.5 * 6.0


def test_composite_score_prefers_longer_waited_patient_when_priority_ties():
    organ = Organ(OrganType.Kidney, o_neg, location=1)
    scorer = CompositeScore()

    patient_a = Patient('a', 'n/a', OrganType.Kidney, o_neg, 100, 1)
    patient_a.rounds_waited = 1
    patient_b = Patient('b', 'n/a', OrganType.Kidney, o_neg, 100, 1)
    patient_b.rounds_waited = 10

    assert scorer.score(patient_b, organ, 0.0) > scorer.score(patient_a, organ, 0.0)
