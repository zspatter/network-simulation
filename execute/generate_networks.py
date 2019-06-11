import shelve

from network_simulator.GraphBuilder import GraphBuilder
from network_simulator.OrganGenerator import OrganGenerator
from network_simulator.OrganList import OrganList
from network_simulator.PatientGenerator import PatientGenerator
from network_simulator.SubnetworkGenerator import SubnetworkGenerator
from network_simulator.WaitList import WaitList

with shelve.open('random_networks') as db:
    for x in range(1, 4):
        network = GraphBuilder.graph_builder(n=150, max_weight=25)

        patients = WaitList()
        PatientGenerator.generate_patients_to_list(graph=network, n=300, wait_list=patients)

        organs = OrganList()
        OrganGenerator.generate_organs_to_list(graph=network, n=75, organ_list=organs)

        hospital_network = network
        patient_network = SubnetworkGenerator.generate_subnetwork(network=hospital_network,
                                                                  collection=patients)
        organ_network = SubnetworkGenerator.generate_subnetwork(network=hospital_network,
                                                                collection=organs)
        
        db[f'hospital_network{x}'] = hospital_network
        db[f'patient_network{x}'] = patient_network
        db[f'organ_network{x}'] = organ_network
