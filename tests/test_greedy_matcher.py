from organflow.allocation.matchers.greedy import GreedyMatcher
from organflow.allocation.scoring import PriorityScore
from tests.allocation_scenarios import build_scenario


def test_greedy_matcher_can_be_led_astray_by_processing_order():
    organ_list, wait_list, network, organ_a, organ_b, patient_x, patient_y = build_scenario()

    result = GreedyMatcher().allocate(organ_list, wait_list, network, PriorityScore())

    assert (organ_a, patient_x) in result.matches
    assert organ_b in result.unmatched_organs
    assert len(result.matches) == 1


def test_greedy_matcher_does_not_double_match_a_patient():
    organ_list, wait_list, network, organ_a, organ_b, patient_x, patient_y = build_scenario()

    result = GreedyMatcher().allocate(organ_list, wait_list, network, PriorityScore())

    matched_patients = [patient for _, patient in result.matches]
    assert len(matched_patients) == len(set(matched_patients))


def test_greedy_matcher_uses_provided_feasibility_instead_of_recomputing():
    # organ_a would normally see both patients (patient_x scores higher) - an explicit
    # feasibility override restricting it to patient_y only should be honored as-is,
    # confirming a caller like TieredMatcher can safely narrow candidates per tier
    organ_list, wait_list, network, organ_a, organ_b, patient_x, patient_y = build_scenario()
    feasibility = {organ_a: [(patient_y, 0.0)], organ_b: []}

    result = GreedyMatcher().allocate(organ_list, wait_list, network, PriorityScore(),
                                      feasibility=feasibility)

    assert result.matches == [(organ_a, patient_y)]
    assert organ_b in result.unmatched_organs
