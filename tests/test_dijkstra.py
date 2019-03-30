import network_simulator.Node as n
import network_simulator.Network as net
import network_simulator.Dijkstra as d


def test_is_connected():
    test_net = net.Network()
    test_net.add_node(n.Node(1))
    test_dijkstra = d.Dijkstra(graph=test_net, source=1)

    assert test_dijkstra.is_connected(test_net)

    test_net.add_node(n.Node(2))
    assert not test_dijkstra.is_connected(test_net)

    test_net.add_edge(node_id1=1, node_id2=2, weight=5)
    assert test_dijkstra.is_connected(test_net)


def test_DFS():
    test_net = net.Network()
    test_net.add_node(n.Node(1))
    test_dijkstra = d.Dijkstra(graph=test_net, source=1)

    assert test_dijkstra.DFS(test_net)

    test_net.add_node(n.Node(2))
    assert not test_dijkstra.DFS(test_net)

    test_net.add_edge(node_id1=1, node_id2=2, weight=5)
    assert test_dijkstra.DFS(test_net)


def test_BFS():
    test_net = net.Network()
    test_net.add_node(n.Node(1))
    test_dijkstra = d.Dijkstra(graph=test_net, source=1)

    assert test_dijkstra.BFS(test_net)

    test_net.add_node(n.Node(2))
    assert not test_dijkstra.BFS(test_net)

    test_net.add_edge(node_id1=1, node_id2=2, weight=5)
    assert test_dijkstra.BFS(test_net)
