import sys
from os.path import abspath, dirname, join

import openpyxl

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

import hospital_count  # noqa: E402


def _worksheet(rows):
    """
    rows: list of (state, region) - state goes in column A, region in column E. Every
    reader here starts at row 2 (range(2, max_row + 1)), treating row 1 as a header.
    """
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(['state', None, None, None, 'region'])
    for state, region in rows:
        worksheet.append([state, None, None, None, region])
    return worksheet


def test_get_unique_states_is_sorted_and_deduplicated():
    worksheet = _worksheet([('TX', 4), ('CA', 5), ('TX', 4)])

    assert hospital_count.get_unique_states(worksheet) == ['CA', 'TX']


def test_get_unique_regions_is_sorted_and_deduplicated():
    worksheet = _worksheet([('TX', 4), ('CA', 5), ('TX', 4)])

    assert hospital_count.get_unique_regions(worksheet) == [4, 5]


def test_set_default_values_zeroes_every_key():
    result = hospital_count.set_default_values(['TX', 'CA'])

    assert result == {'TX': 0, 'CA': 0}


def test_quantify_by_state_counts_occurrences():
    worksheet = _worksheet([('TX', 4), ('CA', 5), ('TX', 4), ('TX', 4)])
    state_dict = hospital_count.set_default_values(hospital_count.get_unique_states(worksheet))

    result = hospital_count.quantify_by_state(worksheet, state_dict)

    assert result == {'CA': 1, 'TX': 3}


def test_quantify_by_region_counts_occurrences():
    worksheet = _worksheet([('TX', 4), ('CA', 5), ('TX', 4), ('TX', 4)])
    region_dict = hospital_count.set_default_values(hospital_count.get_unique_regions(worksheet))

    result = hospital_count.quantify_by_region(worksheet, region_dict)

    assert result == {4: 3, 5: 1}
