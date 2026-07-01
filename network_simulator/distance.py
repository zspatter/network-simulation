"""
Great-circle distance and a simplified transit-time estimate between two
coordinates. Used to derive Network edge weights directly from hospital
coordinates (see Network's docstring for the hours-based weight convention)
instead of scraping a distance-lookup site.
"""
import math

EARTH_RADIUS_KM = 6371.0088

# Simplified two-tier speed model standing in for real routing: organ
# transport typically stays on the ground up to roughly a 4-hour drive
# (~400 km), and switches to chartered/commercial air beyond that. This is a
# documented simplifying assumption for simulation purposes, not
# routing-grade.
GROUND_TRANSPORT_THRESHOLD_KM = 400.0
GROUND_SPEED_KMH = 90.0  # effective ground-courier speed, including transfer overhead
AIR_SPEED_KMH = 700.0  # effective fixed-wing speed, including ground-to-tarmac overhead


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Great-circle distance between two lat/long points, in kilometers.

    :param float lat1: latitude of the first point, in degrees
    :param float lon1: longitude of the first point, in degrees
    :param float lat2: latitude of the second point, in degrees
    :param float lon2: longitude of the second point, in degrees
    :return: distance between the two points, in kilometers
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def estimate_transit_hours(distance_km: float) -> float:
    """
    Rough organ-transport time estimate, in hours. Below
    GROUND_TRANSPORT_THRESHOLD_KM this assumes ground transport; beyond it,
    air transport. Exists so Network edge weights and Organ.viability are
    expressed in the same unit (hours) - see the unit-mismatch note in
    Network's docstring.

    :param float distance_km: great-circle distance, in kilometers
    :return: estimated transit time, in hours
    """
    speed_kmh = GROUND_SPEED_KMH if distance_km <= GROUND_TRANSPORT_THRESHOLD_KM else AIR_SPEED_KMH
    return distance_km / speed_kmh
