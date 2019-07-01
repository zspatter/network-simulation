from os.path import abspath, join

import openpyxl

from network_simulator.Network import Network
from network_simulator.Node import Node


def set_default_indices():
    """
    Sets default dict for columns (placeholders for indices)
    """
    fields = ('unique id',
              'hospital name',
              'city',
              'state',
              'region')
    columns = {}
    for field in fields:
        columns.setdefault(field, None)

    return columns


def get_column_indices(worksheet, columns):
    """
    Gets index for each column for reading data

    :param Worksheet worksheet: worksheet to read
    :param dict columns: expected columns to store indices
    """
    for x in range(1, 7):
        cell = worksheet.cell(row=1, column=x).value.lower()
        if cell in columns:
            columns[cell] = x


def import_nodes(worksheet):
    """
    Imports node from each row and adds it to the network. These nodes
    only contain the following fields: node_id, hospital_name, region,
    city, and state. (adjacency_dict is handled in generate_distance_vector()
    and status is assumed to be True)

    :param Worksheet worksheet: worksheet to read data from
    :return: Network
    """
    network = Network()
    for x in range(2, worksheet.max_row + 1):
        network.add_node(
                node=Node(
                        node_id=int(
                                worksheet.cell(row=x, column=column_indices['unique id']).value),
                        hospital_name=worksheet.cell(row=x,
                                                     column=column_indices['hospital name']).value,
                        region=int(worksheet.cell(row=x, column=column_indices['region']).value),
                        city=worksheet.cell(row=x, column=column_indices['city']).value,
                        state=worksheet.cell(row=x, column=column_indices['state']).value),
                feedback=False)

    generate_distance_vector(network=network)
    return network


def generate_distance_vector(network):
    """
    Finds weight from any given node to all other given node in the
    network using the city, state, and region parameters

    :param Network network:
    """
    for node_id in network.nodes():
        node = network.network_dict[node_id]

        for adjacent_id in set(network.nodes()) - {node_id}:
            adjacent = network.network_dict[adjacent_id]
            weight = get_adjacent_weight(node=node, adjacent=adjacent)
            network.add_edge(node_id1=node_id,
                             node_id2=adjacent_id,
                             weight=weight,
                             feedback=False)


def get_adjacent_weight(node, adjacent, weight=float('inf')):
    """
    Calculates weight based up on city, state, and region fields for
    both the node and adjacent

    :param Node node: current source node
    :param Node adjacent: current destination node
    :param float weight: default max weight
    :return: weight
    """
    # special case for hawaii?
    neighbor_regions = {1:  [9],
                        2:  [9, 10, 11],
                        3:  [4, 8, 11],  # 3 -> 8?
                        4:  [3, 5, 8],
                        5:  [4, 6, 8],
                        6:  [5, 7, 8],
                        7:  [6, 8, 10],  # 7 -> 11?
                        8:  [3, 4, 5, 6, 7],  # 8 -> 11?
                        9:  [1, 2],
                        10: [2, 7, 11],
                        11: [2, 3, 10]}  # 11 -> 7/8?

    if node.region == adjacent.region:
        if node.city == adjacent.city and node.state == adjacent.state:
            weight = 1
        elif node.state == adjacent.state and node.city != adjacent.city:
            weight = 2
        elif node.state != adjacent.state:
            weight = 3
    # condition for Virginia
    elif node.state == adjacent.state:
        weight = 3
    elif adjacent.region in neighbor_regions[node.region]:
        weight = 4

    return weight


if __name__ == '__main__':
    path = join(abspath('.'), 'workbooks', 'National_Transplant_Hospitals.xlsx')
    workbook = openpyxl.load_workbook(filename=path)
    sheet = workbook.active

    column_indices = set_default_indices()
    get_column_indices(worksheet=sheet, columns=column_indices)
    imported_nodes = import_nodes(worksheet=sheet)

    print(imported_nodes)
