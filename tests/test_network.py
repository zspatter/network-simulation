from network_simulator.Network import Network, Node


def test_add_node():
    node1 = Node(1)
    test_net = Network()

    # add node to empty graph
    assert len(test_net.nodes()) == 0
    test_net.add_node(node1)
    assert len(test_net.nodes()) == 1
    assert node1.node_id in test_net.nodes()

    # attempt to add node that already exists
    test_net.add_node(node1)
    assert len(test_net.nodes()) == 1
    assert node1.node_id in test_net.nodes()


def test_remove_node():
    node1 = Node(1)
    node2 = Node(2)
    test_net = Network({1: node1, 2: node2})

    # remove an existing node
    assert len(test_net.nodes()) == 2
    test_net.remove_node(1)
    assert len(test_net.nodes()) == 1
    assert node2.node_id in test_net.network_dict

    # remove a node that doesn't exist
    test_net.remove_node(3)
    assert len(test_net.nodes()) == 1
    assert node2.node_id in test_net.network_dict


def test_add_edge():
    node1 = Node(1)
    node2 = Node(2)
    test_net = Network()

    # add nodes, but not edges
    test_net.add_node(node1)
    test_net.add_node(node2)
    assert len(test_net.network_dict[node1.node_id].get_adjacents()) == 0

    # add edge to existing nodes
    test_net.add_edge(node1.node_id, node2.node_id, 5)
    assert len(test_net.network_dict[node1.node_id].get_adjacents()) == 1
    assert test_net.network_dict[node1.node_id].adjacency_dict[node2.node_id]['weight'] == 5

    # attempt to add edge that already exists
    test_net.add_edge(node1.node_id, node2.node_id, 5)
    assert len(test_net.network_dict[node1.node_id].get_adjacents()) == 1
    assert test_net.network_dict[node1.node_id].adjacency_dict[node2.node_id]['weight'] == 5

    # add inactive node
    node3 = Node(3, status=False)
    test_net.add_node(node3)

    # attempt to add edge to inactive node
    test_net.add_edge(node1.node_id, node3.node_id, 15)
    assert len(test_net.network_dict[node1.node_id].get_adjacents()) == 1
    assert test_net.network_dict[node1.node_id].adjacency_dict[node2.node_id]['weight'] == 5

    # attempts to add edge to node that doesn't exist
    test_net.add_edge(node1.node_id, node_id2=4, weight=25)
    assert len(test_net.network_dict[node1.node_id].get_adjacents()) == 1
    assert test_net.network_dict[node1.node_id].adjacency_dict[node2.node_id]['weight'] == 5


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
    assert len(test_net.network_dict) == 2

    # attempt to remove edge with no shared edge
    test_net.remove_edge(node1.node_id, node3.node_id)
    assert not node1.adjacency_dict
    assert not node2.adjacency_dict
    assert len(test_net.network_dict) == 2

    # attempt to remove edge from a node that doesn't exist
    test_net.remove_edge(node1.node_id, 4)
    assert not node1.adjacency_dict
    assert not node2.adjacency_dict
    assert len(test_net.network_dict) == 2


def test_mark_node_inactive():
    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': True}})
    node2 = Node(2, adjacency_dict={1: {'weight': 3, 'status': True}})
    test_net = Network({1: node1, 2: node2})

    assert len(test_net.network_dict) == len(test_net.nodes())
    assert node2.node_id in test_net.network_dict[node1.node_id].adjacency_dict
    assert node1.node_id in test_net.network_dict[node2.node_id].adjacency_dict

    # test marking existing active node as inactive
    test_net.mark_node_inactive(1)
    assert len(test_net.network_dict) == 2
    assert len(test_net.network_dict) != len(test_net.nodes())
    assert not node1.status
    assert node2.status
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert not node2.adjacency_dict[node1.node_id]['status']
    assert node2.node_id in test_net.network_dict[node1.node_id].adjacency_dict
    assert node1.node_id in test_net.network_dict[node2.node_id].adjacency_dict

    # test already inactive node
    test_net.mark_node_inactive(1)
    assert len(test_net.network_dict) == 2
    assert len(test_net.network_dict) != len(test_net.nodes())
    assert not node1.status
    assert node2.status
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert not node2.adjacency_dict[node1.node_id]['status']
    assert node2.node_id in test_net.network_dict[node1.node_id].adjacency_dict
    assert node1.node_id in test_net.network_dict[node2.node_id].adjacency_dict

    # test node that doesn't exist
    test_net.mark_node_inactive(3)
    assert len(test_net.network_dict) == 2
    assert len(test_net.network_dict) != len(test_net.nodes())


