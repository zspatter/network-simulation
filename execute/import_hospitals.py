"""
Builds a Network of real US transplant-system locations from the OPTN membership directory
(https://www.hrsa.gov/optn/about/membership/optn-membership-database), geocoded via the free US
Census Bureau geocoder (https://geocoding.geo.census.gov - no API key needed). Replaces the old
2019 xlsx + Bing Maps pipeline: Bing Maps' free/basic tier was retired by Microsoft on June 30,
2025, and the Census geocoder is strictly more precise besides, since it geocodes the full
street address rather than just city/state (a city-center point).

Only two OPTN membership `organizationType`s are physical locations this simulation models:
'Transplant Hospital' (where patients wait and transplants happen) and 'Independent OPO' /
'Hospital Based OPO' (Organ Procurement Organizations - who actually coordinate organ recovery;
a transplant hospital performs transplants but doesn't necessarily procure the organ itself).
Everything else in the membership directory (labs, business/individual/public/scientific
members) isn't a location this simulation places patients or organs at.

Some rows share a `centerCode` (e.g. a hospital-based OPO co-located with its affiliated
transplant hospital) but are still distinct physical addresses - checked directly against the
membership CSV - so every row gets its own Node rather than being deduplicated by centerCode.
"""
import csv
import io
import shelve
import time
from os.path import abspath, join

import requests

from organflow.distance import estimate_transit_hours, haversine_km
from organflow.Network import Network
from organflow.Node import Node

PHYSICAL_LOCATION_TYPES = {'Transplant Hospital', 'Independent OPO', 'Hospital Based OPO'}

CENSUS_BATCH_URL = 'https://geocoding.geo.census.gov/geocoder/locations/addressbatch'
CENSUS_BENCHMARK = 'Public_AR_Current'

# Fallback for the ~10% of hospital addresses the Census geocoder can't match - large campus
# addresses (e.g. "One Medical Center Drive") often aren't in TIGER/Line's street reference data
# at all, no matter how the query is reformatted (verified directly - zip+4 vs 5-digit zip vs no
# zip made no difference). Nominatim (OpenStreetMap) resolves all of these in testing. Its usage
# policy caps free use at 1 request/second and requires a descriptive User-Agent identifying the
# application - fine here since this only runs for a handful of per-row fallback lookups, not the
# whole batch.
NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
NOMINATIM_USER_AGENT = 'organflow (hospital network data refresh)'
NOMINATIM_RATE_LIMIT_SECONDS = 1.0


def read_membership_csv(path):
    """
    Reads the OPTN membership CSV into a list of row dicts (one dict per member, keyed by the
    CSV's header names - region, centerCode, organizationType, accountName, address1, city,
    state, zipCode, membershipStatus, etc.).

    :param str path: path to the OPTN membership CSV export
    :return: list of row dicts
    """
    with open(path, newline='', encoding='utf-8-sig') as csv_in:
        return list(csv.DictReader(csv_in))


def filter_physical_locations(rows):
    """
    Keeps only rows that are both a real physical location this simulation models
    (PHYSICAL_LOCATION_TYPES) and currently Approved (drops "Interim Approval-Pending BOD
    Action" rows - not yet real capacity).

    :param rows: rows from read_membership_csv()
    :return: filtered rows
    """
    return [row for row in rows
           if row['membershipStatus'] == 'Approved'
           and row['organizationType'] in PHYSICAL_LOCATION_TYPES]


def geocode_addresses(rows):
    """
    Batch-geocodes every row's street address via the free US Census Bureau geocoder in a
    single request (rather than one request per row), then individually retries via Nominatim
    (rate-limited) any address the Census geocoder couldn't match.

    :param rows: row dicts with 'address1', 'city', 'state', 'zipCode' keys
    :return: {row index (0-based, matching `rows` order): (latitude, longitude)} - a row is
        omitted only if neither geocoder could match its address
    """
    coordinates = _geocode_via_census(rows)

    missing = [index for index in range(len(rows)) if index not in coordinates]
    for index in missing:
        coordinate = _geocode_via_nominatim(rows[index])
        if coordinate:
            coordinates[index] = coordinate
        time.sleep(NOMINATIM_RATE_LIMIT_SECONDS)

    return coordinates


