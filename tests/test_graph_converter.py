from network_simulator.GraphConverter import GraphConverter
from network_simulator.Network import Node, Network

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
