import sys
from os.path import abspath, dirname, join

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

import import_edge_list  # noqa: E402


def test_import_edge_list_reads_unweighted_rows(tmp_path):
    path = tmp_path / 'edges.tsv'
    path.write_text('1\t2\n2\t3\n')

    data = import_edge_list.import_edge_list(str(path))

    assert data == [[1, 2], [2, 3], [None, None]]


def test_import_edge_list_reads_weighted_rows(tmp_path):
    # regression test: a 3-column (weighted) row used to read row[3], which is out of
    # range for a 3-element row and raised IndexError - the weight is at row[2]
    path = tmp_path / 'edges.tsv'
    path.write_text('1\t2\t5\n2\t3\t10\n')

    data = import_edge_list.import_edge_list(str(path))

    assert data == [[1, 2], [2, 3], [5, 10]]


def test_get_nodes_returns_the_union_of_sources_and_destinations():
    data = [[1, 2], [2, 3], [None, None]]

    assert import_edge_list.get_nodes(data) == {1, 2, 3}


def test_build_network_creates_nodes_and_weighted_edges():
    data = [[1, 2], [2, 3], [5, None]]
    nodes = import_edge_list.get_nodes(data)

    network = import_edge_list.build_network(nodes, data)

    assert set(network.network_dict.keys()) == {1, 2, 3}
    assert network.network_dict[1].adjacency_dict[2]['weight'] == 5
    # a None weight (2-column row) defaults to 1 - see add_edges
    assert network.network_dict[2].adjacency_dict[3]['weight'] == 1
