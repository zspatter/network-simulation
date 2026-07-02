from network_simulator.allocation.geography import national_tier, region_tier
from network_simulator.allocation.matchers.greedy import GreedyMatcher
from network_simulator.allocation.matchers.tiered import TieredMatcher
from network_simulator.allocation.scoring import PriorityScore
from network_simulator.BloodType import BloodType
from network_simulator.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from network_simulator.Network import Network
from network_simulator.Node import Node
from network_simulator.Organ import Organ
from network_simulator.OrganList import OrganList
from network_simulator.Patient import Patient
from network_simulator.WaitList import WaitList

o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)


def _build_cross_region_scenario():
    """
    Organ at node 1 (region 1). patient_local (region 1) has lower priority than
    patient_far (region 2) - so an unconstrained scorer prefers patient_far, but a
    region-tiered matcher should only ever consider patient_far if no tier-0 candidate
    exists.
    """
    node1 = Node(1, region=1, adjacency_dict={2: {'weight': 1.0, 'status': True},
                                              3: {'weight': 2.0, 'status': True}})
    node2 = Node(2, region=1, adjacency_dict={1: {'weight': 1.0, 'status': True}})
    node3 = Node(3, region=2, adjacency_dict={1: {'weight': 2.0, 'status': True}})
    network = Network({1: node1, 2: node2, 3: node3})

    organ_list = OrganList()
    organ = Organ(OrganType.Kidney, o_neg, location=1, organ_list=organ_list)

    wait_list = WaitList()
    patient_local = Patient('local', 'n/a', OrganType.Kidney, o_neg, 10, 2, wait_list)
    patient_far = Patient('far, higher priority', 'n/a', OrganType.Kidney,
                          o_neg, 100, 3, wait_list)

    return organ_list, wait_list, network, organ, patient_local, patient_far


def test_region_tier_matches_the_local_candidate_even_though_a_farther_one_scores_higher():
    organ_list, wait_list, network, organ, patient_local, patient_far = \
        _build_cross_region_scenario()

    matcher = TieredMatcher(GreedyMatcher(), region_tier)
    result = matcher.allocate(organ_list, wait_list, network, PriorityScore())

    assert result.matches == [(organ, patient_local)]


def test_without_a_tier_constraint_the_higher_scoring_farther_candidate_wins():
    organ_list, wait_list, network, organ, patient_local, patient_far = \
        _build_cross_region_scenario()

    result = GreedyMatcher().allocate(organ_list, wait_list, network, PriorityScore())

    assert result.matches == [(organ, patient_far)]


def test_national_tier_reproduces_the_unwrapped_matcher():
    organ_list, wait_list, network, organ, patient_local, patient_far = \
        _build_cross_region_scenario()

    matcher = TieredMatcher(GreedyMatcher(), national_tier)
    result = matcher.allocate(organ_list, wait_list, network, PriorityScore())

    assert result.matches == [(organ, patient_far)]


def test_tiered_matcher_expands_to_a_farther_tier_when_no_local_candidate_exists():
    node1 = Node(1, region=1, adjacency_dict={3: {'weight': 2.0, 'status': True}})
    node3 = Node(3, region=2, adjacency_dict={1: {'weight': 2.0, 'status': True}})
    network = Network({1: node1, 3: node3})

    organ_list = OrganList()
    organ = Organ(OrganType.Kidney, o_neg, location=1, organ_list=organ_list)
    wait_list = WaitList()
    patient_far = Patient('far', 'n/a', OrganType.Kidney, o_neg, 100, 3, wait_list)

    matcher = TieredMatcher(GreedyMatcher(), region_tier)
    result = matcher.allocate(organ_list, wait_list, network, PriorityScore())

    assert result.matches == [(organ, patient_far)]


def test_tiered_matcher_leaves_an_organ_unmatched_if_no_candidate_exists_at_any_tier():
    network = Network({1: Node(1, region=1)})
    organ_list = OrganList()
    organ = Organ(OrganType.Kidney, o_neg, location=1, organ_list=organ_list)
    wait_list = WaitList()

    matcher = TieredMatcher(GreedyMatcher(), region_tier)
    result = matcher.allocate(organ_list, wait_list, network, PriorityScore())

    assert result.matches == []
    assert result.unmatched_organs == [organ]
