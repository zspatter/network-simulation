from network_simulator.Network import Node, Network


def test_add_node():
    node1 = Node(1)
    test_net = Network()
    
    # add node to empty graph
    assert len(test_net.nodes()) is 0
    test_net.add_node(node1)
    assert len(test_net.nodes()) is 1
    assert node1.node_id in test_net.nodes()
    
    # attempt to add node that already exists
    test_net.add_node(node1)
    assert len(test_net.nodes()) is 1
    assert node1.node_id in test_net.nodes()


def test_remove_node():
    node1 = Node(1)
    node2 = Node(2)
    test_net = Network({1: node1, 2: node2})
    
    # remove an existing node
    assert len(test_net.nodes()) is 2
    test_net.remove_node(1)
    assert len(test_net.nodes()) is 1
    assert node2.node_id in test_net.network_dict
    
    # remove a node that doesn't exist
    test_net.remove_node(3)
    assert len(test_net.nodes()) is 1
    assert node2.node_id in test_net.network_dict


def test_add_edge():
    node1 = Node(1)
    node2 = Node(2)
    test_net = Network()
    
    # add nodes, but not edges
    test_net.add_node(node1)
    test_net.add_node(node2)
    assert len(test_net.network_dict[node1.node_id].get_adjacents()) is 0
    
    # add edge to existing nodes
    test_net.add_edge(node1.node_id, node2.node_id, 5)
    assert len(test_net.network_dict[node1.node_id].get_adjacents()) is 1
    assert test_net.network_dict[node1.node_id].adjacency_dict[node2.node_id]['weight'] is 5
    
    # attempt to add edge that already exists
    test_net.add_edge(node1.node_id, node2.node_id, 5)
    assert len(test_net.network_dict[node1.node_id].get_adjacents()) is 1
    assert test_net.network_dict[node1.node_id].adjacency_dict[node2.node_id]['weight'] is 5
    
    # add inactive node
    node3 = Node(3, status=False)
    test_net.add_node(node3)
    
    # attempt to add edge to inactive node
    test_net.add_edge(node1.node_id, node3.node_id, 15)
    assert len(test_net.network_dict[node1.node_id].get_adjacents()) is 1
    assert test_net.network_dict[node1.node_id].adjacency_dict[node2.node_id]['weight'] is 5
    
    # attempts to add edge to node that doesn't exist
    test_net.add_edge(node1.node_id, node_id2=4, weight=25)
    assert len(test_net.network_dict[node1.node_id].get_adjacents()) is 1
    assert test_net.network_dict[node1.node_id].adjacency_dict[node2.node_id]['weight'] is 5


def test_remove_edge():
    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': True}})
    node2 = Node(2, adjacency_dict={1: {'weight': 3, 'status': True}})
    node3 = Node(3)
    
    test_net = Network({1: node1, 2: node2})
    
    # test nodes are connected
    assert node2.node_id in node1.adjacency_dict
    assert node1.node_id in node2.adjacency_dict
    
    # remove edge
    test_net.remove_edge(node1.node_id, node2.node_id)
    assert node2.node_id not in node1.adjacency_dict
    assert node1.node_id not in node2.adjacency_dict
    assert not node1.adjacency_dict
    assert not node2.adjacency_dict
    assert len(test_net.network_dict) is 2
    
    # attempt to remove edge with no shared edge
    test_net.remove_edge(node1.node_id, node3.node_id)
    assert not node1.adjacency_dict
    assert not node2.adjacency_dict
    assert len(test_net.network_dict) is 2
    
    # attempt to remove edge from a node that doesn't exist
    test_net.remove_edge(node1.node_id, 4)
    assert not node1.adjacency_dict
    assert not node2.adjacency_dict
    assert len(test_net.network_dict) is 2


