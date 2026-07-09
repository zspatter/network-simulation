import shelve
import sys
from os.path import abspath, dirname, join

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

import generate_networks  # noqa: E402

from organflow.Network import Network  # noqa: E402
from organflow.Node import Node  # noqa: E402


def test_generate_random_graphs_writes_three_shelve_files_with_three_networks_each(tmp_path):
    generate_networks.generate_random_graphs(path=str(tmp_path))

    for x in (1, 2, 3):
        with shelve.open(str(tmp_path / f'random_networks{x}')) as db:
            hospital_network = db[f'hospital_network{x}']
            patient_network = db[f'patient_network{x}']
            organ_network = db[f'organ_network{x}']

            assert isinstance(hospital_network, Network)
            assert len(hospital_network.network_dict) == 150
            # subnetworks only contain the (smaller) subset of nodes patients/organs occupy
            assert len(patient_network.network_dict) <= 150
            assert len(organ_network.network_dict) <= 150


def test_export_gexf_writes_a_gexf_file_per_shelved_network(tmp_path):
    shelve_dir = tmp_path / 'shelve'
    shelve_dir.mkdir()
    gexf_dir = tmp_path / 'gexf'
    gexf_dir.mkdir()

    node1 = Node(1, adjacency_dict={2: {'weight': 3, 'status': True}})
    node2 = Node(2, adjacency_dict={1: {'weight': 3, 'status': True}})
    network = Network({1: node1, 2: node2})
    with shelve.open(str(shelve_dir / 'random_networks1')) as db:
        db['hospital_network1'] = network

    generate_networks.export_gexf(path=str(tmp_path))

    output_file = gexf_dir / 'hospital_network1.gexf'
    assert output_file.exists()
    assert output_file.read_text().startswith('<?xml')