def test_mark_node_active():
    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': True}}, status=False)
    node2 = Node(2, adjacency_dict={1: {'weight': 3, 'status': True}}, status=False)
    test_net = Network({1: node1, 2: node2})
    assert not test_net.nodes()

    # test existing inactive node
    test_net.mark_node_active(1)
    assert node1.node_id in test_net.nodes()
    assert len(test_net.nodes()) == 1
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert node1.status
    assert len(test_net.network_dict) == 2

    # test existing active node
    test_net.mark_node_active(1)
    assert node1.node_id in test_net.nodes()
    assert len(test_net.nodes()) == 1
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert node1.status
    assert len(test_net.network_dict) == 2

    # test nonexistent node
    test_net.mark_node_active(3)
    assert node1.node_id in test_net.nodes()
    assert len(test_net.nodes()) == 1
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert node1.status
    assert len(test_net.network_dict) == 2


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
    assert len(test_net.network_dict) == 2
    assert len(test_net.network_dict) == len(test_net.nodes())

    # test existing nodes with shared, inactive edge
    test_net.mark_edge_inactive(node1.node_id, node2.node_id)
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert not node2.adjacency_dict[node1.node_id]['status']
    assert not node1.get_adjacents()
    assert not node2.get_adjacents()
    assert len(test_net.network_dict) == 2
    assert len(test_net.network_dict) == len(test_net.nodes())

    # test existing nodes with shared, inactive edge
    test_net.add_node(Node(3))
    test_net.mark_edge_inactive(node1.node_id, 3)
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert not node2.adjacency_dict[node1.node_id]['status']
    assert not node1.get_adjacents()
    assert not node2.get_adjacents()
    assert len(test_net.network_dict) == 3
    assert len(test_net.network_dict) == len(test_net.nodes())

    # test with nonexistent node
    test_net.add_node(Node(3))
    test_net.mark_edge_inactive(node1.node_id, 4)
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert not node2.adjacency_dict[node1.node_id]['status']
    assert not node1.get_adjacents()
    assert not node2.get_adjacents()
    assert len(test_net.network_dict) == 3
    assert len(test_net.network_dict) == len(test_net.nodes())


def test_mark_edge_active():
    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': False}})
    node2 = Node(2, adjacency_dict={1: {'weight': 3, 'status': False}})
    test_net = Network({1: node1, 2: node2})

    # test existing, active nodes with shared, inactive edge
    test_net.mark_edge_active(node1.node_id, node2.node_id)
    assert node1.adjacency_dict[node2.node_id]['status']
    assert node2.adjacency_dict[node1.node_id]['status']
    assert len(node1.adjacency_dict) == 1
    assert len(node2.adjacency_dict) == 1
    assert len(test_net.network_dict) == 2
    assert len(test_net.network_dict) == len(test_net.nodes())

    # test existing, active nodes with shared, active edge
    test_net.mark_edge_active(node1.node_id, node2.node_id)
    assert node1.adjacency_dict[node2.node_id]['status']
    assert node2.adjacency_dict[node1.node_id]['status']
    assert len(node1.adjacency_dict) == 1
    assert len(node2.adjacency_dict) == 1
    assert len(test_net.network_dict) == 2
    assert len(test_net.network_dict) == len(test_net.nodes())

    # test existing, inactive node with shared, inactive edge
    test_net.mark_node_inactive(node1.node_id)
    test_net.mark_edge_active(node1.node_id, node2.node_id)
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert not node2.adjacency_dict[node1.node_id]['status']
    assert len(node1.adjacency_dict) == 1
    assert len(node2.adjacency_dict) == 1
    assert len(test_net.network_dict) == 2
    assert len(test_net.network_dict) != len(test_net.nodes())
    assert not node1.status
    assert node2.status

    # test existing nodes without shared edge
    test_net.add_node(Node(3))
    test_net.mark_edge_active(node2.node_id, 3)
    test_net.mark_node_inactive(node1.node_id)
    test_net.mark_edge_active(node1.node_id, node2.node_id)
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert not node2.adjacency_dict[node1.node_id]['status']
    assert len(node1.adjacency_dict) == 1
    assert len(node2.adjacency_dict) == 1
    assert len(test_net.network_dict) == 3
    assert len(test_net.network_dict) != len(test_net.nodes())
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
    assert len(node1.adjacency_dict) == 1
    assert len(node2.adjacency_dict) == 1
    assert len(test_net.network_dict) == 3
    assert len(test_net.network_dict) != len(test_net.nodes())
    assert not node1.status
    assert node2.status


