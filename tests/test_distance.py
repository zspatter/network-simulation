import math

from organflow.distance import (
    AIR_OVERHEAD_HOURS,
    AIR_SPEED_KMH,
    GROUND_CIRCUITY,
    GROUND_HANDLING_HOURS,
    GROUND_SPEED_KMH,
    estimate_transit_hours,
    haversine_km,
)


def test_haversine_km_same_point_is_zero():
    assert haversine_km(41.8781, -87.6298, 41.8781, -87.6298) == 0.0


def test_haversine_km_known_distance():
    # London <-> Paris: commonly cited great-circle distance is ~344 km
    km = haversine_km(51.5074, -0.1278, 48.8566, 2.3522)
    assert 330 < km < 360


def test_short_trips_take_the_ground_mode():
    # Well below the ~190 km crossover, ground is faster and used.
    km = 50.0
    expected_ground = GROUND_HANDLING_HOURS + (GROUND_CIRCUITY * km) / GROUND_SPEED_KMH
    assert estimate_transit_hours(km) == expected_ground


def test_long_trips_take_the_air_mode():
    # Well above the crossover, air is faster and used.
    km = 2000.0
    expected_air = AIR_OVERHEAD_HOURS + km / AIR_SPEED_KMH
    assert estimate_transit_hours(km) == expected_air


def test_transit_carries_fixed_overhead_no_teleporting():
    # Even a co-located organ still costs the ground handling floor - it is not
    # available at the recipient the instant it is recovered.
    assert estimate_transit_hours(0.0) == GROUND_HANDLING_HOURS
    # Every trip clears the smaller of the two fixed costs.
    assert estimate_transit_hours(10.0) >= GROUND_HANDLING_HOURS


def test_transit_is_monotonic_including_across_the_crossover():
    # The old two-tier model inverted at its 400 km switch (401 km was faster
    # than 399 km); the min-of-two-modes model must never do that.
    distances = [0, 50, 100, 189, 190, 300, 399, 401, 500, 1000, 2000, 4000]
    hours = [estimate_transit_hours(d) for d in distances]
    assert hours == sorted(hours)
    assert estimate_transit_hours(399) < estimate_transit_hours(401)


def test_transit_is_continuous_at_the_crossover():
    # Ground and air meet (no jump) where they cross over.
    # crossover where GROUND_HANDLING + GROUND_CIRCUITY*d/GROUND_SPEED == AIR_OVERHEAD + d/AIR_SPEED
    d = (AIR_OVERHEAD_HOURS - GROUND_HANDLING_HOURS) / (
        GROUND_CIRCUITY / GROUND_SPEED_KMH - 1 / AIR_SPEED_KMH)
    ground = GROUND_HANDLING_HOURS + (GROUND_CIRCUITY * d) / GROUND_SPEED_KMH
    air = AIR_OVERHEAD_HOURS + d / AIR_SPEED_KMH
    assert math.isclose(ground, air, rel_tol=1e-9)
    assert math.isclose(estimate_transit_hours(d), ground, rel_tol=1e-9)


def test_coast_to_coast_is_a_realistic_number_of_hours():
    # ~4,000 km great circle should land in a plausible door-to-door band, not
    # the old model's ~5.7 h with zero overhead.
    hours = estimate_transit_hours(4000.0)
    assert 7.0 < hours < 9.0
