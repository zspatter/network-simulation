import pprint
from os.path import abspath, join

import openpyxl
import requests
from bs4 import BeautifulSoup

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
    distance_dict = dict()

    for node_id in network.nodes():
        node = network.network_dict[node_id]

        for adjacent_id in set(network.nodes()) - {node_id}:
            adjacent = network.network_dict[adjacent_id]
            weight = get_adjacent_weight(node=node, adjacent=adjacent)
            if weight:
                network.add_edge(node_id1=node_id,
                                 node_id2=adjacent_id,
                                 weight=weight,
                                 feedback=False)


def get_adjacent_weight(node, adjacent, weight=None):
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


def get_cities_distance_vector(worksheet):
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

    # creates a set of unique locations
    locations = set()
    for x in range(2, worksheet.max_row + 1):
        locations.add((worksheet.cell(row=x, column=column_indices['city']).value,
                       worksheet.cell(row=x, column=column_indices['state']).value,
                       int(worksheet.cell(row=x, column=column_indices['region']).value)))

    #
    distance_vector = dict()

    for location in locations:
        origin_city, origin_state, origin_region = location
        adjacents = dict()
        for destination_city, destination_state, region in locations:
            if region == origin_region or region in neighbor_regions[origin_region]:
                # adjacents[(city, state, region)]
                adjacents.setdefault((destination_city, destination_state, region), None)
        distance_vector[location] = adjacents

    for location in distance_vector:
        source_city, source_state, source_region = location
        source_region = location[2]
        for destination in distance_vector[location]:
            destination_city, destination_state, destination_region = destination
            # verify source/destiantion are adjacent regions and distance
            # values are not already set
            if destination_region in neighbor_regions[source_region]\
                    and not (distance_vector[location][destination]
                             or distance_vector[destination][location]):
                distance = get_distance(source_city=source_city,
                                        source_state=source_state,
                                        destination_city=destination_city,
                                        destination_state=destination_state)
                # verify distance value
                if distance:
                    print(f"{f'{source_city}, {source_state}':<30}"
                          f"{f'{destination_city}, {destination_state}':<30}{f'{distance:,} miles':>12}")
                    distance_vector[location][destination] = distance
                    distance_vector[destination][location] = distance

    pprint.pprint(distance_vector)

    # for city, state, region in sorted(sorted(locations, key=lambda tup: tup[1]), key=lambda tup: tup[2]):
    # for city, state, region in sort_locations(locations):
    #     print(f'{city:<18}{state:<16} {f"(region: {region})":>12}')

    # for node in network.nodes():
    #     for adjacent in network.network_dict[node].get_adjacents():


def get_distance(source_city, source_state, destination_city, destination_state):
    url = f'https://www.distance-cities.com/searchbd' \
        f'?from={source_city}%2C{source_state}' \
        f'&to={destination_city}%2C{destination_state}'

    try:
        res = requests.get(url=url, headers={"Accept": "text/html"})
        res.raise_for_status()

        soup = BeautifulSoup(res.content, features='lxml')
        distance_elem = soup.select('#sud')
        if distance_elem:
            value = int(distance_elem[0].text.split()[0].replace(',', ''))
            return value
    except requests.exceptions.HTTPError as e:
        print(f'Error downloading webpage {url}', e)


def sort_locations(locations):
    sorted_locations = sorted(locations, key=lambda tup: tup[0])
    sorted_locations = sorted(sorted_locations, key=lambda tup: tup[1])
    sorted_locations = sorted(sorted_locations, key=lambda tup: tup[2])
    return sorted_locations


if __name__ == '__main__':
    path = join(abspath('.'), 'import', 'workbooks', 'National_Transplant_Hospitals.xlsx')
    workbook = openpyxl.load_workbook(filename=path)
    sheet = workbook.active

    column_indices = set_default_indices()
    get_column_indices(worksheet=sheet, columns=column_indices)
    # imported_nodes = import_nodes(worksheet=sheet)
    #
    # print(imported_nodes)
    get_cities_distance_vector(worksheet=sheet)
