"""
Donor/recipient size matching for size-sensitive organs (heart, lung).

An oversized or undersized thoracic organ won't fit or function in the
recipient's chest, so heart and lung allocation requires the donor and
recipient to be of comparable body size (in practice via predicted heart mass
or predicted total lung capacity; here abstracted to body weight in kg). Other
organs (kidney, liver, pancreas, intestine) are far less size-constrained and
carry no size gate.
"""
from __future__ import annotations

import random
from typing import Dict, Optional

from network_simulator.compatibility_markers import OrganType

# Body weight distribution (kg) for adult donors/recipients - a documented
# approximation, clamped to a plausible adult range.
_MEAN_BODY_KG = 80.0
_SD_BODY_KG = 15.0
_MIN_BODY_KG = 40.0
_MAX_BODY_KG = 130.0

# Allowed fractional deviation of donor size from recipient size, per organ.
# Lungs are slightly more size-sensitive than hearts. Organs not listed have no
# size constraint.
SIZE_TOLERANCE: Dict[OrganType, float] = {
    OrganType.Heart: 0.30,
    OrganType.Lungs: 0.25,
}


def body_size(rng: Optional[random.Random] = None) -> float:
    """
    Returns a body-size measure (kg) for a donor or recipient, drawn from a
    clamped normal distribution.

    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: body size in kg
    """
    source = rng or random
    return max(_MIN_BODY_KG, min(_MAX_BODY_KG, source.gauss(_MEAN_BODY_KG, _SD_BODY_KG)))


def size_compatible(donor_size: Optional[float], recipient_size: Optional[float],
                    organ_type: OrganType) -> bool:
    """
    Returns True if the donor organ is size-compatible with the recipient.

    Organs without a size constraint (anything not in SIZE_TOLERANCE) are always
    compatible. If either size is unknown (None) - e.g. a hand-constructed test
    organ - the pair is treated as compatible (the gate is skipped) so the
    constraint only ever tightens realistically-generated flows.

    :param donor_size: donor body size (kg) or None
    :param recipient_size: recipient body size (kg) or None
    :param OrganType organ_type: organ being matched
    :return: True if size-compatible (or unconstrained/unknown)
    """
    tolerance = SIZE_TOLERANCE.get(organ_type)
    if tolerance is None:
        return True
    if donor_size is None or recipient_size is None:
        return True
    ratio = donor_size / recipient_size
    return (1.0 - tolerance) <= ratio <= (1.0 + tolerance)
