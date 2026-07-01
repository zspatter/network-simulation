from network_simulator.allocation.matchers.greedy import GreedyMatcher
from network_simulator.allocation.scoring import PriorityScore
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
