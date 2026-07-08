"""
Non-death wait-list removals - the outflow channel besides transplant and death.

Real wait lists lose a large share of candidates for reasons that are neither a
transplant nor a death on the list: removed as *too sick to transplant*,
*condition improved*, *transferred* to another program, or the candidate
*declined*. Nationally this is comparable in magnitude to wait-list deaths, and
it is a big part of why the real list stays near steady-state rather than growing
without bound. A model with only transplant and death as exits has no way to
balance arrivals except by growing the list (and its death count) unrealistically
- so this adds the missing competing risk.

Modeled, like mortality, as a constant annual hazard converted to a per-round
probability over ROUND_DURATION_DAYS. Kept separate from mortality (a removal is
not a death - it must not be counted as one) and from the matchers, following the
project's "callers apply side effects explicitly" convention.
"""
from __future__ import annotations

import math
import random
from typing import List, Optional

from network_simulator.clinical.mortality import DAYS_PER_YEAR, ROUND_DURATION_DAYS
from network_simulator.Patient import Patient
from network_simulator.WaitList import WaitList

# Baseline annual rate of removal for reasons other than transplant or death.
# Documented approximation in the range OPTN reports for "removed - other" plus
# "too sick to transplant" / "condition improved" (a few percent per year); the
# exact figure is the primary knob for calibrating steady-state wait-list size.
OTHER_REMOVAL_ANNUAL_RATE = 0.05


def per_round_removal_prob(annual_rate: float = OTHER_REMOVAL_ANNUAL_RATE) -> float:
    """
    Probability a waiting patient is removed (non-death) during one round, under
    a constant-hazard model over ROUND_DURATION_DAYS - the same conversion
    mortality.py uses.

    :param float annual_rate: annualized non-death removal hazard
    :return: per-round removal probability in [0, 1)
    """
    dt_years = ROUND_DURATION_DAYS / DAYS_PER_YEAR
    return 1.0 - math.exp(-annual_rate * dt_years)


def simulate_round_removals(wait_list: WaitList,
                            annual_rate: float = OTHER_REMOVAL_ANNUAL_RATE,
                            rng: Optional[random.Random] = None) -> List[Patient]:
    """
    Rolls non-death removal for every patient still on the wait list and removes
    those drawn. Intended to be called once per round, after mortality, so the
    two competing risks don't both fire on the same patient in the same round.

    :param WaitList wait_list: the wait list to thin (mutated in place)
    :param float annual_rate: annualized non-death removal hazard
    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: the patients removed this round (already off the list)
    """
    if annual_rate <= 0.0:
        return []
    source = rng or random
    probability = per_round_removal_prob(annual_rate)

    removed: List[Patient] = []
    for patient in list(wait_list.wait_list):
        if source.random() < probability:
            wait_list.remove_patient(patient)
            removed.append(patient)
    return removed
