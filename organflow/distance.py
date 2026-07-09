"""
Great-circle distance and a door-to-door organ-transport time estimate between
two coordinates. Used to derive Network edge weights directly from hospital
coordinates (see Network's docstring for the hours-based weight convention)
instead of scraping a distance-lookup site.

Transit is modeled as the faster of two competing modes:

  ground: GROUND_HANDLING_HOURS + (GROUND_CIRCUITY * great_circle_km) / GROUND_SPEED_KMH
  air:    AIR_OVERHEAD_HOURS    +  great_circle_km / AIR_SPEED_KMH
  transit = min(ground, air)

This is deliberately more faithful than a single distance->speed ratio in three
ways that matter for whether geography actually binds a match:

  1. Real *fixed* overhead. An organ is not teleported the instant it is
     recovered: it is packaged, driven to an airport, flown, and driven from the
     destination airport to the recipient hospital, with coordination throughout.
     Air transport therefore carries a multi-hour fixed cost (AIR_OVERHEAD_HOURS)
     independent of flight distance - which is exactly what makes a short hop
     ground-preferable and a long haul air-preferable.
  2. Road circuity. Ground distance is not the great-circle line; real road
     distance runs ~GROUND_CIRCUITY times longer.
  3. Monotonic and continuous in distance. Because ground has a low fixed cost
     and high marginal cost while air is the reverse, their min crosses over once
     (~190 km here) and never inverts - a farther hospital is never "closer" in
     time, unlike the old two-tier model's discontinuity at its ground->air
     switch. This is what let the old model treat a 1,200 km flight as more
     "local" than a 300 km drive.

Values are documented simulation approximations, not routing-grade.
"""
import math

EARTH_RADIUS_KM = 6371.0088

# Ground courier: package/load at origin, then drive real (circuitous) roads.
GROUND_HANDLING_HOURS = 0.5   # organ packaging + loading before the vehicle moves
GROUND_CIRCUITY = 1.25        # road distance / great-circle distance
GROUND_SPEED_KMH = 105.0      # effective courier speed incl. urgency, net of stops

# Charter air: fixed cost is both hospital<->airport ground legs plus taxi/climb/
# descent and flight coordination; marginal cost is cruise over the great circle.
AIR_OVERHEAD_HOURS = 2.5      # fixed door-to-door air overhead, independent of distance
AIR_SPEED_KMH = 750.0         # effective fixed-wing cruise


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
    Door-to-door organ-transport time estimate, in hours: the faster of the
    ground and air modes (see the module docstring for the model and why it is
    monotonic in distance). Expressed in hours so Network edge weights and
    Organ.viability share a unit - see the note in Network's docstring.

    :param float distance_km: great-circle distance, in kilometers
    :return: estimated transit time, in hours
    """
    ground_hours = GROUND_HANDLING_HOURS + (GROUND_CIRCUITY * distance_km) / GROUND_SPEED_KMH
    air_hours = AIR_OVERHEAD_HOURS + distance_km / AIR_SPEED_KMH
    return min(ground_hours, air_hours)
