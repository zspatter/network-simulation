import sys
from os.path import abspath, dirname, join

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

import import_hospitals  # noqa: E402

from organflow.Network import Network  # noqa: E402
from organflow.Node import Node  # noqa: E402


class _FakeResponse:
    """Minimal stand-in for requests.Response - .text for Census, .json() for Nominatim."""
    def __init__(self, text=None, json_body=None):
        self.text = text
        self._json_body = json_body

    def raise_for_status(self):
        pass

    def json(self):
        return self._json_body


def test_filter_physical_locations_keeps_only_approved_hospitals_and_opos():
    rows = [
        {'organizationType': 'Transplant Hospital', 'membershipStatus': 'Approved'},
        {'organizationType': 'Independent OPO', 'membershipStatus': 'Approved'},
        {'organizationType': 'Hospital Based OPO', 'membershipStatus': 'Approved'},
        {'organizationType': 'Hospital Based Lab', 'membershipStatus': 'Approved'},
        {'organizationType': 'Transplant Hospital',
         'membershipStatus': 'Interim Approval-Pending BOD Action'},
    ]

    filtered = import_hospitals.filter_physical_locations(rows)

    assert len(filtered) == 3
    assert {row['organizationType'] for row in filtered} == \
        {'Transplant Hospital', 'Independent OPO', 'Hospital Based OPO'}


def test_read_membership_csv_reads_rows(tmp_path):
    path = tmp_path / 'membership.csv'
    path.write_text('region,organizationType,membershipStatus,accountName,address1,city,'
                    'state,zipCode\n3,Transplant Hospital,Approved,Test Hospital,100 Main St,'
                    'Testville,AL,35233\n')

    rows = import_hospitals.read_membership_csv(str(path))

    assert len(rows) == 1
    assert rows[0]['accountName'] == 'Test Hospital'
    assert rows[0]['region'] == '3'


def test_geocode_addresses_uses_census_batch_result_and_falls_back_to_nominatim(monkeypatch):
    rows = [
        {'address1': '100 Main St', 'city': 'Testville', 'state': 'AL', 'zipCode': '35233'},
        {'address1': '200 Oak Ave', 'city': 'Otherville', 'state': 'AL', 'zipCode': '35234'},
    ]
    census_csv = (
        '"0","100 Main St, Testville, AL, 35233","Match","Exact",'
        '"100 MAIN ST, TESTVILLE, AL, 35233","-86.8,33.5","123","L"\n'
        '"1","200 Oak Ave, Otherville, AL, 35234","No_Match"\n'
    )
    monkeypatch.setattr(import_hospitals.requests, 'post',
                       lambda *a, **k: _FakeResponse(text=census_csv))
    monkeypatch.setattr(import_hospitals.requests, 'get',
                       lambda *a, **k: _FakeResponse(json_body=[{'lat': '33.6', 'lon': '-86.9'}]))
    monkeypatch.setattr(import_hospitals.time, 'sleep', lambda *_: None)

    coordinates = import_hospitals.geocode_addresses(rows)

    assert coordinates[0] == (33.5, -86.8)  # resolved directly by Census
    assert coordinates[1] == (33.6, -86.9)  # resolved by the Nominatim fallback


def test_geocode_addresses_omits_a_row_neither_geocoder_can_match(monkeypatch):
    rows = [{'address1': 'nowhere', 'city': 'nowhere', 'state': 'ZZ', 'zipCode': '00000'}]
    monkeypatch.setattr(import_hospitals.requests, 'post',
                       lambda *a, **k: _FakeResponse(text='"0","nowhere","No_Match"\n'))
    monkeypatch.setattr(import_hospitals.requests, 'get',
                       lambda *a, **k: _FakeResponse(json_body=[]))
    monkeypatch.setattr(import_hospitals.time, 'sleep', lambda *_: None)

    assert import_hospitals.geocode_addresses(rows) == {}


def test_import_nodes_tags_node_ids_by_organizationType(monkeypatch):
    rows = [
        {'accountName': 'Hospital A', 'region': '4', 'city': 'Austin', 'state': 'TX',
         'organizationType': 'Transplant Hospital'},
        {'accountName': 'OPO B', 'region': '4', 'city': 'Austin', 'state': 'TX',
         'organizationType': 'Independent OPO'},
    ]
    monkeypatch.setattr(import_hospitals, 'geocode_addresses',
                        lambda rows: {0: (30.27, -97.74), 1: (30.28, -97.75)})

    network, transplant_hospital_ids, opo_ids = import_hospitals.import_nodes(
            rows, neighbor_regions={})

    assert set(network.network_dict.keys()) == {1, 2}
    assert transplant_hospital_ids == {1}
    assert opo_ids == {2}
    assert network.network_dict[1].city == 'Austin'
    assert network.network_dict[1].region == 4


def test_import_nodes_skips_rows_that_failed_to_geocode(monkeypatch):
    rows = [
        {'accountName': 'Hospital A', 'region': '4', 'city': 'Austin', 'state': 'TX',
         'organizationType': 'Transplant Hospital'},
        {'accountName': 'Hospital B (unresolved)', 'region': '4', 'city': 'Nowhere',
         'state': 'TX', 'organizationType': 'Transplant Hospital'},
    ]
    monkeypatch.setattr(import_hospitals, 'geocode_addresses',
                        lambda rows: {0: (30.27, -97.74)})  # row 1 has no match

    network, transplant_hospital_ids, opo_ids = import_hospitals.import_nodes(
            rows, neighbor_regions={})

    assert len(network.network_dict) == 1
    assert transplant_hospital_ids == {1}
    assert opo_ids == set()


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
