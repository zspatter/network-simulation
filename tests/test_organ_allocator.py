import network_simulator.Dijkstra as d
import network_simulator.Network as net
import network_simulator.Organ as o
import network_simulator.OrganAllocator as oA
import network_simulator.OrganList as oL
import network_simulator.Patient as p
import network_simulator.WaitList as wL
from network_simulator.BloodType import BloodType
from network_simulator.CompatibilityMarkers import OrganType, BloodTypeLetter, BloodTypePolarity


def test_allocate_organs():
    ab_pos = BloodType(BloodTypeLetter.AB, BloodTypePolarity.POS)
    o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)
    organ_list = oL.OrganList()

    organ1 = o.Organ(OrganType.Pancreas.value, ab_pos, 1, organ_list)
    organ2 = o.Organ(OrganType.Heart.value, o_neg, 1, organ_list)

    wait_list = wL.WaitList()
    patient1 = p.Patient('name', 'illness 1', OrganType.Pancreas.value,
                         ab_pos, 100, 1, wait_list)
    patient2 = p.Patient('name', 'illness 2', OrganType.Pancreas.value,
                         o_neg, 200, 3, wait_list)
    patient3 = p.Patient('name', 'illness 3', OrganType.Heart.value,
                         ab_pos, 100, 2, wait_list)
    patient4 = p.Patient('name', 'illness 4', OrganType.Heart.value,
                         ab_pos, 50, 2, wait_list)

    node1 = net.Node(1, adjacency_dict={2: {'weight': 10, 'status': True},
                                        3: {'weight': 25, 'status': True}})
    node2 = net.Node(2, adjacency_dict={3: {'weight': 35, 'status': True}})
    node3 = net.Node(3, {})
    test_net = net.Network({1: node1, 2: node2, 3: node3})

    oA.OrganAllocator.allocate_organs(organ_list, wait_list, test_net)
    assert len(organ_list.organ_list) is 0
    assert len(wait_list.wait_list) is 2
    assert patient2 in wait_list.wait_list
    assert patient4 in wait_list.wait_list


def test_find_best_match():
    ab_pos = BloodType(BloodTypeLetter.AB, BloodTypePolarity.POS)
    o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)
    wait_list = wL.WaitList()

    patient1 = p.Patient('name', 'illness 1', OrganType.Pancreas.value,
                         ab_pos, 100, 1, wait_list)
    patient2 = p.Patient('name', 'illness 2', OrganType.Pancreas.value,
                         ab_pos, 250, 3, wait_list)
    patient3 = p.Patient('name', 'illness 3', OrganType.Pancreas.value,
                         o_neg, 400, 2, wait_list)
    patient4 = p.Patient('name', 'illness 4', OrganType.Heart.value,
                         ab_pos, 500, 2, wait_list)
    organ = o.Organ(OrganType.Pancreas.value, o_neg, 1)

    node1 = net.Node(1, adjacency_dict={2: {'weight': 10, 'status': True},
                                        3: {'weight': 25, 'status': True}})
    node2 = net.Node(2, adjacency_dict={3: {'weight': 35, 'status': True}})
    node3 = net.Node(3, {})
    test_net = net.Network({1: node1, 2: node2, 3: node3})
    weights, paths = d.Dijkstra.dijkstra(test_net, 1)

    patient = oA.OrganAllocator.find_best_match(organ, wait_list, weights)
    assert patient is patient3
    assert len(wait_list.wait_list) is 4

    node1.adjacency_dict[3]['weight'] = 300
    node3.adjacency_dict[1]['weight'] = 300
    test_net.mark_node_inactive(2)
    wait_list.remove_patient(patient3)
    weights, paths = d.Dijkstra.dijkstra(test_net, 1)
    assert len(weights) is 2

    patient = oA.OrganAllocator.find_best_match(organ, wait_list, weights)
    assert patient is patient1
