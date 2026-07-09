import pytest

from organflow.distance import estimate_transit_hours, haversine_km
from organflow.exceptions import GraphElementError
from organflow.Network import Network, Node


def test_add_node():
    node1 = Node(1)
    test_net = Network()

    # add node to empty graph
    assert len(test_net.nodes()) == 0
    test_net.add_node(node1)
    assert len(test_net.nodes()) == 1
    assert node1.node_id in test_net.nodes()

    # adding a node that already exists raises, leaving the graph unchanged
    with pytest.raises(GraphElementError):
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

    # removing a node that doesn't exist raises, leaving the graph unchanged
    with pytest.raises(GraphElementError):
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

    # adding an edge that already exists raises
    with pytest.raises(GraphElementError):
        test_net.add_edge(node1.node_id, node2.node_id, 5)
    assert len(test_net.network_dict[node1.node_id].get_adjacents()) == 1

    # adding an edge to an inactive node raises
    node3 = Node(3, status=False)
    test_net.add_node(node3)
    with pytest.raises(GraphElementError):
        test_net.add_edge(node1.node_id, node3.node_id, 15)
    assert len(test_net.network_dict[node1.node_id].get_adjacents()) == 1

    # adding an edge to a node that doesn't exist raises
    with pytest.raises(GraphElementError):
        test_net.add_edge(node1.node_id, node_id2=4, weight=25)
    assert len(test_net.network_dict[node1.node_id].get_adjacents()) == 1


def test_remove_edge():
    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': True}})
    node2 = Node(2, adjacency_dict={1: {'weight': 3, 'status': True}})
    node3 = Node(3)
    test_net = Network({1: node1, 2: node2})

    assert node2.node_id in node1.adjacency_dict
    assert node1.node_id in node2.adjacency_dict

    # remove edge
    test_net.remove_edge(node1.node_id, node2.node_id)
    assert node2.node_id not in node1.adjacency_dict
    assert node1.node_id not in node2.adjacency_dict
    assert len(test_net.network_dict) == 2

    # removing an edge that doesn't exist (no shared edge) raises
    test_net.add_node(node3)
    with pytest.raises(GraphElementError):
        test_net.remove_edge(node1.node_id, node3.node_id)

    # removing an edge from a node that doesn't exist raises
    with pytest.raises(GraphElementError):
        test_net.remove_edge(node1.node_id, 4)


def test_mark_node_inactive():
    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': True}})
    node2 = Node(2, adjacency_dict={1: {'weight': 3, 'status': True}})
    test_net = Network({1: node1, 2: node2})

    # marking an existing active node inactive
    test_net.mark_node_inactive(1)
    assert not node1.status
    assert node2.status
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert not node2.adjacency_dict[node1.node_id]['status']

    # an already-inactive node raises, leaving state unchanged
    with pytest.raises(GraphElementError):
        test_net.mark_node_inactive(1)
    assert not node1.status

    # a nonexistent node raises
    with pytest.raises(GraphElementError):
        test_net.mark_node_inactive(3)


def test_mark_node_active():
    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': True}}, status=False)
    node2 = Node(2, adjacency_dict={1: {'weight': 3, 'status': True}}, status=False)
    test_net = Network({1: node1, 2: node2})
    assert not test_net.nodes()

    # mark an existing inactive node active (node2 still inactive, so the edge stays inactive)
    test_net.mark_node_active(1)
    assert node1.node_id in test_net.nodes()
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert node1.status

    # an already-active node raises
    with pytest.raises(GraphElementError):
        test_net.mark_node_active(1)
    assert node1.status

    # a nonexistent node raises
    with pytest.raises(GraphElementError):
        test_net.mark_node_active(3)


def test_mark_edge_inactive():
    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': True}})
    node2 = Node(2, adjacency_dict={1: {'weight': 3, 'status': True}})
    test_net = Network({1: node1, 2: node2})

    # a shared, active edge is deactivated in both directions
    test_net.mark_edge_inactive(node1.node_id, node2.node_id)
    assert not node1.adjacency_dict[node2.node_id]['status']
    assert not node2.adjacency_dict[node1.node_id]['status']

    # an already-inactive edge raises
    with pytest.raises(GraphElementError):
        test_net.mark_edge_inactive(node1.node_id, node2.node_id)

    # no shared edge raises
    test_net.add_node(Node(3))
    with pytest.raises(GraphElementError):
        test_net.mark_edge_inactive(node1.node_id, 3)

    # a nonexistent node raises
    with pytest.raises(GraphElementError):
        test_net.mark_edge_inactive(node1.node_id, 4)


