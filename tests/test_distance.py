from network_simulator.distance import (
    GROUND_TRANSPORT_THRESHOLD_KM,
    estimate_transit_hours,
    haversine_km,
)


def test_haversine_km_same_point_is_zero():
    assert haversine_km(41.8781, -87.6298, 41.8781, -87.6298) == 0.0


def test_haversine_km_known_distance():
    # London <-> Paris: commonly cited great-circle distance is ~344 km
    km = haversine_km(51.5074, -0.1278, 48.8566, 2.3522)
    assert 330 < km < 360


def test_estimate_transit_hours_uses_ground_speed_below_threshold():
    km = GROUND_TRANSPORT_THRESHOLD_KM - 1
    hours = estimate_transit_hours(km)
    assert hours == km / 90.0


def test_estimate_transit_hours_uses_air_speed_above_threshold():
    km = GROUND_TRANSPORT_THRESHOLD_KM + 1
    hours = estimate_transit_hours(km)
    assert hours == km / 700.0


def test_estimate_transit_hours_increases_with_distance():
    assert estimate_transit_hours(50) < estimate_transit_hours(500) < estimate_transit_hours(5000)
