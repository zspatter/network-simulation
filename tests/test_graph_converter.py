from organflow.GraphConverter import GraphConverter
from organflow.Network import Network, Node

node_a = Node(1, 'A',
              {2: {'weight': 1, 'status': True},
               3: {'weight': 2, 'status': True}})
node_b = Node(2, 'B',
              {3: {'weight': 1, 'status': True}})
node_c = Node(3, 'C',
              {1: {'weight': 2, 'status': True}})
node_d = Node(4, 'D')

network = Network({node_a.node_id: node_a,
                   node_b.node_id: node_b,
                   node_c.node_id: node_c,
                   node_d.node_id: node_d})


def test_graph_converter():
    """
    Verifies all nodes present in Network are present in NetworkX
    Verifies all edges present in Network are present in NetworkX
    Verifies edge weights match for corresponding edges in both Network and NetworkX
    """
    network_x = GraphConverter.convert_to_networkx(network)
    nodes = network.nodes()
    nx_nodes = list(network_x.nodes)

    for node in nodes:
        assert node in nx_nodes
        adjacents = network.network_dict[node].get_adjacents()

        for adjacent in adjacents:
            assert (node, adjacent) or (adjacent, node) in network_x.edges
            edge_weight = network.network_dict[node].adjacency_dict[adjacent]['weight']
            assert edge_weight == network_x[node][adjacent]['weight']

    for node in nx_nodes:
        assert node in nodes


def test_convert_to_networkx_uses_regional_weight_when_requested():
    node_x = Node(10, 'X', {11: {'weight': 5, 'status': True, 'regional weight': 3}})
    node_y = Node(11, 'Y')
    regional_network = Network({10: node_x, 11: node_y})

    network_x = GraphConverter.convert_to_networkx(regional_network, is_regional_weight=True)

    assert network_x[10][11]['weight'] == 3


def test_convert_to_attribute_nx_includes_hospital_attributes():
    node_x = Node(20, 'X', {21: {'weight': 4, 'status': True}},
                  region=1, city='Boston', state='MA')
    node_y = Node(21, 'Y', region=1, city='Cambridge', state='MA')
    attribute_network = Network({20: node_x, 21: node_y})

    network_x = GraphConverter.convert_to_attribute_nx(
            attribute_network, state_dict={'MA': 2}, region_dict={1: 2})

    assert network_x.nodes[20]['hospital_name'] == 'X'
    assert network_x.nodes[20]['city'] == 'Boston'
    assert network_x.nodes[20]['state'] == 'MA'
    assert network_x.nodes[20]['region'] == 1
    assert network_x.nodes[20]['state_count'] == 2
    assert network_x.nodes[20]['region_count'] == 2
    assert network_x[20][21]['weight'] == 4


def test_convert_to_attribute_nx_maps_us_state_to_washington_dc():
    node_x = Node(30, 'X', region=2, city='Washington', state='US')
    dc_network = Network({30: node_x})

    network_x = GraphConverter.convert_to_attribute_nx(
            dc_network, state_dict={'Washington D.C.': 1}, region_dict={2: 1})

    assert network_x.nodes[30]['state'] == 'Washington D.C.'