def test_mark_node_inactive():
    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': True}})
    node2 = Node(2, adjacency_dict={1: {'weight': 3, 'status': True}})
    test_net = Network({1: node1, 2: node2})
    
    assert len(test_net.network_dict) is len(test_net.nodes())
    assert node2.node_id in test_net.network_dict[node1.node_id].adjacency_dict
    assert node1.node_id in test_net.network_dict[node2.node_id].adjacency_dict
    
    # test marking existing active node as inactive
    test_net.mark_node_inactive(1)
    assert len(test_net.network_dict) is 2
    assert len(test_net.network_dict) is not len(test_net.nodes())
    assert not node1.status
    assert node2.status
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert not node2.adjacency_dict[node1.node_id]['status']
    assert node2.node_id in test_net.network_dict[node1.node_id].adjacency_dict
    assert node1.node_id in test_net.network_dict[node2.node_id].adjacency_dict
    
    # test already inactive node
    test_net.mark_node_inactive(1)
    assert len(test_net.network_dict) is 2
    assert len(test_net.network_dict) is not len(test_net.nodes())
    assert not node1.status
    assert node2.status
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert not node2.adjacency_dict[node1.node_id]['status']
    assert node2.node_id in test_net.network_dict[node1.node_id].adjacency_dict
    assert node1.node_id in test_net.network_dict[node2.node_id].adjacency_dict
    
    # test node that doesn't exist
    test_net.mark_node_inactive(3)
    assert len(test_net.network_dict) is 2
    assert len(test_net.network_dict) is not len(test_net.nodes())


def test_mark_node_active():
    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': True}}, status=False)
    node2 = Node(2, adjacency_dict={1: {'weight': 3, 'status': True}}, status=False)
    test_net = Network({1: node1, 2: node2})
    assert not test_net.nodes()
    
    # test existing inactive node
    test_net.mark_node_active(1)
    assert node1.node_id in test_net.nodes()
    assert len(test_net.nodes()) is 1
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert node1.status
    assert len(test_net.network_dict) is 2
    
    # test existing active node
    test_net.mark_node_active(1)
    assert node1.node_id in test_net.nodes()
    assert len(test_net.nodes()) is 1
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert node1.status
    assert len(test_net.network_dict) is 2
    
    # test nonexistent node
    test_net.mark_node_active(3)
    assert node1.node_id in test_net.nodes()
    assert len(test_net.nodes()) is 1
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert node1.status
    assert len(test_net.network_dict) is 2


def test_mark_edge_inactive():
    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': True}})
    node2 = Node(2, adjacency_dict={1: {'weight': 3, 'status': True}})
    test_net = Network({1: node1, 2: node2})
    
    # test existing nodes with shared, active edge
    test_net.mark_edge_inactive(node1.node_id, node2.node_id)
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert not node2.adjacency_dict[node1.node_id]['status']
    assert not node1.get_adjacents()
    assert not node2.get_adjacents()
    assert len(test_net.network_dict) is 2
    assert len(test_net.network_dict) is len(test_net.nodes())
    
    # test existing nodes with shared, inactive edge
    test_net.mark_edge_inactive(node1.node_id, node2.node_id)
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert not node2.adjacency_dict[node1.node_id]['status']
    assert not node1.get_adjacents()
    assert not node2.get_adjacents()
    assert len(test_net.network_dict) is 2
    assert len(test_net.network_dict) is len(test_net.nodes())
    
    # test existing nodes with shared, inactive edge
    test_net.add_node(Node(3))
    test_net.mark_edge_inactive(node1.node_id, 3)
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert not node2.adjacency_dict[node1.node_id]['status']
    assert not node1.get_adjacents()
    assert not node2.get_adjacents()
    assert len(test_net.network_dict) is 3
    assert len(test_net.network_dict) is len(test_net.nodes())
    
    # test with nonexistent node
    test_net.add_node(Node(3))
    test_net.mark_edge_inactive(node1.node_id, 4)
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert not node2.adjacency_dict[node1.node_id]['status']
    assert not node1.get_adjacents()
    assert not node2.get_adjacents()
    assert len(test_net.network_dict) is 3
    assert len(test_net.network_dict) is len(test_net.nodes())


