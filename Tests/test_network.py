import Network_Simulator.Node as n
import Network_Simulator.Network as net


def test_add_node():
    node1 = n.Node(1)
    test_net = net.Network()

    assert len(test_net.nodes()) is 0
    test_net.add_node(node1)
    assert len(test_net.nodes()) is 1
    assert node1.node_id in test_net.nodes()


def test_add_edge():
    node1 = n.Node(1)
    node2 = n.Node(2)
    test_net = net.Network()

    test_net.add_node(node1)
    test_net.add_node(node2)
    assert len(test_net.network_dict[node1.node_id].get_adjacents()) is 0

    test_net.add_edge(node1.node_id, node2.node_id, 5)
    assert len(test_net.network_dict[node1.node_id].get_adjacents()) is 1
    assert test_net.network_dict[node1.node_id].adjacency_dict[node2.node_id]['weight'] is 5


def test_is_connected():
    test_net = net.Network()
    test_net.add_node(n.Node(1))

    assert test_net.is_connected()

    test_net.add_node(n.Node(2))
    assert not test_net.is_connected()

    test_net.add_edge(1, 2, 5)
    assert test_net.is_connected()


def test_DFS():
    test_net = net.Network()
    test_net.add_node(n.Node(1))

    assert test_net.DFS()

    test_net.add_node(n.Node(2))
    assert not test_net.DFS()

    test_net.add_edge(1, 2, 5)
    assert test_net.DFS()


def test_BFS():
    test_net = net.Network()
    test_net.add_node(n.Node(1))

    assert test_net.BFS()

    test_net.add_node(n.Node(2))
    assert not test_net.BFS()

    test_net.add_edge(1, 2, 5)
    assert test_net.BFS()



