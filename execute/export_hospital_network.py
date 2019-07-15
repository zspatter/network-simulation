import shelve
from os.path import abspath, basename, join

import networkx

from network_simulator.GraphConverter import GraphConverter


def export_gexf(import_path='.',
                shelve_key='hospital_network',
                export_path='hospital_network.gexf',
                is_regional_weight=None):
    """
    This function exports the shelve_variable value within the shelve file
    stored at path. This network is then converted to a networkx object
    and exported in GEXF format at filename.

    :param str import_path: shelve filepath
    :param str shelve_key: name of key network is stored as
    :param str export_path: export filepath
    :param bool is_regional_weight: indicates whether or not regional
            weight should be weight metric
    """
    db = shelve.open(filename=import_path)
    hospital_network = db[shelve_key]

    nx = GraphConverter.convert_to_networkx(network=hospital_network,
                                            is_regional_weight=is_regional_weight)
    networkx.write_gexf(G=nx, path=export_path)
    print(f"'{basename(export_path)}' has been successfully exported to: {export_path}\n")


if __name__ == '__main__':
    shelve_path = join(abspath('.'), 'export', 'shelve', 'distance_vector')
    export_root = join(abspath('.'), 'export', 'gexf')

    export_gexf(import_path=shelve_path,
                export_path=join(export_root, 'hospital_network_distance.gexf'))
    export_gexf(import_path=shelve_path,
                export_path=join(export_root, 'hospital_network_regional.gexf'),
                is_regional_weight=True)
