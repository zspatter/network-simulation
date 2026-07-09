"""
Integration-level calibration guards for the realism model. Where the unit tests
check each mechanism in isolation, these run a multi-year trial with every real
channel enabled (deaths, non-death removals, living-donor transplants, organ
acceptance/discard) and assert the *aggregate* behavior lands in a realistic band:
the wait list approaches a steady state instead of growing without bound, and the
organ-discard rate resembles OPTN/SRTR figures.

These are the tests that would have caught the original unbounded-growth defect.
They run on a small hand-built coordinate network (real US city coordinates, no
geocoding) so the realistic door-to-door transit model applies without the cost of
building the full national network.
"""
import sys
from os.path import abspath, dirname, join

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

from benchmark_strategies import run_trial  # noqa: E402

from network_simulator.allocation import STRATEGIES  # noqa: E402
from network_simulator.clinical.removal import OTHER_REMOVAL_ANNUAL_RATE  # noqa: E402
from network_simulator.Network import Network  # noqa: E402
from network_simulator.Node import Node  # noqa: E402

# A handful of real US metros spread coast to coast, so transit spans local through
# cross-country. A coordinate network needs no edges: Network.transit_from computes
# direct point-to-point transit from the coordinates.
_CITIES = [
    (1, 'Chicago', 41.88, -87.63),
    (2, 'Boston', 42.36, -71.06),
    (3, 'Los Angeles', 34.05, -118.24),
    (4, 'Houston', 29.76, -95.37),
    (5, 'Atlanta', 33.75, -84.39),
    (6, 'Denver', 39.74, -104.99),
    (7, 'Seattle', 47.61, -122.33),
    (8, 'Miami', 25.76, -80.19),
]


def _coordinate_network() -> Network:
    return Network({node_id: Node(node_id, name, latitude=lat, longitude=lon)
                    for node_id, name, lat, lon in _CITIES})


def _realistic_trial(rounds, patients_per_round=30, harvests_per_round=8, seed=0):
    """A multi-round trial with every real outflow channel enabled."""
    return run_trial(
            seed=seed, strategy=STRATEGIES['real_world_circle'], rounds=rounds,
            patients_per_round=patients_per_round, harvests_per_round=harvests_per_round,
            network=_coordinate_network(), snapshot_interval_rounds=52,
            other_removal_annual_rate=OTHER_REMOVAL_ANNUAL_RATE,
            living_donors_per_round=3, realistic_outcomes=True)


def test_wait_list_approaches_a_steady_state_rather_than_growing_without_bound():
    metrics = _realistic_trial(rounds=52 * 6)
    sizes = [size for _, size in metrics.wait_list_size_snapshots]
    assert len(sizes) == 6

    first_year_growth = sizes[0]
    last_year_growth = sizes[-1] - sizes[-2]
    # growth must decelerate sharply - the original two-exit model grew ~linearly forever
    assert last_year_growth < 0.5 * first_year_growth


def test_most_arrivals_are_absorbed_by_the_real_outflow_channels():
    rounds, patients_per_round = 52 * 6, 30
    metrics = _realistic_trial(rounds=rounds, patients_per_round=patients_per_round)

    arrivals = patients_per_round * rounds
    outflow = (metrics.organs_transplanted + metrics.living_donor_transplants
               + metrics.waitlist_deaths + metrics.other_removals)
    # with only transplant + death (the original model) this sat near 60%; the added
    # channels must push most arrivals through some exit
    assert outflow / arrivals > 0.8


def test_organ_discard_rate_matches_the_2024_optn_non_use_rate():
    metrics = _realistic_trial(rounds=52 * 4)
    recovered = metrics.organs_transplanted + metrics.organs_wasted
    discard_rate = metrics.organs_discarded / recovered
    # OPTN/SRTR 2024 overall non-use was 20.7%; the organ-specific base rates are calibrated
    # to that, so realized decline/discard should land in a band centered near it
    assert 0.14 < discard_rate < 0.27


def test_every_real_outflow_channel_is_exercised():
    metrics = _realistic_trial(rounds=52 * 4)
    assert metrics.waitlist_deaths > 0
    assert metrics.other_removals > 0
    assert metrics.living_donor_transplants > 0
    assert metrics.organs_discarded > 0
    assert metrics.organs_transplanted > 0