def test_mark_edge_active():
    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': False}})
    node2 = Node(2, adjacency_dict={1: {'weight': 3, 'status': False}})
    test_net = Network({1: node1, 2: node2})
    
    # test existing, active nodes with shared, inactive edge
    test_net.mark_edge_active(node1.node_id, node2.node_id)
    assert node1.adjacency_dict[node2.node_id]['status']
    assert node2.adjacency_dict[node1.node_id]['status']
    assert len(node1.adjacency_dict) is 1
    assert len(node2.adjacency_dict) is 1
    assert len(test_net.network_dict) is 2
    assert len(test_net.network_dict) is len(test_net.nodes())
    
    # test existing, active nodes with shared, active edge
    test_net.mark_edge_active(node1.node_id, node2.node_id)
    assert node1.adjacency_dict[node2.node_id]['status']
    assert node2.adjacency_dict[node1.node_id]['status']
    assert len(node1.adjacency_dict) is 1
    assert len(node2.adjacency_dict) is 1
    assert len(test_net.network_dict) is 2
    assert len(test_net.network_dict) is len(test_net.nodes())
    
    # test existing, inactive node with shared, inactive edge
    test_net.mark_node_inactive(node1.node_id)
    test_net.mark_edge_active(node1.node_id, node2.node_id)
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert not node2.adjacency_dict[node1.node_id]['status']
    assert len(node1.adjacency_dict) is 1
    assert len(node2.adjacency_dict) is 1
    assert len(test_net.network_dict) is 2
    assert len(test_net.network_dict) is not len(test_net.nodes())
    assert not node1.status
    assert node2.status
    
    # test existing nodes without shared edge
    test_net.add_node(Node(3))
    test_net.mark_edge_active(node2.node_id, 3)
    test_net.mark_node_inactive(node1.node_id)
    test_net.mark_edge_active(node1.node_id, node2.node_id)
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert not node2.adjacency_dict[node1.node_id]['status']
    assert len(node1.adjacency_dict) is 1
    assert len(node2.adjacency_dict) is 1
    assert len(test_net.network_dict) is 3
    assert len(test_net.network_dict) is not len(test_net.nodes())
    assert not node1.status
    assert node2.status
    
    # test node that doesn't exist
    test_net.mark_edge_active(node2.node_id, 4)
    test_net.add_node(Node(3))
    test_net.mark_edge_active(node2.node_id, 3)
    test_net.mark_node_inactive(node1.node_id)
    test_net.mark_edge_active(node1.node_id, node2.node_id)
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert not node2.adjacency_dict[node1.node_id]['status']
    assert len(node1.adjacency_dict) is 1
    assert len(node2.adjacency_dict) is 1
    assert len(test_net.network_dict) is 3
    assert len(test_net.network_dict) is not len(test_net.nodes())
    assert not node1.status
    assert node2.status


def test_nodes():
    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': True}})
    node2 = Node(2, adjacency_dict={1: {'weight': 3, 'status': True}})
    test_net = Network({1: node1, 2: node2})
    
    # test graph with 2 active nodes
    assert len(test_net.nodes()) is 2
    assert len(test_net.nodes()) is len(test_net.network_dict)
    assert node1.node_id in test_net.nodes()
    assert node2.node_id in test_net.nodes()
    
    # test edge deactivation
    test_net.mark_edge_inactive(node1.node_id, node2.node_id)
    assert len(test_net.nodes()) is 2
    assert len(test_net.nodes()) is len(test_net.network_dict)
    assert node1.node_id in test_net.nodes()
    assert node2.node_id in test_net.nodes()
    
    # deactivate 1 node and test
    test_net.mark_node_inactive(node1.node_id)
    assert len(test_net.nodes()) is 1
    assert len(test_net.nodes()) is not len(test_net.network_dict)
    assert len(test_net.network_dict) is 2
    assert node1.node_id not in test_net.nodes()
    assert node2.node_id in test_net.nodes()
    
    # deactivate last node
    test_net.mark_node_inactive(node2.node_id)
    assert not test_net.nodes()
    assert len(test_net.nodes()) is not len(test_net.network_dict)
    assert len(test_net.network_dict) is 2
    assert node1.node_id not in test_net.nodes()
    assert node2.node_id not in test_net.nodes()
