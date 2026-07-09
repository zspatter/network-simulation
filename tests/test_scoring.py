from organflow.allocation.scoring import (
    AcuityScore,
    CompositeScore,
    ContinuousDistributionScore,
    PriorityScore,
    RealWorldScore,
    ScoreWeights,
)
from organflow.BloodType import BloodType
from organflow.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from organflow.Organ import Organ
from organflow.Patient import Patient

o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)


def test_priority_score_returns_patient_priority():
    patient = Patient('name', 'n/a', OrganType.Kidney, o_neg, 250, 1)
    organ = Organ(OrganType.Kidney, o_neg, location=1)

    assert PriorityScore().score(patient, organ, transit_hours=3.0) == 250.0


def test_acuity_score_returns_patient_acuity():
    patient = Patient('name', 'n/a', OrganType.Liver, o_neg, 100, 1, acuity=0.73)
    organ = Organ(OrganType.Liver, o_neg, location=1)

    assert AcuityScore().score(patient, organ, transit_hours=3.0) == 0.73


def test_continuous_distribution_proximity_decreases_with_transit():
    patient = Patient('name', 'n/a', OrganType.Kidney, o_neg, 100, 1, acuity=0.5, cpra=0.3)
    patient.rounds_waited = 10
    organ = Organ(OrganType.Kidney, o_neg, location=1)
    scorer = ContinuousDistributionScore()

    near = scorer.score(patient, organ, transit_hours=0.5)
    far = scorer.score(patient, organ, transit_hours=10.0)
    # geography is a continuous term with no hard boundary: closer scores strictly higher,
    # all else equal
    assert near > far


def test_continuous_distribution_zero_proximity_weight_ignores_geography():
    patient = Patient('name', 'n/a', OrganType.Liver, o_neg, 100, 1, acuity=0.6, cpra=0.2)
    organ = Organ(OrganType.Liver, o_neg, location=1)
    scorer = ContinuousDistributionScore(proximity_weight=0.0)

    # with proximity_weight 0, transit does not affect the score at all
    assert scorer.score(patient, organ, 0.5) == scorer.score(patient, organ, 20.0)


def test_continuous_distribution_weights_are_additive_and_comparable():
    patient = Patient('name', 'n/a', OrganType.Heart, o_neg, 100, 1, acuity=1.0, cpra=1.0)
    patient.rounds_waited = 0
    organ = Organ(OrganType.Heart, o_neg, location=1)
    # acuity 1.0 * 100 * medical_weight + proximity(1/(1+0))=1 *100 * proximity + cpra 1*100*sens
    scorer = ContinuousDistributionScore(medical_weight=1.0, wait_weight=0.0,
                                         proximity_weight=1.0, sensitization_weight=1.0)
    assert scorer.score(patient, organ, transit_hours=0.0) == 100.0 + 100.0 + 100.0


def test_composite_score_default_weights_ignore_acuity():
    # acuity coefficient defaults to 0, so legacy composite arithmetic is unchanged
    patient = Patient('name', 'n/a', OrganType.Kidney, o_neg, 100, 1, acuity=0.9)
    patient.rounds_waited = 4
    organ = Organ(OrganType.Kidney, o_neg, location=1)

    weights = ScoreWeights(urgency=1.0, wait_time=2.0, geography=-0.5)
    score = CompositeScore(weights=weights).score(patient, organ, transit_hours=6.0)

    assert score == 1.0 * 100 + 2.0 * 4 - 0.5 * 6.0


def test_composite_score_includes_acuity_term_when_weighted():
    patient = Patient('name', 'n/a', OrganType.Liver, o_neg, 100, 1, acuity=0.8)
    patient.rounds_waited = 4
    organ = Organ(OrganType.Liver, o_neg, location=1)

    weights = ScoreWeights(urgency=1.0, acuity=100.0, wait_time=2.0, geography=-0.5)
    score = CompositeScore(weights=weights).score(patient, organ, transit_hours=6.0)

    assert score == 1.0 * 100 + 100.0 * 0.8 + 2.0 * 4 - 0.5 * 6.0


def test_composite_score_prefers_longer_waited_patient_when_priority_ties():
    organ = Organ(OrganType.Kidney, o_neg, location=1)
    scorer = CompositeScore()

    patient_a = Patient('a', 'n/a', OrganType.Kidney, o_neg, 100, 1)
    patient_a.rounds_waited = 1
    patient_b = Patient('b', 'n/a', OrganType.Kidney, o_neg, 100, 1)
    patient_b.rounds_waited = 10

    assert scorer.score(patient_b, organ, 0.0) > scorer.score(patient_a, organ, 0.0)


