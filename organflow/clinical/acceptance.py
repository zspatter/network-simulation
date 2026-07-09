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
   ischemia) and a more marginal donor (higher quality_index) both raise the
   discard chance, so geography and donor quality each cost organs wasted, not
   just feasibility.

2. Graft outcome. Even when transplanted, a longer cold-ischemia time and a more
   marginal donor lower expected graft survival, so a far-flown or lower-quality
   organ yields fewer life-years than a local, pristine one. graft_survival_factor
   scales the life-years benefit accordingly, so both trade-offs show up in
   *outcomes*, not only in eligibility.

Donor quality is a continuous index (KDPI convention; see clinical.frequencies)
that generalizes the earlier binary DBD/DCD split - a marginal organ is one high
on that index, not merely a DCD one. Rates are documented approximations (discard
rates in the range OPTN/SRTR report; the ischemia and quality slopes are
simplifying assumptions), and are the knobs for tuning transplant volume and the
geography-vs-utility trade-off.
"""
from __future__ import annotations

import random
from typing import Dict, Optional

from organflow.clinical.frequencies import POPULATION_MEAN_QUALITY_INDEX
from organflow.compatibility_markers import OrganType

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

# Donor-quality index effect. Each organ carries a continuous quality index (KDPI convention:
# 0 = ideal donor, 100 = most marginal; see clinical.frequencies.random_quality_index), which
# generalizes the retired binary DBD/DCD multipliers into a continuum. Two effects scale with it:
#
# Discard. A linear multiplier on BASE_DISCARD_PROB, centered on the population-mean index so it
# is MEAN-PRESERVING: an average-quality organ multiplies by 1.0, better organs below it, marginal
# organs above it, and the population mean stays 1.0 - so BASE_DISCARD_PROB remains the population
# average matching the observed 2024 non-use, and quality just redistributes discard toward
# marginal organs (verified by a mean-preservation test and validate_realism). QUALITY_DISCARD_SLOPE
# is sized so the pathway means (~40 DBD, ~60 DCD) land near the old 0.78/1.30 pathway multipliers.
QUALITY_DISCARD_SLOPE = 0.02
MIN_QUALITY_DISCARD_MULTIPLIER = 0.1
MAX_QUALITY_DISCARD_MULTIPLIER = 1.9

# Graft. Organs at or better than the population-mean index graft at full; marginal organs above
# it graft progressively worse (this is a pure life-years scaler, it does not affect the discard
# calibration). The slope is sized so a DCD-typical organ (~60) grafts ~8% worse, matching the old
# straight DCD graft reduction.
GRAFT_QUALITY_SLOPE = 0.007


def quality_discard_multiplier(quality_index: float) -> float:
    """
    Mean-preserving multiplier on BASE_DISCARD_PROB for a donor-quality index (KDPI convention:
    higher = more marginal). 1.0 at the population-mean index, below 1.0 for better organs, above
    for marginal ones; clamped to keep the scaled probability sane at the tails.

    :param float quality_index: donor-quality index in [0, 100] (higher = more marginal)
    :return: discard multiplier in [MIN_QUALITY_DISCARD_MULTIPLIER, MAX_QUALITY_DISCARD_MULTIPLIER]
    """
    raw = 1.0 + QUALITY_DISCARD_SLOPE * (quality_index - POPULATION_MEAN_QUALITY_INDEX)
    return min(MAX_QUALITY_DISCARD_MULTIPLIER, max(MIN_QUALITY_DISCARD_MULTIPLIER, raw))


def quality_graft_factor(quality_index: float) -> float:
    """
    Graft-survival multiplier for a donor-quality index: 1.0 for organs at or better than the
    population mean, declining for marginal organs above it (not floored here - the caller applies
    MIN_GRAFT_FACTOR to the combined ischemia x quality product).

    :param float quality_index: donor-quality index in [0, 100] (higher = more marginal)
    :return: quality graft multiplier in (0, 1.0]
    """
    excess = max(0.0, quality_index - POPULATION_MEAN_QUALITY_INDEX)
    return min(1.0, 1.0 - GRAFT_QUALITY_SLOPE * excess)


def discard_probability(organ_type: OrganType, transit_hours: float,
                        quality_index: float = POPULATION_MEAN_QUALITY_INDEX) -> float:
    """
    Probability a matched organ is discarded (declined and never transplanted),
    rising with accumulated cold ischemia (transit_hours) and with a more marginal
    donor-quality index (quality_index).

    :param OrganType organ_type: the organ being offered
    :param float transit_hours: transit time to the recipient (cold-ischemia proxy)
    :param float quality_index: donor-quality index in [0, 100] (higher = discarded more often)
    :return: discard probability in [0, MAX_DISCARD_PROB]
    """
    base = BASE_DISCARD_PROB.get(organ_type, _DEFAULT_BASE_DISCARD)
    base *= quality_discard_multiplier(quality_index)
    return min(MAX_DISCARD_PROB, base + ISCHEMIA_DISCARD_PER_HOUR * max(0.0, transit_hours))


def is_discarded(organ_type: OrganType, transit_hours: float,
                 quality_index: float = POPULATION_MEAN_QUALITY_INDEX,
                 rng: Optional[random.Random] = None) -> bool:
    """
    Draws whether a matched organ is discarded rather than transplanted.

    :param OrganType organ_type: the organ being offered
    :param float transit_hours: transit time to the recipient
    :param float quality_index: donor-quality index in [0, 100] (higher = discarded more often)
    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: True if the organ is discarded (wasted)
    """
    source = rng or random
    return source.random() < discard_probability(organ_type, transit_hours, quality_index)


def graft_survival_factor(transit_hours: float,
                          quality_index: float = POPULATION_MEAN_QUALITY_INDEX) -> float:
    """
    Multiplier on an organ's expected life-years, decreasing with cold ischemia
    (transit_hours), reduced further for a more marginal donor-quality index
    (quality_index), and floored at MIN_GRAFT_FACTOR.

    :param float transit_hours: transit time to the recipient
    :param float quality_index: donor-quality index in [0, 100] (higher = grafts worse)
    :return: graft-survival multiplier in [MIN_GRAFT_FACTOR, 1.0]
    """
    ischemia_factor = 1.0 - GRAFT_PENALTY_PER_HOUR * max(0.0, transit_hours)
    return max(MIN_GRAFT_FACTOR, ischemia_factor * quality_graft_factor(quality_index))
