import sys
from os.path import abspath, dirname, join

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

import export_edgelist  # noqa: E402

from network_simulator.Network import Network  # noqa: E402
from network_simulator.Node import Node  # noqa: E402


def _small_network():
    # 1-2 and 2-3, both undirected (mirrored in each node's adjacency dict, per Network's
    # __init__ - see Network's docstring)
    node1 = Node(1, adjacency_dict={2: {'weight': 1, 'status': True}})
    node2 = Node(2, adjacency_dict={1: {'weight': 1, 'status': True},
                                    3: {'weight': 2, 'status': True}})
    node3 = Node(3, adjacency_dict={2: {'weight': 2, 'status': True}})
    return Network({1: node1, 2: node2, 3: node3})


def test_generate_edge_list_writes_both_directions_of_every_edge(tmp_path):
    network = _small_network()
    output_path = tmp_path / 'edgelist.txt'

    export_edgelist.generate_edge_list(network, output_path)

    lines = set(output_path.read_text().splitlines())
    assert lines == {'1 2', '2 1', '2 3', '3 2'}


def test_unique_edge_list_deduplicates_bidirectional_pairs():
    network = _small_network()

    edges = export_edgelist.unique_edge_list(network)

    assert len(edges) == 2
    normalized = {frozenset(edge) for edge in edges}
    assert normalized == {frozenset({1, 2}), frozenset({2, 3})}


def test_write_edge_list_writes_one_pair_per_line(tmp_path):
    output_path = tmp_path / 'unique_edges.txt'

    export_edgelist.write_edge_list([(1, 2), (2, 3)], output_path)

    assert output_path.read_text() == '1 2\n2 3'
