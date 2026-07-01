from network_simulator.allocation.feasibility import feasible_matches_by_organ
from network_simulator.BloodType import BloodType
from network_simulator.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from network_simulator.Network import Network
from network_simulator.Node import Node
from network_simulator.Organ import Organ
from network_simulator.OrganList import OrganList
from network_simulator.Patient import Patient
from network_simulator.WaitList import WaitList

o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)
ab_pos = BloodType(BloodTypeLetter.AB, BloodTypePolarity.POS)


def _network(weight: float = 1.0) -> Network:
    node1 = Node(1, adjacency_dict={2: {'weight': weight, 'status': True}})
    node2 = Node(2, adjacency_dict={1: {'weight': weight, 'status': True}})
    return Network({1: node1, 2: node2})


def test_feasible_matches_filters_by_organ_type_and_blood_type():
    network = _network()
    organ_list = OrganList()
    # AB+ is a restrictive donor type (only AB+ recipients can accept it),
    # unlike O- (universal donor)
    organ = Organ(OrganType.Kidney, ab_pos, location=1, organ_list=organ_list)

    wait_list = WaitList()
    matching_patient = Patient('match', 'n/a', OrganType.Kidney, ab_pos, 100, 2, wait_list)
    Patient('wrong organ', 'n/a', OrganType.Liver, ab_pos, 100, 2, wait_list)
    Patient('wrong blood', 'n/a', OrganType.Kidney, o_neg, 100, 2, wait_list)

    matches = feasible_matches_by_organ(organ_list, wait_list, network)
    feasible_patients = [patient for patient, _ in matches[organ]]

    assert feasible_patients == [matching_patient]


def test_feasible_matches_respects_operation_buffer():
    # Heart: viability 6h, operation buffer 5h -> only ~1h of transit budget remains
    organ_list = OrganList()

    close_network = _network(weight=1.0)
    close_organ = Organ(OrganType.Heart, o_neg, location=1, organ_list=organ_list)
    wait_list = WaitList()
    close_patient = Patient('close', 'n/a', OrganType.Heart, o_neg, 100, 2, wait_list)

    matches = feasible_matches_by_organ(organ_list, wait_list, close_network)
    assert (close_patient, 1.0) in matches[close_organ]

    far_network = _network(weight=3.0)
    matches = feasible_matches_by_organ(organ_list, wait_list, far_network)
    feasible_patients = [patient for patient, _ in matches[close_organ]]
    assert close_patient not in feasible_patients


def test_feasible_matches_returns_empty_list_for_organ_with_no_candidates():
    network = _network()
    organ_list = OrganList()
    organ = Organ(OrganType.Pancreas, o_neg, location=1, organ_list=organ_list)
    wait_list = WaitList()

    matches = feasible_matches_by_organ(organ_list, wait_list, network)
    assert matches[organ] == []
