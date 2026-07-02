import shelve
from os.path import abspath, join

import openpyxl
from openpyxl.utils import get_column_letter

from network_simulator.distance import estimate_transit_hours, haversine_km
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
              'region',
              'latitude',
              'longitude')
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
    for x in range(1, 9):
        cell = worksheet[f'{get_column_letter(x)}1'].value
        if cell and cell.lower() in columns:
            columns[cell.lower()] = get_column_letter(x)


def import_nodes(worksheet, column_indices, neighbor_regions):
    """
    Imports a node from each row and adds it to the network. Nodes carry
    node_id, hospital_name, region, city, state, and coordinates (latitude/
    longitude); generate_distance_vector() uses the coordinates to compute
    edge weights directly instead of looking up a pre-scraped distance
    matrix (status is assumed to be True).

    :param Worksheet worksheet: worksheet to read data from
    :param dict column_indices: {field name: column letter}, from get_column_indices()
    :param dict neighbor_regions: {region: [adjacent region, ...]}, forwarded to
        get_adjacent_regional_weight() via generate_distance_vector()
    :return: Network
    """
    network = Network()
    for x in range(2, worksheet.max_row + 1):
        network.add_node(
                node=Node(node_id=int(worksheet[f'{column_indices["unique id"]}{x}'].value),
                          hospital_name=worksheet[f'{column_indices["hospital name"]}{x}'].value,
                          region=int(worksheet[f'{column_indices["region"]}{x}'].value),
                          city=worksheet[f'{column_indices["city"]}{x}'].value,
                          state=worksheet[f'{column_indices["state"]}{x}'].value,
                          latitude=float(worksheet[f'{column_indices["latitude"]}{x}'].value),
                          longitude=float(worksheet[f'{column_indices["longitude"]}{x}'].value)),
                feedback=False)

    generate_distance_vector(network=network, neighbor_regions=neighbor_regions)
    return network


def generate_distance_vector(network, neighbor_regions):
    """
    Computes the weight (estimated transit hours - see
    network_simulator.distance) between every pair of nodes directly from
    their coordinates via the haversine formula. This replaces the old
    pipeline that scraped driving/straight-line distances from a
    third-party site and cached them in a shelve-backed distance matrix.

    :param Network network:
    :param dict neighbor_regions: {region: [adjacent region, ...]}, forwarded to
        get_adjacent_regional_weight()
    """
    for source, adjacent in node_pair_generator(network=network):
        if source.node_id >= adjacent.node_id:
            continue  # undirected edge; only needs to be added once per pair

        regional_weight = get_adjacent_regional_weight(source=source, adjacent=adjacent,
                                                        neighbor_regions=neighbor_regions)
        if regional_weight:
            km = haversine_km(source.latitude, source.longitude,
                              adjacent.latitude, adjacent.longitude)
            network.add_edge(node_id1=source.node_id,
                             node_id2=adjacent.node_id,
                             weight=estimate_transit_hours(km),
                             regional_weight=regional_weight,
                             feedback=False)


def node_pair_generator(network):
    """
    Generator that yields all possible pairings of nodes

    :param Network network: source of nodes
    """
    for node_id in network.nodes():
        source = network.network_dict[node_id]

        for adjacent_id in set(network.nodes()) - {node_id}:
            adjacent = network.network_dict[adjacent_id]

            yield source, adjacent


def get_adjacent_regional_weight(source, adjacent, neighbor_regions, weight=None):
    """
    Calculates weight based up on city, state, and region fields for
    both the node and adjacent

    :param Node source: current source node
    :param Node adjacent: current destination node
    :param dict neighbor_regions: {region: [adjacent region, ...]}
    :param float weight: default max weight
    :return: weight
    """

    if source.region == adjacent.region:
        if source.city == adjacent.city and source.state == adjacent.state:
            weight = 1
        elif source.state == adjacent.state and source.city != adjacent.city:
            weight = 2
        elif source.state != adjacent.state:
            weight = 3
    # condition for Virginia
    elif source.state == adjacent.state:
        weight = 3
    elif adjacent.region in neighbor_regions[source.region]:
        weight = 4

    return weight


if __name__ == '__main__':
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

    root = join(abspath('.'), 'export', 'shelve')

    path = join(abspath('.'), 'import', 'workbooks',
                'National_Transplant_Hospitals_coordinates.xlsx')
    workbook = openpyxl.load_workbook(filename=path)
    sheet = workbook.active

    column_indices = set_default_indices()
    get_column_indices(worksheet=sheet, columns=column_indices)

    hospital_network = import_nodes(worksheet=sheet, column_indices=column_indices,
                                    neighbor_regions=neighbor_regions)

    with shelve.open(join(root, 'distance_vector')) as db:
        db['hospital_network2'] = hospital_network

    print(hospital_network)
