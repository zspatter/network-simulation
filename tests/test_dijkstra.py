import network_simulator.Dijkstra as d
import network_simulator.Network as net


def test_dijkstra():
    test_node1 = net.Node(node_id=1, adjacency_dict={2: {'weight': 5, 'status': True}})
    test_node2 = net.Node(node_id=2, adjacency_dict={3: {'weight': 5, 'status': True}})
    test_node3 = net.Node(node_id=3)
    test_node4 = net.Node(node_id=4)
    test_net = net.Network({test_node1.node_id: test_node1,
                            test_node2.node_id: test_node2,
                            test_node3.node_id: test_node3,
                            test_node4.node_id: test_node4})

    weight, previous = d.Dijkstra.dijkstra(graph=test_net, source=1)
    assert weight[1] is 0
    assert weight[2] is 5
    assert weight[3] is 10
    assert weight[4] == float('inf')
    assert previous[1] is None
    assert previous[2] is 1
    assert previous[3] is 2
    assert previous[4] is None


def test_minimum_unvisited_distance():
    unvisited = [1, 2, 3, 4, 5]
    weight = dict.fromkeys(unvisited, float('inf'))

    assert d.Dijkstra.minimum_unvisited_distance(unvisited, weight) is 1
    weight[2] = 0
    assert d.Dijkstra.minimum_unvisited_distance(unvisited, weight) is 2
    weight[3] = 3
    weight[5] = 5
    assert d.Dijkstra.minimum_unvisited_distance(unvisited, weight) is 2
    unvisited.remove(2)
    assert d.Dijkstra.minimum_unvisited_distance(unvisited, weight) is 3
    unvisited.remove(3)
    assert d.Dijkstra.minimum_unvisited_distance(unvisited, weight) is 5
    unvisited.remove(5)
    assert d.Dijkstra.minimum_unvisited_distance(unvisited, weight) is 1


def test_shortest_path():
    test_node1 = net.Node(node_id=1, adjacency_dict={2: {'weight': 10, 'status': True}})
    test_node2 = net.Node(node_id=2, adjacency_dict={3: {'weight': 5, 'status': True}})
    test_node3 = net.Node(node_id=3, adjacency_dict={4: {'weight': 3, 'status': True}})
    test_node4 = net.Node(node_id=4, adjacency_dict={1: {'weight': 6, 'status': True}})
    test_node5 = net.Node(node_id=5, adjacency_dict={1: {'weight': 1, 'status': True},
                                                     3: {'weight': 2, 'status': True}})
    test_net = net.Network({test_node1.node_id: test_node1,
                            test_node2.node_id: test_node2,
                            test_node3.node_id: test_node3,
                            test_node4.node_id: test_node4,
                            test_node5.node_id: test_node5})

    dijkstra = d.Dijkstra(graph=test_net, source=test_node1.node_id)
    path, weight = dijkstra.shortest_path(destination=test_node3.node_id)
    assert path == [1, 5, 3]
    assert weight is 3

    test_net.remove_node(test_node5.node_id)
    dijkstra = d.Dijkstra(graph=test_net, source=test_node1.node_id)
    path, weight = dijkstra.shortest_path(destination=test_node3.node_id)
    assert path == [1, 4, 3]
    assert weight is 9

    test_net.remove_node(test_node4.node_id)
    dijkstra = d.Dijkstra(graph=test_net, source=test_node1.node_id)
    path, weight = dijkstra.shortest_path(destination=test_node3.node_id)
    assert path == [1, 2, 3]
    assert weight is 15

    test_net.remove_node(test_node2.node_id)
    dijkstra = d.Dijkstra(graph=test_net, source=test_node1.node_id)
    path, weight = dijkstra.shortest_path(destination=test_node3.node_id)
    assert path is None
    assert weight == float('inf')


def test_all_shortest_paths():
    test_node1 = net.Node(node_id=1, adjacency_dict={2: {'weight': 10, 'status': True}})
    test_node2 = net.Node(node_id=2, adjacency_dict={3: {'weight': 5, 'status': True},
                                                     4: {'weight': 10, 'status': True},
                                                     5: {'weight': 15, 'status': True}})
    test_node3 = net.Node(node_id=3)
    test_node4 = net.Node(node_id=4)
    test_node5 = net.Node(node_id=5)
    test_net = net.Network({test_node1.node_id: test_node1,
                            test_node2.node_id: test_node2,
                            test_node3.node_id: test_node3,
                            test_node4.node_id: test_node4,
                            test_node5.node_id: test_node5})

    dijkstra = d.Dijkstra(graph=test_net, source=test_node1.node_id)
    shortest_paths = dijkstra.all_shortest_paths()
    assert shortest_paths[1] == ([1], 0)
    assert shortest_paths[2] == ([1, 2], 10)
    assert shortest_paths[3] == ([1, 2, 3], 15)
    assert shortest_paths[4] == ([1, 2, 4], 20)
    assert shortest_paths[5] == ([1, 2, 5], 25)
