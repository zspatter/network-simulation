"""
Living-donor transplants - a wait-list outflow the deceased-donor pipeline never
captures.

Nationally ~7,000 transplants a year come from *living* donors, overwhelmingly
kidney with a smaller liver share. These are directed donations (a specific donor
gives to a specific recipient), so they are largely independent of the
deceased-organ match run and of wait-list priority - and they remove candidates
the deceased-donor allocation therefore never has to serve. Omitting them (as the
original model did) both understates transplants and inflates the wait list.

Modeled simply: a per-round count of living-donor transplants is drawn off
eligible (kidney/liver) waiters, weighted toward kidney. Recipients are chosen
without regard to allocation priority, reflecting directed donation. Callers apply
the result explicitly, per the project convention.
"""
from __future__ import annotations

import random
from collections import defaultdict
from typing import Dict, List, Optional

from organflow.compatibility_markers import OrganType
from organflow.Patient import Patient
from organflow.WaitList import WaitList

# Living donation is almost entirely kidney, with a modest liver share; other
# organs are negligible in living-donor practice.
LIVING_DONOR_ORGAN_WEIGHTS: Dict[OrganType, float] = {
    OrganType.Kidney: 0.9,
    OrganType.Liver:  0.1,
}


def simulate_living_donor_transplants(wait_list: WaitList, count: int,
                                      rng: Optional[random.Random] = None) -> List[Patient]:
    """
    Removes up to `count` eligible waiters who receive a living-donor transplant
    this round, drawn by LIVING_DONOR_ORGAN_WEIGHTS and then uniformly within the
    chosen organ (directed donation ignores allocation priority).

    :param WaitList wait_list: the wait list to draw recipients from (mutated in place)
    :param int count: number of living-donor transplants this round
    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: the patients transplanted from living donors this round (already off the list)
    """
    if count <= 0:
        return []
    source = rng or random

    eligible: Dict[OrganType, List[Patient]] = defaultdict(list)
    for patient in wait_list.wait_list:
        if patient.organ_needed in LIVING_DONOR_ORGAN_WEIGHTS:
            eligible[patient.organ_needed].append(patient)

    recipients: List[Patient] = []
    for _ in range(count):
        organs = [organ for organ in eligible if eligible[organ]]
        if not organs:
            break
        weights = [LIVING_DONOR_ORGAN_WEIGHTS[organ] for organ in organs]
        organ = source.choices(organs, weights=weights, k=1)[0]

        pool = eligible[organ]
        chosen = pool.pop(source.randrange(len(pool)))
        wait_list.remove_patient(chosen)
        recipients.append(chosen)
    return recipients
