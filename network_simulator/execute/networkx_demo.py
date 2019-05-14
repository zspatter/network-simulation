import matplotlib.pyplot as plt
import networkx as nx

from network_simulator.GraphBuilder import GraphBuilder
from network_simulator.GraphConverter import GraphConverter
from network_simulator.OrganGenerator import OrganGenerator
from network_simulator.OrganList import OrganList
from network_simulator.PatientGenerator import PatientGenerator
from network_simulator.SubnetworkGenerator import SubnetworkGenerator
from network_simulator.WaitList import WaitList

# node1 = Node(1, "A",
#              {2: {'weight': 3, 'status': True},
#               3: {'weight': 5, 'status': True},
#               6: {'weight': 6, 'status': False}})
# node2 = Node(2, "B",
#              {1: {'weight': 20, 'status': True},
#               4: {'weight': 3, 'status': True}})
# node3 = Node(3, "C",
#              {2: {'weight': 6, 'status': True},
#               4: {'weight': 9, 'status': True}})
# node4 = Node(4, "D",
#              {3: {'weight': 8, 'status': True},
#               2: {'weight': 4, 'status': True}})
# node5 = Node(5, "E",
#              {1: {'weight': 1, 'status': True},
#               4: {'weight': 2, 'status': True}})
#
# net = Network({node1.node_id: node1,
#                node2.node_id: node2,
#                node3.node_id: node3,
#                node4.node_id: node4,
#                node5.node_id: node5})


# creates network
network = GraphBuilder.graph_builder(20)

# creates patient list
wait_list = WaitList()
PatientGenerator.generate_patients_to_list(network, 10, wait_list)
print(wait_list)

# creates organ list
organ_list = OrganList()
OrganGenerator.generate_organs_to_list(network, 10, organ_list)
print(organ_list)

# creates subnetworks for patients and organs
patient_network = SubnetworkGenerator.generate_subnetwork(network, wait_list)
organ_network = SubnetworkGenerator.generate_subnetwork(network, organ_list)

# generates NetworkX graphs
graph_nx = GraphConverter.convert_to_networkx(network)
patient_nx = GraphConverter.convert_to_networkx(patient_network)
organ_nx = GraphConverter.convert_to_networkx(organ_network)

# plots hospital network (overall/global network)
pos = nx.spring_layout(graph_nx)
edge_weights = {(u, v,): d['weight'] for u, v, d in graph_nx.edges(data=True)}
nx.draw(graph_nx, pos=pos, with_labels=True)
nx.draw_networkx_edge_labels(graph_nx, pos, edge_weights)
plt.show()

# plots patient network
pos = nx.spring_layout(patient_nx)
edge_weights = {(u, v,): d['weight'] for u, v, d in patient_nx.edges(data=True)}
nx.draw(patient_nx, pos=pos, with_labels=True)
nx.draw_networkx_edge_labels(patient_nx, pos, edge_weights)
plt.show()

# plots organ network
pos = nx.spring_layout(organ_nx)
edge_weights = {(u, v,): d['weight'] for u, v, d in organ_nx.edges(data=True)}
nx.draw(organ_nx, pos=pos, with_labels=True)
nx.draw_networkx_edge_labels(organ_nx, pos, edge_weights)
plt.show()
