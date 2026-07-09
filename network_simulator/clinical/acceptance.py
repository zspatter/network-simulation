"""
Organ acceptance / decline and the cold-ischemia -> graft-outcome link.

Two real effects the original model left out, both driven by organ quality and
how long the organ has been out of the body:

1. Discard. A recovered organ offered to a candidate is often declined - for
   quality, logistics, or recipient-readiness reasons - and an organ declined
   down the whole match run is discarded, never transplanted. This is a large,
   organ-specific effect (kidney and pancreas discard ~20-25% of recovered
   organs; hearts far less), and it is a big reason the real transplant count is
   well below the number of organs recovered. Modeled here as a *terminal*
   discard probability - the net chance an organ goes unused after offers -
   rather than simulating each decline-and-re-offer, so it plugs into the round
   loop without rewriting the matchers. Longer transit (more accumulated cold
   ischemia) raises the discard chance, which also gives geography a cost in
   organs wasted, not just in feasibility.

2. Graft outcome. Even when transplanted, a longer cold-ischemia time lowers
   expected graft survival, so a far-flown organ yields fewer life-years than a
   local one. graft_survival_factor scales the life-years benefit accordingly,
   so the geography trade-off shows up in *outcomes*, not only in eligibility.

Rates are documented approximations (discard rates in the range OPTN/SRTR
report; the ischemia slopes are simplifying assumptions), and are the knobs for
tuning transplant volume and the geography-vs-utility trade-off.
"""
from __future__ import annotations

import random
from typing import Dict, Optional

from network_simulator.compatibility_markers import OrganType

# Baseline probability a recovered organ is ultimately not transplanted (discarded/declined
# down the match run). These are the actual 2024 non-use rates by organ. Source: OPTN/SRTR
# 2024 Annual Data Report, Deceased Organ Donation (https://srtr.hrsa.gov/adr/2024/DOD/),
# retrieved 2026-07-08. Kidney/pancreas run high (~29% / ~25%); hearts are almost always used
# (~2%). Overall non-use across organs was 20.7%.
BASE_DISCARD_PROB: Dict[OrganType, float] = {
    OrganType.Kidney:     0.293,
    OrganType.Liver:      0.115,
    OrganType.Heart:      0.019,
    OrganType.Lungs:      0.113,
    OrganType.Pancreas:   0.251,
    OrganType.Intestines: 0.049,
}
_DEFAULT_BASE_DISCARD = 0.15

# Extra discard probability per hour of transit. The base rates above are *observed* averages
# that already embed real cold-ischemia effects, so this term is deliberately small - it exists
# so the simulation's counterfactuals (e.g. dropping the geographic constraint and shipping
# organs farther) still show geography raising discard, rather than to re-derive the baseline.
# It biases realized discard modestly above the observed base; the total is capped below 1.
ISCHEMIA_DISCARD_PER_HOUR = 0.004
MAX_DISCARD_PROB = 0.95

# Graft-survival penalty per hour of cold ischemia, floored so a long haul still yields a
# worthwhile fraction of the organ's life-years (an accepted far organ is not worthless).
GRAFT_PENALTY_PER_HOUR = 0.02
MIN_GRAFT_FACTOR = 0.6


def discard_probability(organ_type: OrganType, transit_hours: float) -> float:
    """
    Probability a matched organ is discarded (declined and never transplanted),
    rising with accumulated cold ischemia (transit_hours).

    :param OrganType organ_type: the organ being offered
    :param float transit_hours: transit time to the recipient (cold-ischemia proxy)
    :return: discard probability in [0, MAX_DISCARD_PROB]
    """
    base = BASE_DISCARD_PROB.get(organ_type, _DEFAULT_BASE_DISCARD)
    return min(MAX_DISCARD_PROB, base + ISCHEMIA_DISCARD_PER_HOUR * max(0.0, transit_hours))


def is_discarded(organ_type: OrganType, transit_hours: float,
                 rng: Optional[random.Random] = None) -> bool:
    """
    Draws whether a matched organ is discarded rather than transplanted.

    :param OrganType organ_type: the organ being offered
    :param float transit_hours: transit time to the recipient
    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: True if the organ is discarded (wasted)
    """
    source = rng or random
    return source.random() < discard_probability(organ_type, transit_hours)


def graft_survival_factor(transit_hours: float) -> float:
    """
    Multiplier on an organ's expected life-years, decreasing with cold ischemia
    (transit_hours) and floored at MIN_GRAFT_FACTOR.

    :param float transit_hours: transit time to the recipient
    :return: graft-survival multiplier in [MIN_GRAFT_FACTOR, 1.0]
    """
    return max(MIN_GRAFT_FACTOR, 1.0 - GRAFT_PENALTY_PER_HOUR * max(0.0, transit_hours))
