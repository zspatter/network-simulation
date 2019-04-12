import network_simulator.Organ as o
import network_simulator.Patient as p
import network_simulator.Network as net
import network_simulator.WaitList as wl
import network_simulator.OrganList as ol
import network_simulator.OrganAllocator as oa
import network_simulator.Dijkstra as d


def test_allocate_organs():
    organ_list = ol.OrganList()
    organ1 = o.Organ(o.Organ.PANCREAS, o.Organ.AB_POS, 3, organ_list)
    organ2 = o.Organ(o.Organ.HEART, o.Organ.O_NEG, 3, organ_list)

    wait_list = wl.WaitList()
    patient1 = p.Patient('name', 'illness 1', p.Patient.PANCREAS,
                         p.Patient.AB_POS, 100, 1, wait_list)
    patient2 = p.Patient('name', 'illness 2', p.Patient.PANCREAS,
                         p.Patient.O_NEG, 200, 3, wait_list)
    patient3 = p.Patient('name', 'illness 3', p.Patient.HEART,
                         p.Patient.AB_POS, 100, 2, wait_list)
    patient4 = p.Patient('name', 'illness 4', p.Patient.HEART,
                         p.Patient.AB_POS, 50, 2, wait_list)

    node1 = net.Node(1, adjacency_dict={2: {'weight': 10, 'status': True},
                                        3: {'weight': 25, 'status': True}})
    node2 = net.Node(2, adjacency_dict={3: {'weight': 35, 'status': True}})
    node3 = net.Node(3, {})
    test_net = net.Network({1: node1, 2: node2, 3: node3})

    oa.OrganAllocator.allocate_organs(organ_list, wait_list, test_net)
    assert len(organ_list.organ_list) is 0
    assert len (wait_list.wait_list) is 2
    assert patient2 in wait_list.wait_list
    assert patient4 in wait_list.wait_list


def test_find_best_match():
    wait_list = wl.WaitList()
    patient1 = p.Patient('name', 'illness 1', p.Patient.PANCREAS,
                         p.Patient.AB_POS, 100, 1, wait_list)
    patient2 = p.Patient('name', 'illness 2', p.Patient.PANCREAS,
                         p.Patient.AB_POS, 250, 3, wait_list)
    patient3 = p.Patient('name', 'illness 3', p.Patient.PANCREAS,
                         p.Patient.O_NEG, 400, 2, wait_list)
    patient4 = p.Patient('name', 'illness 4', p.Patient.HEART,
                         p.Patient.AB_POS, 500, 2, wait_list)
    organ = o.Organ(o.Organ.PANCREAS, o.Organ.AB_POS, 1)

    node1 = net.Node(1, adjacency_dict={2: {'weight': 10, 'status': True},
                                        3: {'weight': 25, 'status': True}})
    node2 = net.Node(2, adjacency_dict={3: {'weight': 35, 'status': True}})
    node3 = net.Node(3, {})
    test_net = net.Network({1: node1, 2: node2, 3: node3})
    weights, paths = d.Dijkstra.dijkstra(test_net, 1)

    patient = oa.OrganAllocator.find_best_match(organ, wait_list, weights)
    assert patient is patient2

    node1.adjacency_dict[3]['weight'] = 300
    node3.adjacency_dict[1]['weight'] = 300
    test_net.mark_node_inactive(2)
    weights, paths = d.Dijkstra.dijkstra(test_net, 1)
    assert len(weights) is 2

    patient = oa.OrganAllocator.find_best_match(organ, wait_list, weights)
    assert patient is patient1

