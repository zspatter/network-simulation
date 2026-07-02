import sys
from os.path import abspath, dirname, join

import openpyxl

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

import import_hospitals  # noqa: E402

from network_simulator.Network import Network  # noqa: E402
from network_simulator.Node import Node  # noqa: E402

_HEADERS = ('unique id', 'hospital name', 'city', 'state', 'region', 'latitude', 'longitude')


def _build_worksheet(rows):
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(list(_HEADERS))
    for row in rows:
        worksheet.append([row[header] for header in _HEADERS])
    return worksheet


def test_set_default_indices_returns_every_field_unset():
    columns = import_hospitals.set_default_indices()

    assert set(columns.keys()) == set(_HEADERS)
    assert all(value is None for value in columns.values())


def test_get_column_indices_maps_header_names_to_column_letters():
    worksheet = _build_worksheet([])
    columns = import_hospitals.set_default_indices()

    import_hospitals.get_column_indices(worksheet=worksheet, columns=columns)

    assert columns['unique id'] == 'A'
    assert columns['hospital name'] == 'B'
    assert columns['region'] == 'E'
    assert columns['longitude'] == 'G'


def test_import_nodes_builds_a_network_with_coordinates_and_region():
    rows = [
        {'unique id': 1, 'hospital name': 'Hospital A', 'city': 'Austin', 'state': 'TX',
         'region': 4, 'latitude': 30.27, 'longitude': -97.74},
        {'unique id': 2, 'hospital name': 'Hospital B', 'city': 'Dallas', 'state': 'TX',
         'region': 4, 'latitude': 32.78, 'longitude': -96.80},
    ]
    worksheet = _build_worksheet(rows)
    columns = import_hospitals.set_default_indices()
    import_hospitals.get_column_indices(worksheet=worksheet, columns=columns)

    network = import_hospitals.import_nodes(worksheet=worksheet, column_indices=columns,
                                            neighbor_regions={})

    assert set(network.network_dict.keys()) == {1, 2}
    assert network.network_dict[1].city == 'Austin'
    assert network.network_dict[1].region == 4
    # same region, different city, same state -> regional_weight 2 (see
    # get_adjacent_regional_weight), so an edge should have been added
    assert 2 in network.network_dict[1].adjacency_dict


def test_get_adjacent_regional_weight_same_city_and_state_is_weight_one():
    source = Node(1, region=4, city='Austin', state='TX')
    adjacent = Node(2, region=4, city='Austin', state='TX')

    assert import_hospitals.get_adjacent_regional_weight(source, adjacent, {}) == 1


def test_get_adjacent_regional_weight_same_region_and_state_different_city_is_weight_two():
    source = Node(1, region=4, city='Austin', state='TX')
    adjacent = Node(2, region=4, city='Dallas', state='TX')

    assert import_hospitals.get_adjacent_regional_weight(source, adjacent, {}) == 2


def test_get_adjacent_regional_weight_same_region_different_state_is_weight_three():
    source = Node(1, region=4, city='Austin', state='TX')
    adjacent = Node(2, region=4, city='Little Rock', state='AR')

    assert import_hospitals.get_adjacent_regional_weight(source, adjacent, {}) == 3


def test_get_adjacent_regional_weight_different_region_same_state_is_weight_three():
    # the Virginia special case: a state can straddle two OPTN regions
    source = Node(1, region=1, city='Richmond', state='VA')
    adjacent = Node(2, region=2, city='Norfolk', state='VA')

    assert import_hospitals.get_adjacent_regional_weight(source, adjacent, {}) == 3


def test_get_adjacent_regional_weight_neighboring_region_is_weight_four():
    source = Node(1, region=1, city='Boston', state='MA')
    adjacent = Node(2, region=9, city='New York', state='NY')

    assert import_hospitals.get_adjacent_regional_weight(source, adjacent, {1: [9]}) == 4


def test_get_adjacent_regional_weight_unrelated_regions_returns_none():
    source = Node(1, region=1, city='Boston', state='MA')
    adjacent = Node(2, region=5, city='Chicago', state='IL')

    assert import_hospitals.get_adjacent_regional_weight(source, adjacent, {1: [9]}) is None


def test_node_pair_generator_yields_every_ordered_pair():
    network = Network({1: Node(1), 2: Node(2), 3: Node(3)})

    pairs = list(import_hospitals.node_pair_generator(network))

    assert len(pairs) == 6  # 3 nodes -> 3 * 2 ordered pairs (excludes self-pairs)


def test_generate_distance_vector_adds_edges_between_same_region_nodes():
    network = Network({
        1: Node(1, region=4, city='Austin', state='TX', latitude=30.27, longitude=-97.74),
        2: Node(2, region=4, city='Dallas', state='TX', latitude=32.78, longitude=-96.80),
    })

    import_hospitals.generate_distance_vector(network=network, neighbor_regions={})

    assert 2 in network.network_dict[1].adjacency_dict
    assert network.network_dict[1].adjacency_dict[2]['weight'] > 0


def test_generate_distance_vector_skips_unrelated_regions():
    network = Network({
        1: Node(1, region=1, city='Boston', state='MA', latitude=42.36, longitude=-71.06),
        2: Node(2, region=5, city='Chicago', state='IL', latitude=41.88, longitude=-87.63),
    })

    import_hospitals.generate_distance_vector(network=network, neighbor_regions={1: [9]})

    assert network.network_dict[1].adjacency_dict == {}