def _geocode_via_census(rows):
    """One batch call to the Census geocoder - see geocode_addresses()."""
    batch_csv = io.StringIO()
    writer = csv.writer(batch_csv)
    for index, row in enumerate(rows):
        writer.writerow([index, row['address1'], row['city'], row['state'], row['zipCode']])

    response = requests.post(
            CENSUS_BATCH_URL,
            files={'addressFile': ('batch.csv', batch_csv.getvalue(), 'text/csv')},
            data={'benchmark': CENSUS_BENCHMARK})
    response.raise_for_status()

    coordinates = {}
    for line in csv.reader(io.StringIO(response.text)):
        if not line or line[2] != 'Match':
            continue
        longitude, latitude = line[5].split(',')
        coordinates[int(line[0])] = (float(latitude), float(longitude))
    return coordinates


def _geocode_via_nominatim(row):
    """
    One rate-limited fallback lookup via Nominatim - see geocode_addresses(). Institutional
    campus addresses (e.g. "One Medical Center Drive") are frequently missing from Census'
    TIGER/Line street reference data outright, regardless of how the query is formatted, but
    Nominatim's broader (OpenStreetMap-derived) index resolves them.

    :param dict row: a single row dict with 'address1', 'city', 'state' keys
    :return: (latitude, longitude), or None if Nominatim also found no match
    """
    query = f"{row['address1']}, {row['city']}, {row['state']}"
    response = requests.get(NOMINATIM_URL, params={'q': query, 'format': 'json', 'limit': 1},
                            headers={'User-Agent': NOMINATIM_USER_AGENT})
    response.raise_for_status()

    matches = response.json()
    if not matches:
        return None
    return float(matches[0]['lat']), float(matches[0]['lon'])


def import_nodes(rows, neighbor_regions):
    """
    Builds a Network from membership rows already filtered by filter_physical_locations(): one
    Node per row (sequential node_id over successfully-geocoded rows only), then wires edges via
    generate_distance_vector().

    :param rows: filtered rows (see filter_physical_locations())
    :param dict neighbor_regions: {region: [adjacent region, ...]}, forwarded to
        get_adjacent_regional_weight() via generate_distance_vector()
    :return: (Network, transplant_hospital_ids, opo_ids) - the latter two are the node_id sets
        by role, for restricting where patients vs. organs are generated - see
        organflow.PatientGenerator/OrganGenerator's eligible_nodes parameter
    """
    coordinates = geocode_addresses(rows)
    geocoded_rows = [(row, coordinates[index]) for index, row in enumerate(rows)
                     if index in coordinates]

    network = Network()
    transplant_hospital_ids = set()
    opo_ids = set()

    for node_id, (row, (latitude, longitude)) in enumerate(geocoded_rows, start=1):
        network.add_node(
                node=Node(node_id=node_id,
                          hospital_name=row['accountName'],
                          region=int(row['region']),
                          city=row['city'],
                          state=row['state'],
                          latitude=latitude,
                          longitude=longitude))

        if row['organizationType'] == 'Transplant Hospital':
            transplant_hospital_ids.add(node_id)
        else:
            opo_ids.add(node_id)

    generate_distance_vector(network=network, neighbor_regions=neighbor_regions)
    return network, transplant_hospital_ids, opo_ids


def generate_distance_vector(network, neighbor_regions):
    """
    Computes the weight (estimated transit hours - see
    organflow.distance) between every pair of nodes directly from
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
                             regional_weight=regional_weight)


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

    csv_path = join(abspath('.'), 'import', 'optn_membership', 'optn_membership_2026-07-02.csv')
    membership_rows = filter_physical_locations(read_membership_csv(csv_path))

    hospital_network, transplant_hospital_ids, opo_ids = import_nodes(
            rows=membership_rows, neighbor_regions=neighbor_regions)

    with shelve.open(join(root, 'distance_vector')) as db:
        db['hospital_network2'] = hospital_network
        db['transplant_hospital_ids'] = transplant_hospital_ids
        db['opo_ids'] = opo_ids

    print(hospital_network)
