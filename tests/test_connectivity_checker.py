import network_simulator.ConnectivityChecker as cC
import network_simulator.Network as net


def test_is_connected():
    test_net = net.Network()
    test_net.add_node(net.Node(1))

    assert cC.ConnectivityChecker.is_connected(test_net)

    test_net.add_node(net.Node(2))
    assert not cC.ConnectivityChecker.is_connected(test_net)

    test_net.add_edge(node_id1=1, node_id2=2, weight=5)
    assert cC.ConnectivityChecker.is_connected(test_net)


def test_depth_first_search():
    test_net = net.Network()
    test_net.add_node(net.Node(1))

    assert cC.ConnectivityChecker.depth_first_search(test_net)

    test_net.add_node(net.Node(2))
    assert not cC.ConnectivityChecker.depth_first_search(test_net)

    test_net.add_edge(node_id1=1, node_id2=2, weight=5)
    assert cC.ConnectivityChecker.depth_first_search(test_net)


def test_breadth_first_search():
    test_net = net.Network()
    test_net.add_node(net.Node(1))

    assert cC.ConnectivityChecker.breadth_first_search(test_net)

    test_net.add_node(net.Node(2))
    assert not cC.ConnectivityChecker.breadth_first_search(test_net)

    test_net.add_edge(node_id1=1, node_id2=2, weight=5)
    assert cC.ConnectivityChecker.breadth_first_search(test_net)
