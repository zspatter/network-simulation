import os
import shelve
from os.path import join, abspath

import networkx

from network_simulator.GraphBuilder import GraphBuilder
from network_simulator.GraphConverter import GraphConverter
from network_simulator.OrganGenerator import OrganGenerator
from network_simulator.OrganList import OrganList
from network_simulator.PatientGenerator import PatientGenerator
from network_simulator.SubnetworkGenerator import SubnetworkGenerator
from network_simulator.WaitList import WaitList


def generate_random_graphs(path):
    for x in range(1, 4):

        with shelve.open(join(path, f'random_networks{x}')) as db:
            db.clear()
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


def export_gexf(path='.'):
    path = abspath(path)
    os.makedirs(path, exist_ok=True)

    filenames = ('random_networks1', 'random_networks2', 'random_networks3')

    for filename in filenames:
        with shelve.open(join(path, 'shelve', filename)) as db:
            for key in db.keys():
                nx = GraphConverter.convert_to_networkx(db[key])
                networkx.write_gexf(G=nx, path=join(path, 'gexf', f'{key}.gexf'))


if __name__ == '__main__':
    generate_random_graphs(path=join(abspath('.'), 'export', 'shelve'))
    export_gexf(path=join(abspath('.'), 'export'))
