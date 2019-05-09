from network_simulator.ConnectivityChecker import ConnectivityChecker
from network_simulator.Network import Node, Network


def test_is_connected():
    test_net = Network()
    test_net.add_node(Node(1))
    
    assert ConnectivityChecker.is_connected(test_net)
    
    test_net.add_node(Node(2))
    assert not ConnectivityChecker.is_connected(test_net)
    
    test_net.add_edge(node_id1=1, node_id2=2, weight=5)
    assert ConnectivityChecker.is_connected(test_net)


def test_depth_first_search():
    test_net = Network()
    test_net.add_node(Node(1))
    
    assert ConnectivityChecker.depth_first_search(test_net)
    
    test_net.add_node(Node(2))
    assert not ConnectivityChecker.depth_first_search(test_net)
    
    test_net.add_edge(node_id1=1, node_id2=2, weight=5)
    assert ConnectivityChecker.depth_first_search(test_net)


def test_breadth_first_search():
    test_net = Network()
    test_net.add_node(Node(1))
    
    assert ConnectivityChecker.breadth_first_search(test_net)
    
    test_net.add_node(Node(2))
    assert not ConnectivityChecker.breadth_first_search(test_net)
    
    test_net.add_edge(node_id1=1, node_id2=2, weight=5)
    assert ConnectivityChecker.breadth_first_search(test_net)
