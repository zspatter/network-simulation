import shelve
from os.path import abspath, join

import networkx

from network_simulator.GraphConverter import GraphConverter


def export_gexf(path='.', filename='hospital_network', is_regional_weight=None):
    db = shelve.open(filename=path)
    hospital_network = db['hospital_network']

    nx = GraphConverter.convert_to_networkx(network=hospital_network,
                                            is_regional_weight=is_regional_weight)
    networkx.write_gexf(G=nx, path=filename)


if __name__ == '__main__':
    shelve_path = join(abspath('.'), 'export', 'shelve', 'distance_vector')
    export_root = join(abspath('.'), 'export', 'gexf')

    export_gexf(path=shelve_path,
                filename=join(export_root, 'hospital_network_distance.gexf'))
    export_gexf(path=shelve_path,
                filename=join(export_root, 'hospital_network_regional.gexf'),
                is_regional_weight=True)