def test_mark_edge_active():
    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': False}})
    node2 = Node(2, adjacency_dict={1: {'weight': 3, 'status': False}})
    test_net = Network({1: node1, 2: node2})

    # a shared, inactive edge between two active nodes is reactivated
    test_net.mark_edge_active(node1.node_id, node2.node_id)
    assert node1.adjacency_dict[node2.node_id]['status']
    assert node2.adjacency_dict[node1.node_id]['status']

    # an already-active edge raises
    with pytest.raises(GraphElementError):
        test_net.mark_edge_active(node1.node_id, node2.node_id)

    # an edge touching an inactive node cannot be activated
    test_net.mark_edge_inactive(node1.node_id, node2.node_id)
    test_net.mark_node_inactive(node1.node_id)
    with pytest.raises(GraphElementError):
        test_net.mark_edge_active(node1.node_id, node2.node_id)
    assert not node1.adjacency_dict[node2.node_id]['status']

    # no shared edge raises
    test_net.add_node(Node(3))
    with pytest.raises(GraphElementError):
        test_net.mark_edge_active(node2.node_id, 3)

    # a nonexistent node raises
    with pytest.raises(GraphElementError):
        test_net.mark_edge_active(node2.node_id, 4)


def test_mark_edge_helpers_detect_a_one_sided_edge():
    # Regression: the old guard tested node_id1's presence in node_id2's dict twice, so a
    # half-present edge (mirrored only one way) was mishandled. It must be treated as "no
    # shared edge" in both directions.
    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': True}})
    node2 = Node(2, adjacency_dict={1: {'weight': 3, 'status': True}})
    test_net = Network({1: node1, 2: node2})
    # break the mirror: leave the edge only on node1's side
    del test_net.network_dict[2].adjacency_dict[1]

    with pytest.raises(GraphElementError):
        test_net.mark_edge_inactive(1, 2)
    with pytest.raises(GraphElementError):
        test_net.mark_edge_active(1, 2)
    with pytest.raises(GraphElementError):
        test_net.mark_edge_active(2, 1)


def test_nodes():
    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': True}})
    node2 = Node(2, adjacency_dict={1: {'weight': 3, 'status': True}})
    test_net = Network({1: node1, 2: node2})

    assert len(test_net.nodes()) == 2

    # edge deactivation doesn't remove nodes from the active set
    test_net.mark_edge_inactive(node1.node_id, node2.node_id)
    assert len(test_net.nodes()) == 2

    # deactivating a node removes it from the active set but not the dict
    test_net.mark_node_inactive(node1.node_id)
    assert len(test_net.nodes()) == 1
    assert len(test_net.network_dict) == 2
    assert node1.node_id not in test_net.nodes()
    assert node2.node_id in test_net.nodes()

    test_net.mark_node_inactive(node2.node_id)
    assert not test_net.nodes()
    assert len(test_net.network_dict) == 2


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
    with pytest.raises(GraphElementError):
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


def test_transit_from_uses_coordinates_when_present():
    # An absurd edge weight (99h) is deliberately ignored: a coordinate-bearing
    # network computes direct point-to-point transit, not a graph-edge sum.
    node1 = Node(1, latitude=41.88, longitude=-87.63,
                 adjacency_dict={2: {'weight': 99, 'status': True}})
    node2 = Node(2, latitude=42.36, longitude=-71.06,
                 adjacency_dict={1: {'weight': 99, 'status': True}})
    net = Network({1: node1, 2: node2})

    transit = net.transit_from(1)
    expected = estimate_transit_hours(haversine_km(41.88, -87.63, 42.36, -71.06))
    assert transit[2] == expected
    assert transit[2] < 99  # not the fictitious edge weight
    # source-to-itself is the ground handling floor, not zero (no teleporting)
    assert transit[1] == estimate_transit_hours(0.0)


def test_transit_from_falls_back_to_shortest_path_without_coordinates():
    # No coordinates -> the graph edge weights are the distance model (Dijkstra sum).
    node1 = Node(1, adjacency_dict={2: {'weight': 4, 'status': True}})
    node2 = Node(2, adjacency_dict={1: {'weight': 4, 'status': True},
                                    3: {'weight': 5, 'status': True}})
    node3 = Node(3, adjacency_dict={2: {'weight': 5, 'status': True}})
    net = Network({1: node1, 2: node2, 3: node3})

    transit = net.transit_from(1)
    assert transit[1] == 0
    assert transit[2] == 4
    assert transit[3] == 9  # 1 -> 2 -> 3


def test_transit_from_is_cached_until_a_mutation_invalidates_it():
    node1 = Node(1, adjacency_dict={2: {'weight': 4, 'status': True}})
    node2 = Node(2, adjacency_dict={1: {'weight': 4, 'status': True}})
    net = Network({1: node1, 2: node2})

    first = net.transit_from(1)
    assert net.transit_from(1) is first  # served from cache (same object)

    net.mark_node_inactive(2)  # a mutation must invalidate the cache
    assert net.transit_from(1) is not first
