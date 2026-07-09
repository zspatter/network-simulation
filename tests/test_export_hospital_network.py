import shelve
import sys
from os.path import abspath, dirname, join

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

import export_hospital_network  # noqa: E402

from organflow.Network import Network  # noqa: E402
from organflow.Node import Node  # noqa: E402


def _small_network():
    node1 = Node(1, region=4, city='Austin', state='TX',
                adjacency_dict={2: {'weight': 3, 'status': True}})
    node2 = Node(2, region=4, city='Dallas', state='TX',
                adjacency_dict={1: {'weight': 3, 'status': True}})
    return Network({1: node1, 2: node2})


def test_export_gexf_without_attributes(tmp_path):
    shelve_path = tmp_path / 'distance_vector'
    with shelve.open(str(shelve_path)) as db:
        db['hospital_network2'] = _small_network()
    output_path = tmp_path / 'hospital_network.gexf'

    export_hospital_network.export_gexf(import_path=str(shelve_path), export_path=str(output_path))

    assert output_path.exists()
    assert output_path.read_text().startswith('<?xml')


def test_export_gexf_with_state_and_region_attributes(tmp_path):
    shelve_path = tmp_path / 'distance_vector'
    with shelve.open(str(shelve_path)) as db:
        db['hospital_network2'] = _small_network()
    output_path = tmp_path / 'hospital_network_attrs.gexf'

    export_hospital_network.export_gexf(import_path=str(shelve_path), export_path=str(output_path),
                                        state_dict={'TX': 2}, region_dict={4: 2})

    assert output_path.exists()
    assert output_path.read_text().startswith('<?xml')
