import time

from network_simulator.allocation.matchers.optimal import OptimalMatcher
from network_simulator.allocation.scoring import CompositeScore, PriorityScore, ScoreWeights
from network_simulator.BloodType import BloodType
from network_simulator.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from network_simulator.Network import Network
from network_simulator.Node import Node
from network_simulator.Organ import Organ
from network_simulator.OrganList import OrganList
from network_simulator.Patient import Patient
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


def test_optimal_matcher_excludes_non_positive_scored_candidates_from_the_graph():
    # feasible (blood/organ type compatible, within viability), but a large
    # negative geography penalty drives the composite score to <= 0 - such
    # a candidate should be excluded from the matching graph entirely,
    # leaving the organ unmatched rather than "matched" at a net-negative value
    o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)
    node1 = Node(1, adjacency_dict={2: {'weight': 5.0, 'status': True}})
    node2 = Node(2, adjacency_dict={1: {'weight': 5.0, 'status': True}})
    network = Network({1: node1, 2: node2})

    organ_list = OrganList()
    organ = Organ(OrganType.Kidney, o_neg, location=1, organ_list=organ_list)

    wait_list = WaitList()
    Patient('far, no priority', 'n/a', OrganType.Kidney, o_neg, 0, 2, wait_list)

    scorer = CompositeScore(weights=ScoreWeights(urgency=1.0, wait_time=2.0, geography=-1.0))
    result = OptimalMatcher().allocate(organ_list, wait_list, network, scorer)

    assert result.matches == []
    assert result.unmatched_organs == [organ]


def test_optimal_matcher_uses_provided_feasibility_instead_of_recomputing():
    # organ_a would normally see both patients (patient_x scores higher) - an explicit
    # feasibility override restricting it to patient_y only should be honored as-is,
    # confirming a caller like TieredMatcher can safely narrow candidates per tier
    organ_list, wait_list, network, organ_a, organ_b, patient_x, patient_y = build_scenario()
    feasibility = {organ_a: [(patient_y, 0.0)], organ_b: []}

    result = OptimalMatcher().allocate(organ_list, wait_list, network, PriorityScore(),
                                       feasibility=feasibility)

    assert result.matches == [(organ_a, patient_y)]
    assert organ_b in result.unmatched_organs


def test_optimal_matcher_solves_a_large_multi_organ_type_batch_quickly():
    # regression test: OptimalMatcher previously solved one global nx.max_weight_matching
    # over every organ, which both took minutes and could crash outright once a candidate
    # pool reached tens of thousands (measured directly against the real national-scale
    # network). This exercises two organ types at once, at a scale far beyond the other
    # fixtures here, and asserts it stays fast.
    o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)
    network = Network({1: Node(1)})
    organ_list = OrganList()
    wait_list = WaitList()

    for _ in range(50):
        Organ(OrganType.Kidney, o_neg, location=1, organ_list=organ_list)
    for _ in range(20):
        Organ(OrganType.Heart, o_neg, location=1, organ_list=organ_list)
    for i in range(3000):
        Patient(f'kidney patient {i}', 'n/a', OrganType.Kidney, o_neg, i, 1, wait_list)
    for i in range(500):
        Patient(f'heart patient {i}', 'n/a', OrganType.Heart, o_neg, i, 1, wait_list)

    start = time.perf_counter()
    result = OptimalMatcher().allocate(organ_list, wait_list, network, PriorityScore())
    elapsed = time.perf_counter() - start

    assert elapsed < 10.0
    assert len(result.matches) == 70  # every organ finds a candidate (ample supply of both)
    kidney_organs = {organ.organ_id for organ in organ_list.organ_list
                    if organ.organ_type is OrganType.Kidney}
    for organ, patient in result.matches:
        # organ types never cross-match - each organ's candidate is the same organ type
        assert (organ.organ_id in kidney_organs) == (patient.organ_needed is OrganType.Kidney)
