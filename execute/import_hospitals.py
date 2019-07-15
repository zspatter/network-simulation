import shelve
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
            node=Node(node_id=int(worksheet.cell(x, column_indices['unique id']).value),
                      hospital_name=worksheet.cell(x, column_indices['hospital name']).value,
                      region=int(worksheet.cell(x, column_indices['region']).value),
                      city=worksheet.cell(x, column_indices['city']).value,
                      state=worksheet.cell(x, column_indices['state']).value),
            feedback=False)

    generate_distance_vector(network=network)
    return network


def generate_distance_vector(network):
    """
    Finds weight from any given node to all other given node in the
    network using the city, state, and region parameters

    :param Network network:
    """
    for source, adjacent in node_pair_generator(network=network):
        weight = lookup_weight(source=source,
                               adjacent=adjacent)
        regional_weight = get_adjacent_regional_weight(source=source,
                                                       adjacent=adjacent)

        if weight and regional_weight:
            network.add_edge(node_id1=source.node_id,
                             node_id2=adjacent.node_id,
                             weight=weight,
                             regional_weight=regional_weight,
                             feedback=False)


def lookup_weight(source, adjacent):
    source_location = (source.city, source.state, source.region)
    adjacent_location = (adjacent.city, adjacent.state, adjacent.region)

    if source_location in distance_matrix \
            and adjacent_location in distance_matrix[source_location]:
        return distance_matrix[source_location][adjacent_location]


def node_pair_generator(network):
    for node_id in network.nodes():
        source = network.network_dict[node_id]

        for adjacent_id in set(network.nodes()) - {node_id}:
            adjacent = network.network_dict[adjacent_id]

            yield source, adjacent


def get_adjacent_regional_weight(source, adjacent, weight=None):
    """
    Calculates weight based up on city, state, and region fields for
    both the node and adjacent

    :param Node source: current source node
    :param Node adjacent: current destination node
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


def get_unique_locations(worksheet):
    # creates a set of unique locations
    locations = set()
    for x in range(2, worksheet.max_row + 1):
        locations.add((worksheet.cell(row=x, column=column_indices['city']).value,
                       worksheet.cell(row=x, column=column_indices['state']).value,
                       int(worksheet.cell(row=x, column=column_indices['region']).value)))
    return locations


def set_default_distances(locations):
    distance_dict = dict()
    for location in locations:
        _, _, origin_region = location
        adjacents = dict()
        for destination_city, destination_state, region in locations:
            if region == origin_region or region in neighbor_regions[origin_region]:
                adjacents.setdefault((destination_city, destination_state, region), None)
        distance_dict[location] = adjacents
    return distance_dict


def get_distances(distance_vector):
    for source in distance_vector:
        source_city, source_state, source_region = source
        source_region = source[2]
        for destination in distance_vector[source]:
            destination_city, destination_state, destination_region = destination
            # if city/state are same for source and destination
            if source == destination:
                distance_vector[source][destination] = 1
                distance_vector[destination][source] = 1
            # verify source/destination are adjacent regions and distance
            # values are not already set
            elif destination_region in neighbor_regions[source_region] \
                    and not (distance_vector[source][destination]
                             or distance_vector[destination][source]):
                distance = get_distance(source_city=source_city,
                                        source_state=source_state,
                                        destination_city=destination_city,
                                        destination_state=destination_state)
                # verify distance value
                if distance:
                    print(f"{f'{source_city}, {source_state}':<30}"
                          f"{f'{destination_city}, {destination_state}':<30}"
                          f"{f'{distance:,} km':>12}")
                    distance_vector[source][destination] = distance
                    distance_vector[destination][source] = distance

    return distance_vector


def get_distance(source_city, source_state, destination_city, destination_state):
    url = f'https://www.distance-cities.com/searchbd' \
        f'?from={source_city}%2C{source_state}' \
        f'&to={destination_city}%2C{destination_state}'

    try:
        res = requests.get(url=url, headers={"Accept": "text/html"})
        res.raise_for_status()

        soup = BeautifulSoup(res.content, features='lxml')
        distance_elem = soup.select('#rkm')

        if distance_elem:
            value = float(distance_elem[0].text.split()[0].replace(',', ''))
            return value
    except requests.exceptions.HTTPError as e:
        print(f'Error downloading webpage {url}', e)


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

    path = join(abspath('.'), 'import', 'workbooks',
                'National_Transplant_Hospitals_coordinates.xlsx')
    workbook = openpyxl.load_workbook(filename=path)
    sheet = workbook.active

    column_indices = set_default_indices()
    get_column_indices(worksheet=sheet, columns=column_indices)

    # cities = get_unique_locations(worksheet=sheet)
    # distance_matrix = set_default_distances(locations=cities)
    # distance_matrix = get_distances(distance_vector=distance_matrix)

    root = join(abspath('.'), 'export', 'shelve')
    db = shelve.open(join(root, 'distance_vector'))
    distance_matrix = db['distance_vector']

    hospital_network = import_nodes(worksheet=sheet)
    db['hospital_network'] = hospital_network
    print(hospital_network)
