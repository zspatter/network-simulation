from os.path import abspath, join

import openpyxl

from network_simulator.Network import Network
from network_simulator.Node import Node

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

fields = ('unique id',
          'hospital name',
          'city',
          'state',
          'region')
column_indices = {}

for field in fields:
    column_indices.setdefault(field, None)


def get_column_indices(worksheet):
    for x in range(1, 7):
        cell = worksheet.cell(row=1, column=x).value.lower()
        if cell in column_indices:
            column_indices[cell] = x


def import_nodes(worksheet):
    network = Network()
    for x in range(2, worksheet.max_row):
        network.add_node(
                node=Node(
                        node_id=int(
                                worksheet.cell(row=x, column=column_indices['unique id']).value),
                        label=worksheet.cell(row=x, column=column_indices['hospital name']).value,
                        region=int(worksheet.cell(row=x, column=column_indices['region']).value),
                        city=worksheet.cell(row=x, column=column_indices['city']).value,
                        state=worksheet.cell(row=x, column=column_indices['state']).value),
                feedback=False)

    generate_distance_vector(network=network)

    return network


def generate_distance_vector(network):
    for node_id in network.nodes():
        node = network.network_dict[node_id]

        for adjacent_id in set(network.nodes()) - {node_id}:
            adjacent = network.network_dict[adjacent_id]
            weight = get_adjacent_weight(adjacent, node)
            network.add_edge(node_id1=node_id,
                             node_id2=adjacent_id,
                             weight=weight,
                             feedback=False)


def get_adjacent_weight(adjacent, node):
    weight = float('inf')

    if node.city == adjacent.city and node.state == adjacent.state:
        weight = 1
    elif node.state == adjacent.state and node.city != adjacent.state:
        weight = 2
    elif node.region == adjacent.region and node.state != adjacent.state:
        weight = 3
    elif node.region != adjacent.region and \
            adjacent.region in neighbor_regions[node.region]:
        weight = 4

    return weight


if __name__ == '__main__':
    path = join(abspath('.'), 'workbooks', 'National_Transplant_Hospitals.xlsx')
    workbook = openpyxl.load_workbook(filename=path)
    sheet = workbook.active

    get_column_indices(worksheet=sheet)
    imported_nodes = import_nodes(worksheet=sheet)
    print(imported_nodes)
