from organflow.GraphBuilder import GraphBuilder


def test_generate_random_adjacency_dict():
    test_dict = GraphBuilder.generate_random_adjacency_dict(node_id=1,
                                                            total_nodes=50, max_weight=50)
    assert len(test_dict) < 50

    for node in test_dict:
        assert 0 < test_dict[node]['weight'] < 51
        assert test_dict[node]['status']


def test_generate_random_network():
    n = 5
    graph = GraphBuilder.graph_builder(n)
    assert len(graph.network_dict) is n
    assert len(graph.nodes()) is n
    for node in graph.network_dict:
        assert len(graph.network_dict[node].adjacency_dict) < n


def test_generate_random_network_assigns_synthetic_regions():
    # region is a deterministic round-robin partition over NUM_SYNTHETIC_REGIONS,
    # not left unset - see GraphBuilder.graph_builder docstring
    n = 25
    graph = GraphBuilder.graph_builder(n)

    for node_id, node in graph.network_dict.items():
        assert node.region == ((node_id - 1) % GraphBuilder.NUM_SYNTHETIC_REGIONS) + 1

    seen_regions = {node.region for node in graph.network_dict.values()}
    assert seen_regions == set(range(1, GraphBuilder.NUM_SYNTHETIC_REGIONS + 1))
