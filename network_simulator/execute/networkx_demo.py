import networkx as nx
import matplotlib.pyplot as plt
from network_simulator.Node import Node
from network_simulator.Network import Network
from network_simulator.GraphConverter import GraphConverter


node1 = Node(1, "A",
             {2: {'weight': 3, 'status': True},
              3: {'weight': 5, 'status': True},
              6: {'weight': 6, 'status': False}})
node2 = Node(2, "B",
             {1: {'weight': 20, 'status': True},
              4: {'weight': 3, 'status': True}})
node3 = Node(3, "C",
             {2: {'weight': 6, 'status': True},
              4: {'weight': 9, 'status': True}})
node4 = Node(4, "D",
             {3: {'weight': 8, 'status': True},
              2: {'weight': 4, 'status': True}})
node5 = Node(5, "E",
             {1: {'weight': 1, 'status': True},
              4: {'weight': 2, 'status': True}})

net = Network({node1.node_id: node1,
               node2.node_id: node2,
               node3.node_id: node3,
               node4.node_id: node4,
               node5.node_id: node5})

G = GraphConverter.convert_to_networkx(net)

# G = nx.Graph()
# G.add_node(1)
# G.add_nodes_from([2, 3])
# G.add_edge(1, 2)
#
# print(list(nx.connected_components(G)))
#
# d = {1: {2: {'weight': 10}},
#      2: {3: {'weight': 9}, 4: {'weight': 3}, 6: {'weight': 4}},
#      3: {4: {'weight': 8}},
#      4: {5: {'weight': 7}},
#      5: {6: {'weight': 6}},
#      6: {7: {'weight': 5}}}
#
# G = nx.Graph()
# G.add_edge(1, 2, weight=10)
# G.add_edge(2, 3, weight=9)
# G.add_edge(3, 4, weight=8)
# G.add_edge(4, 5, weight=7)
# G.add_edge(5, 3, weight=30)
# G.add_edge(2, 1, weight=10)

pos = nx.spring_layout(G)
# nx.draw(G, pos=pos, with_labels=True)
# nx.draw_networkx_edge_labels(G, pos)
edge_weights = {(u, v,): d['weight'] for u, v, d in G.edges(data=True)}

# print(edge_weights)
# for u, v, d in G.edges(data=True):
#     print(u, v, d)

nx.draw(G, pos=pos, with_labels=True)
nx.draw_networkx_edge_labels(G, pos, edge_weights)

plt.show()
