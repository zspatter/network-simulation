from organflow.GraphBuilder import GraphBuilder
from organflow.OrganGenerator import OrganGenerator
from organflow.OrganList import OrganList
from organflow.PatientGenerator import PatientGenerator
from organflow.SubnetworkGenerator import SubnetworkGenerator
from organflow.WaitList import WaitList

network = GraphBuilder.graph_builder(20)
wait_list = WaitList()
organ_list = OrganList()

PatientGenerator.generate_patients_to_list(network, 10, wait_list)
OrganGenerator.generate_organs_to_list(network, 5, organ_list)

print(network)
print(wait_list)
print(organ_list)

# print(isinstance(wait_list, WaitList), isinstance(organ_list, OrganList))
# print(type(wait_list), type(organ_list))

patient_network = SubnetworkGenerator.generate_subnetwork(network, wait_list)
print(patient_network)

organ_network = SubnetworkGenerator.generate_subnetwork(network, organ_list)
print(organ_network)
