import shelve
from pathlib import Path


def generate_edge_list(network, output_path=Path('edgelist.txt')):
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


def unique_edge_list(network):
    """
    Generates an edge list with only unique edges. This removes duplicates
    resulting from the bidirectional nature of the edges.

    :param network_simulator.Network network: source network
    :return: list edge_list: unique set of edges
    """
    edge_list = []
    nodes = [network.network_dict[node] for node in network.nodes()]

    for node in nodes:
        adjacents = node.get_adjacents()
        for adjacent in adjacents:
            edge = (node.node_id, adjacent)
            alternate = (adjacent, node.node_id)
            if edge not in edge_list and alternate not in edge_list:
                edge_list.append(edge)

    return edge_list


def write_edge_list(edge_list, output_path):
    """
    Takes an edge list (list of integer pairs as tuples) and
    exports the edge list as plaintext

    :param list edge_list: list of unique edges (node pairs)
    :param Path output_path: path to resulting output
    """
    with output_path.open('w') as out:
        lines = '\n'.join(map(lambda x: f'{x[0]} {x[1]}', edge_list))
        out.writelines(lines)


if __name__ == '__main__':
    db = shelve.open(str(Path('./export/shelve/distance_vector')))
    hospital_network = db['hospital_network2']
    # generate_edge_list(network=hospital_network,
    #                    output_path=Path('./export/edgelist/hospital_edge_list2'))

    edges = unique_edge_list(network=hospital_network)
    write_edge_list(edge_list=edges,
                    output_path=Path('./export/edgelist/unique_edge_list'))
