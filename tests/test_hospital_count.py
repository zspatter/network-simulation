import sys
from os.path import abspath, dirname, join

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

import hospital_count  # noqa: E402


def _rows(pairs):
    """pairs: list of (state, region) tuples."""
    return [{'state': state, 'region': str(region)} for state, region in pairs]


def test_get_unique_states_is_sorted_and_deduplicated():
    rows = _rows([('TX', 4), ('CA', 5), ('TX', 4)])

    assert hospital_count.get_unique_states(rows) == ['CA', 'TX']


def test_get_unique_regions_is_sorted_and_deduplicated():
    rows = _rows([('TX', 4), ('CA', 5), ('TX', 4)])

    assert hospital_count.get_unique_regions(rows) == [4, 5]


def test_set_default_values_zeroes_every_key():
    assert hospital_count.set_default_values(['TX', 'CA']) == {'TX': 0, 'CA': 0}


def test_quantify_by_state_counts_occurrences():
    rows = _rows([('TX', 4), ('CA', 5), ('TX', 4), ('TX', 4)])
    state_dict = hospital_count.set_default_values(hospital_count.get_unique_states(rows))

    result = hospital_count.quantify_by_state(rows, state_dict)

    assert result == {'CA': 1, 'TX': 3}


def test_quantify_by_region_counts_occurrences():
    rows = _rows([('TX', 4), ('CA', 5), ('TX', 4), ('TX', 4)])
    region_dict = hospital_count.set_default_values(hospital_count.get_unique_regions(rows))

    result = hospital_count.quantify_by_region(rows, region_dict)

    assert result == {4: 3, 5: 1}