def test_real_world_score_kidney_combines_wait_time_and_cpra_tier():
    organ = Organ(OrganType.Kidney, o_neg, location=1)
    patient = Patient('name', 'n/a', OrganType.Kidney, o_neg, 0, 1, cpra=0.995)
    patient.rounds_waited = 3

    assert RealWorldScore().score(patient, organ, transit_hours=0.0) == 3.0 + 50.0


def test_real_world_score_liver_uses_meld_directly():
    organ = Organ(OrganType.Liver, o_neg, location=1)
    patient = Patient('name', 'n/a', OrganType.Liver, o_neg, 0, 1, raw_urgency=25.0)

    assert RealWorldScore().score(patient, organ, transit_hours=0.0) == 25.0


def test_real_world_score_heart_inverts_status_tier_so_higher_means_more_urgent():
    organ = Organ(OrganType.Heart, o_neg, location=1)
    patient = Patient('name', 'n/a', OrganType.Heart, o_neg, 0, 1, raw_urgency=1.0)  # status 1

    assert RealWorldScore().score(patient, organ, transit_hours=0.0) == 6.0  # 7 - 1


def test_real_world_score_lung_uses_las_directly():
    organ = Organ(OrganType.Lungs, o_neg, location=1)
    patient = Patient('name', 'n/a', OrganType.Lungs, o_neg, 0, 1, raw_urgency=80.0)

    assert RealWorldScore().score(patient, organ, transit_hours=0.0) == 80.0


def test_real_world_score_pancreas_falls_back_to_scaled_acuity():
    organ = Organ(OrganType.Pancreas, o_neg, location=1)
    patient = Patient('name', 'n/a', OrganType.Pancreas, o_neg, 0, 1, acuity=0.8)

    assert RealWorldScore().score(patient, organ, transit_hours=0.0) == 8.0  # acuity * 10


def test_real_world_score_floors_native_points_before_the_geography_penalty():
    # a freshly-listed, unsensitized kidney candidate has 0 native points (0 rounds
    # waited, cPRA 0) - without a floor, a distant organ would drive the score to <=0
    # and OptimalMatcher drops any edge with weight <= 0 (see test_optimal_matcher.py)
    organ = Organ(OrganType.Kidney, o_neg, location=1)
    patient = Patient('name', 'n/a', OrganType.Kidney, o_neg, 0, 1)  # rounds_waited=0, cpra=0.0

    assert RealWorldScore().score(patient, organ, transit_hours=25.0) > 0


def test_real_world_score_prefers_the_closer_candidate_when_native_points_tie():
    organ = Organ(OrganType.Liver, o_neg, location=1)
    patient_near = Patient('near', 'n/a', OrganType.Liver, o_neg, 0, 1, raw_urgency=20.0)
    patient_far = Patient('far', 'n/a', OrganType.Liver, o_neg, 0, 1, raw_urgency=20.0)

    scorer = RealWorldScore()
    assert scorer.score(patient_near, organ, transit_hours=1.0) > \
        scorer.score(patient_far, organ, transit_hours=10.0)


def test_real_world_score_gives_pediatric_candidates_a_fixed_bonus():
    from organflow.allocation.scoring import _PEDIATRIC_BONUS
    organ = Organ(OrganType.Liver, o_neg, location=1)
    adult = Patient('adult', 'n/a', OrganType.Liver, o_neg, 0, 1, raw_urgency=20.0)
    child = Patient('child', 'n/a', OrganType.Liver, o_neg, 0, 1, raw_urgency=20.0,
                    is_pediatric=True)

    scorer = RealWorldScore()
    assert scorer.score(child, organ, 2.0) == scorer.score(adult, organ, 2.0) + _PEDIATRIC_BONUS


def test_continuous_distribution_gives_pediatric_candidates_its_pediatric_weight():
    organ = Organ(OrganType.Heart, o_neg, location=1)
    adult = Patient('adult', 'n/a', OrganType.Heart, o_neg, 100, 1, acuity=0.5)
    child = Patient('child', 'n/a', OrganType.Heart, o_neg, 100, 1, acuity=0.5, is_pediatric=True)

    scorer = ContinuousDistributionScore(pediatric_weight=30.0)
    assert scorer.score(child, organ, 1.0) == scorer.score(adult, organ, 1.0) + 30.0
