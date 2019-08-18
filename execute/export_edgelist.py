import shelve
from pathlib import Path


def generate_edgelist(network, output_path=Path('edgelist.txt')):
    """
    Takes a network object and exports it's edge list to the output path

    :param network_simulator.Network network: source network
    :param Path output_path: path to resulting output
    """
    with output_path.open('w') as out:
        for node in network.nodes():
            adjacents = network.network_dict[node].get_adjacents()
            lines = [f'{node} {x}\n' for x in adjacents]
            out.writelines(lines)


if __name__ == '__main__':
    db = shelve.open(str(Path('./export/shelve/distance_vector')))
    hospital_network = db['hospital_network']
    generate_edgelist(network=hospital_network,
                      output_path=Path('./export/edgelist/hospital_edgelist'))
