from network_simulator.BloodType import BloodType
from network_simulator.CompatibilityMarkers import OrganType, BloodTypeLetter, BloodTypePolarity
from network_simulator.Dijkstra import Dijkstra
from network_simulator.Network import Node, Network
from network_simulator.Organ import Organ
from network_simulator.OrganAllocator import OrganAllocator
from network_simulator.OrganList import OrganList
from network_simulator.Patient import Patient
from network_simulator.WaitList import WaitList


def test_allocate_organs():
    ab_pos = BloodType(BloodTypeLetter.AB, BloodTypePolarity.POS)
    o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)
    organ_list = OrganList()
    
    organ1 = Organ(OrganType.Pancreas.value, ab_pos, 1, organ_list)
    organ2 = Organ(OrganType.Heart.value, o_neg, 1, organ_list)
    
    wait_list = WaitList()
    patient1 = Patient('name', 'illness 1', OrganType.Pancreas.value,
                       ab_pos, 100, 1, wait_list)
    patient2 = Patient('name', 'illness 2', OrganType.Pancreas.value,
                       o_neg, 200, 3, wait_list)
    patient3 = Patient('name', 'illness 3', OrganType.Heart.value,
                       ab_pos, 100, 2, wait_list)
    patient4 = Patient('name', 'illness 4', OrganType.Heart.value,
                       ab_pos, 50, 2, wait_list)
    
    node1 = Node(1, adjacency_dict={2: {'weight': 10, 'status': True},
                                    3: {'weight': 25, 'status': True}})
    node2 = Node(2, adjacency_dict={3: {'weight': 35, 'status': True}})
    node3 = Node(3, {})
    test_net = Network({1: node1, 2: node2, 3: node3})
    
    OrganAllocator.allocate_organs(organ_list, wait_list, test_net)
    assert len(organ_list.organ_list) is 0
    assert len(wait_list.wait_list) is 2
    assert patient2 in wait_list.wait_list
    assert patient4 in wait_list.wait_list


def test_find_best_match():
    ab_pos = BloodType(BloodTypeLetter.AB, BloodTypePolarity.POS)
    o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)
    wait_list = WaitList()
    
    patient1 = Patient('name', 'illness 1', OrganType.Pancreas.value,
                       ab_pos, 100, 1, wait_list)
    patient2 = Patient('name', 'illness 2', OrganType.Pancreas.value,
                       ab_pos, 250, 3, wait_list)
    patient3 = Patient('name', 'illness 3', OrganType.Pancreas.value,
                       o_neg, 400, 2, wait_list)
    patient4 = Patient('name', 'illness 4', OrganType.Heart.value,
                       ab_pos, 500, 2, wait_list)
    organ = Organ(OrganType.Pancreas.value, o_neg, 1)
    
    node1 = Node(1, adjacency_dict={2: {'weight': 10, 'status': True},
                                    3: {'weight': 25, 'status': True}})
    node2 = Node(2, adjacency_dict={3: {'weight': 35, 'status': True}})
    node3 = Node(3, {})
    test_net = Network({1: node1, 2: node2, 3: node3})
    weights, paths = Dijkstra.dijkstra(test_net, 1)
    
    patient = OrganAllocator.find_best_match(organ, wait_list, weights)
    assert patient is patient3
    assert len(wait_list.wait_list) is 4
    
    node1.adjacency_dict[3]['weight'] = 300
    node3.adjacency_dict[1]['weight'] = 300
    test_net.mark_node_inactive(2)
    wait_list.remove_patient(patient3)
    weights, paths = Dijkstra.dijkstra(test_net, 1)
    assert len(weights) is 2
    
    patient = OrganAllocator.find_best_match(organ, wait_list, weights)
    assert patient is patient1
