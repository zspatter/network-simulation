import network_simulator.GraphBuilder as gb


def test_generate_random_adjacency_dict():
    test_dict = gb.GraphBuilder.generate_random_adjacency_dict(1, 50)
    assert len(test_dict) < 50

    for node in test_dict:
        assert test_dict[node]['weight'] < 50
        assert test_dict[node]['weight'] > 0
        assert test_dict[node]['status']


def test_generate_random_network():
    n = 5
    graph = gb.GraphBuilder.generate_random_network(n)
    assert len(graph.network_dict) is n
    assert len(graph.nodes()) is n
    for node in graph.network_dict:
        assert len(graph.network_dict[node].adjacency_dict) < n
