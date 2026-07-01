from network_simulator.allocation.matchers.optimal import OptimalMatcher
from network_simulator.allocation.scoring import PriorityScore
from network_simulator.BloodType import BloodType
from network_simulator.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from network_simulator.Network import Network
from network_simulator.Node import Node
from network_simulator.Organ import Organ
from network_simulator.OrganList import OrganList
from network_simulator.WaitList import WaitList
from tests.allocation_scenarios import build_scenario


def test_optimal_matcher_avoids_the_greedy_processing_order_pitfall():
    organ_list, wait_list, network, organ_a, organ_b, patient_x, patient_y = build_scenario()

    result = OptimalMatcher().allocate(organ_list, wait_list, network, PriorityScore())

    assert len(result.matches) == 2
    assert len(result.unmatched_organs) == 0

    total_score = sum(patient.priority for _, patient in result.matches)
    assert total_score == 110  # beats greedy's 100 (organ B would otherwise go unmatched)


def test_optimal_matcher_leaves_infeasible_organ_unmatched():
    network = Network({1: Node(1)})
    organ_list = OrganList()
    o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)
    organ = Organ(OrganType.Pancreas, o_neg, location=1, organ_list=organ_list)
    wait_list = WaitList()

    result = OptimalMatcher().allocate(organ_list, wait_list, network, PriorityScore())

    assert result.matches == []
    assert result.unmatched_organs == [organ]