def test_nodes():
    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': True}})
    node2 = Node(2, adjacency_dict={1: {'weight': 3, 'status': True}})
    test_net = Network({1: node1, 2: node2})

    # test graph with 2 active nodes
    assert len(test_net.nodes()) == 2
    assert len(test_net.nodes()) == len(test_net.network_dict)
    assert node1.node_id in test_net.nodes()
    assert node2.node_id in test_net.nodes()

    # test edge deactivation
    test_net.mark_edge_inactive(node1.node_id, node2.node_id)
    assert len(test_net.nodes()) == 2
    assert len(test_net.nodes()) == len(test_net.network_dict)
    assert node1.node_id in test_net.nodes()
    assert node2.node_id in test_net.nodes()

    # deactivate 1 node and test
    test_net.mark_node_inactive(node1.node_id)
    assert len(test_net.nodes()) == 1
    assert len(test_net.nodes()) != len(test_net.network_dict)
    assert len(test_net.network_dict) == 2
    assert node1.node_id not in test_net.nodes()
    assert node2.node_id in test_net.nodes()

    # deactivate last node
    test_net.mark_node_inactive(node2.node_id)
    assert not test_net.nodes()
    assert len(test_net.nodes()) != len(test_net.network_dict)
    assert len(test_net.network_dict) == 2
    assert node1.node_id not in test_net.nodes()
    assert node2.node_id not in test_net.nodes()


def test_init_removes_edges_to_nonexistent_nodes():
    # node1 references node 2, which is never actually added to the graph -
    # the constructor should drop that dangling edge rather than leave a
    # KeyError waiting to happen the next time it's traversed
    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': True}})
    test_net = Network({1: node1})

    assert node1.adjacency_dict == {}
    assert test_net.nodes() == [1]


def test_init_mirrors_one_sided_adjacency():
    # node1 -> node2 is declared, but node2 doesn't declare the reverse edge;
    # the constructor should mirror it so the graph is genuinely undirected
    node1 = Node(1, adjacency_dict={2: {'weight': 7, 'status': True}})
    node2 = Node(2)
    test_net = Network({1: node1, 2: node2})

    assert test_net.network_dict[2].adjacency_dict[1]['weight'] == 7
    assert test_net.network_dict[2].adjacency_dict[1] is node1.adjacency_dict[2]


def test__iter__():
    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': True}})
    node2 = Node(2, adjacency_dict={1: {'weight': 3, 'status': True}})
    test_net = Network({1: node1, 2: node2})

    assert sorted(list(test_net)) == test_net.nodes()

    test_net.mark_node_inactive(node1.node_id)
    assert list(test_net) == [node2.node_id]


def test_add_node_mirrors_new_node_own_adjacency():
    # the new node arrives already knowing about node1; add_node should
    # mirror that edge onto node1's adjacency dict too
    node1 = Node(1)
    test_net = Network({1: node1})

    node2 = Node(2, adjacency_dict={1: {'weight': 9, 'status': True}})
    test_net.add_node(node2)

    assert node1.adjacency_dict[2]['weight'] == 9
    assert node1.adjacency_dict[2] is node2.adjacency_dict[1]


def test_add_edge_with_regional_weight():
    node1 = Node(1)
    node2 = Node(2)
    test_net = Network({1: node1, 2: node2})

    test_net.add_edge(node1.node_id, node2.node_id, weight=5, regional_weight=2)

    assert node1.adjacency_dict[2]['weight'] == 5
    assert node1.adjacency_dict[2]['regional weight'] == 2
    assert node2.adjacency_dict[1]['regional weight'] == 2


def test_remove_edge_between_existing_nodes_with_no_shared_edge():
    node1 = Node(1)
    node2 = Node(2)
    test_net = Network({1: node1, 2: node2})

    # both nodes exist, but there's no edge between them to remove
    test_net.remove_edge(node1.node_id, node2.node_id)

    assert node1.adjacency_dict == {}
    assert node2.adjacency_dict == {}


def test__str__():
    node1 = Node(1, 'A', {2: {'weight': 3, 'status': True}})
    node2 = Node(2, 'B', {1: {'weight': 3, 'status': True}})
    test_net = Network({1: node1, 2: node2})

    text = str(test_net)
    assert 'A' in text
    assert 'B' in text
    assert text.endswith('\n===============================\n')
