"""
Tallies OPTN membership rows by state and region, for the GEXF attribute annotation in
export_hospital_network.py. Reads the same membership CSV and physical-location filter as
import_hospitals.py, so the counts correspond to what's actually in the exported network.
"""
import shelve
from pathlib import Path

from import_hospitals import filter_physical_locations, read_membership_csv


def get_unique_states(rows):
    return sorted({row['state'] for row in rows})


def get_unique_regions(rows):
    return sorted({int(row['region']) for row in rows})


def set_default_values(collection):
    return {item: 0 for item in collection}


def quantify_by_state(rows, state_dict):
    for row in rows:
        state_dict[row['state']] += 1
    return state_dict


def quantify_by_region(rows, region_dict):
    for row in rows:
        region_dict[int(row['region'])] += 1
    return region_dict


if __name__ == '__main__':
    csv_path = Path('./import/optn_membership/optn_membership_2026-07-02.csv')
    membership_rows = filter_physical_locations(read_membership_csv(csv_path))

    unique_states = get_unique_states(membership_rows)
    unique_regions = get_unique_regions(membership_rows)

    states = quantify_by_state(membership_rows, set_default_values(unique_states))
    regions = quantify_by_region(membership_rows, set_default_values(unique_regions))

    export_path = Path('./export/shelve/hospital_quantities')
    db = shelve.open(str(export_path))

    db['states'] = states
    db['regions'] = regions
