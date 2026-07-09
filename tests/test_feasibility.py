from organflow.allocation.feasibility import feasible_matches_by_organ
from organflow.BloodType import BloodType
from organflow.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from organflow.Network import Network
from organflow.Node import Node
from organflow.Organ import Organ
from organflow.OrganList import OrganList
from organflow.Patient import Patient
from organflow.WaitList import WaitList

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
    # Heart: viability 6h, operation buffer 1.5h -> 4.5h of transit budget remains
    organ_list = OrganList()

    close_network = _network(weight=1.0)
    close_organ = Organ(OrganType.Heart, o_neg, location=1, organ_list=organ_list)
    wait_list = WaitList()
    close_patient = Patient('close', 'n/a', OrganType.Heart, o_neg, 100, 2, wait_list)

    matches = feasible_matches_by_organ(organ_list, wait_list, close_network)
    assert (close_patient, 1.0) in matches[close_organ]

    # 5h transit exceeds the 4.5h budget (6h viability - 1.5h operation buffer)
    far_network = _network(weight=5.0)
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


def test_feasible_matches_excludes_positive_crossmatch_kidney_patient():
    network = _network()
    organ_list = OrganList()
    organ = Organ(OrganType.Kidney, o_neg, location=1, organ_list=organ_list,
                  hla_antigens=frozenset({4, 5}))

    wait_list = WaitList()
    compatible = Patient('crossmatch neg', 'n/a', OrganType.Kidney, o_neg, 100, 2, wait_list,
                         unacceptable_antigens=frozenset({9}))
    Patient('crossmatch pos', 'n/a', OrganType.Kidney, o_neg, 100, 2, wait_list,
            unacceptable_antigens=frozenset({5}))

    matches = feasible_matches_by_organ(organ_list, wait_list, network)[organ]
    feasible_patients = [p for p, _ in matches]
    assert feasible_patients == [compatible]


def test_feasible_matches_excludes_size_mismatched_heart_patient():
    network = _network()
    organ_list = OrganList()
    # small donor heart; viability 6h - operation buffer 5h leaves 1h, transit is 1h
    # (feasible on time)
    organ = Organ(OrganType.Heart, o_neg, location=1, organ_list=organ_list, donor_size=55.0)

    wait_list = WaitList()
    size_matched = Patient('size ok', 'n/a', OrganType.Heart, o_neg, 100, 2, wait_list,
                           body_size=60.0)
    Patient('too large', 'n/a', OrganType.Heart, o_neg, 100, 2, wait_list, body_size=110.0)

    matches = feasible_matches_by_organ(organ_list, wait_list, network)[organ]
    feasible_patients = [p for p, _ in matches]
    assert feasible_patients == [size_matched]
