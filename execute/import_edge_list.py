import csv
from os.path import abspath, join

from network_simulator.exceptions import GraphElementError
from network_simulator.Network import Network
from network_simulator.Node import Node


def import_edge_list(path, delimiter='\t'):
    data = [[], [], []]
    with open(file=path, mode='r', newline='') as csv_in:
        reader = csv.reader(csv_in, delimiter=delimiter)
        for row in reader:
            data[0].append(int(row[0]))
            data[1].append(int(row[1]))
            data[2].append(int(row[2])) if len(row) == 3 else data[2].append(None)

    return data


def get_nodes(data):
    source_nodes = set(data[0])
    destination_nodes = set(data[1])
    return source_nodes | destination_nodes


def build_network(nodes, data):
    network = Network()
    for node in nodes:
        network.add_node(node=Node(node))

    return add_edges(network=network, data=data)


def add_edges(network, data):
    for x in range(len(data[0])):
        # an edge list may name a pair more than once (or in both directions);
        # skip the duplicate rather than fail the whole import
        try:
            network.add_edge(node_id1=data[0][x],
                             node_id2=data[1][x],
                             weight=data[2][x] if data[2][x] else 1)
        except GraphElementError:
            continue

    return network


if __name__ == '__main__':
    filepath = join(abspath('.'), 'import', 'edge_lists', 'edge_list.tsv')
    edge_list_data = import_edge_list(path=filepath)
    nodes_set = get_nodes(data=edge_list_data)
    net = build_network(nodes=nodes_set, data=edge_list_data)
    print(net)
