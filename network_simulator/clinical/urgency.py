"""
Organ-specific medical urgency, normalized to a common "acuity" scale.

Real allocation urgency is measured on organ-specific scales - MELD (liver,
6-40), LAS (lung, 0-100), status tiers (heart, 1 most urgent .. 6), while
kidney candidates are sustained by dialysis and are not acutely urgent. To let
one ScoringFunction rank across organ types, each native score is mapped to a
common acuity in (0, 1] via documented anchor points, where higher acuity means
higher near-term death risk (see mortality.py, which turns acuity into a
per-round death probability).

Each organ provides three pure, rng-seeded functions: generate an initial
native urgency, progress it one round (disease advances while waiting), and
normalize a native score to acuity. Anchor values are documented approximations
chosen so the resulting mortality (mortality.py) resembles published figures,
not exact clinical instruments.
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional, Tuple

from network_simulator.compatibility_markers import OrganType

# A listed patient always carries some risk, so acuity never reaches 0 - this
# also keeps OptimalMatcher's `weight > 0` edge filter from dropping anyone an
# acuity-based scorer would otherwise consider.
ACUITY_FLOOR = 0.02

# Native-score -> acuity anchor points per organ (piecewise-linear between them,
# clamped at the ends). Calibrated so mortality.py reproduces roughly the right
# death rates (e.g. liver MELD 31-40 ~high, MELD <=20 ~low).
# Anchors are sorted ascending by native score; y may decrease with x (heart:
# a lower status number is MORE urgent, so acuity falls as status rises).
_ACUITY_ANCHORS: Dict[OrganType, List[Tuple[float, float]]] = {
    OrganType.Liver:  [(6, 0.05), (15, 0.20), (25, 0.65), (35, 0.90), (40, 0.97)],  # MELD
    OrganType.Lungs:  [(0, 0.02), (40, 0.25), (70, 0.60), (100, 0.90)],  # LAS
    OrganType.Heart:  [(1, 0.90), (2, 0.70), (3, 0.50), (4, 0.30),       # status tiers
                       (5, 0.15), (6, 0.08)],
    OrganType.Kidney: [(0, 0.05)],                                       # dialysis sustains
    OrganType.Pancreas:   [(0, 0.10)],
    OrganType.Intestines: [(0, 0.20)],
}


def _interpolate(x: float, anchors: List[Tuple[float, float]]) -> float:
    """Piecewise-linear interpolation over (x, y) anchors sorted ascending by x."""
    if len(anchors) == 1:
        return anchors[0][1]
    if x <= anchors[0][0]:
        return anchors[0][1]
    if x >= anchors[-1][0]:
        return anchors[-1][1]
    for (x0, y0), (x1, y1) in zip(anchors, anchors[1:]):
        if x0 <= x <= x1:
            t = (x - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)
    return anchors[-1][1]


def initial_raw_urgency(organ_type: OrganType, rng: Optional[random.Random] = None) -> float:
    """
    Returns a newly listed patient's urgency on the organ's native scale.
    Distributions are skewed the way real listings are (most patients start
    moderate, not critical).

    :param OrganType organ_type: the organ the patient needs
    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: initial native urgency score
    """
    source = rng or random
    if organ_type is OrganType.Liver:
        return source.triangular(6, 40, 12)      # MELD, mode ~12
    if organ_type is OrganType.Lungs:
        return max(0.0, min(100.0, source.gauss(40, 12)))  # LAS
    if organ_type is OrganType.Heart:
        # status tier 1 (most urgent) .. 6; weighted toward less urgent
        return float(source.choices([1, 2, 3, 4, 5, 6],
                                    weights=[3, 5, 8, 12, 14, 16])[0])
    # kidney / pancreas / intestine: no meaningful acute native scale
    return 0.0


def progress(organ_type: OrganType, raw_urgency: float, rounds_waited: int,
             rng: Optional[random.Random] = None) -> float:
    """
    Advances a patient's native urgency by one round of disease progression.
    Liver/lung scores drift upward; heart may escalate to a more urgent tier;
    kidney barely changes acutely (its priority comes from wait time, handled
    by the scorer, not from a rising acute score).

    :param OrganType organ_type: the organ the patient needs
    :param float raw_urgency: current native urgency
    :param int rounds_waited: how many rounds the patient has waited (unused for
        most organs; available for wait-sensitive progression)
    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: the progressed native urgency
    """
    source = rng or random
    if organ_type is OrganType.Liver:
        return min(40.0, raw_urgency + source.uniform(0.0, 2.0))
    if organ_type is OrganType.Lungs:
        return min(100.0, raw_urgency + source.uniform(0.0, 3.0))
    if organ_type is OrganType.Heart:
        # small chance of escalating to a more urgent (lower) status tier
        if raw_urgency > 1 and source.random() < 0.15:
            return raw_urgency - 1
        return raw_urgency
    return raw_urgency


def to_acuity(organ_type: OrganType, raw_urgency: float) -> float:
    """
    Normalizes a native urgency score to acuity in [ACUITY_FLOOR, 1].

    :param OrganType organ_type: the organ the patient needs
    :param float raw_urgency: native urgency score
    :return: acuity in [ACUITY_FLOOR, 1] (higher = higher near-term death risk)
    """
    anchors = _ACUITY_ANCHORS.get(organ_type, [(0, ACUITY_FLOOR)])
    return max(ACUITY_FLOOR, _interpolate(raw_urgency, anchors))
