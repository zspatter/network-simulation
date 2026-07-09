"""
Graft failure and re-transplantation - the feedback loop that returns a prior
recipient to the wait list.

A transplanted organ is not the end of the story: grafts fail over time
(chronic rejection, recurrence of disease, technical loss), and when one does the
patient faces one of two outcomes. If a bridge to survival exists - dialysis for a
failed kidney, most obviously - the patient can **relist** as a re-transplant
candidate; if not - a failed heart or lung - graft failure is usually fatal. So a
share of every year's new listings are not first-time patients but returning
recipients, and that share is real and organ-specific: ~10% of kidney transplants
go to re-transplant candidates, far fewer for the thoracic organs.

This module models graft failure as a constant annual hazard on a registry of
living grafts (the same constant-hazard-per-round conversion mortality and removal
use), splitting each failure into a re-listing or a post-transplant death by an
organ-specific relist fraction. Re-listing is the point of the loop: it couples
graft *outcomes* back to future *demand* (worse graft survival -> more relisting),
and a relisted candidate re-enters more sensitized (prior-transplant antibodies),
so re-transplants are harder to match, as in reality.

Post-transplant deaths here are deliberately NOT wait-list deaths (the patient had
already left the list via transplant), so they are tracked as a separate outcome
and never inflate the wait-list-death calibration.

Rates are documented approximations (graft half-lives and relist-vs-death splits
from the transplant literature); the blended failure rate is tuned so the emergent
re-transplant share of listings approaches RETRANSPLANT_SHARE_OF_LISTINGS.
"""
from __future__ import annotations

import math
import random
from typing import List, Optional, Tuple

from organflow.clinical.hla import ANTIGEN_POOL_SIZE, cpra
from organflow.clinical.mortality import DAYS_PER_YEAR, ROUND_DURATION_DAYS
from organflow.clinical.progression import initialize_urgency
from organflow.compatibility_markers import OrganType
from organflow.Patient import Patient

# Two competing per-round hazards act on a living graft, both constant-annual-rate converted like
# mortality/removal. They must compete, or (with only a failure hazard) every graft would
# eventually fail and its recipient relist - whereas in reality most recipients die WITH a
# functioning graft, or the graft outlives them.
#
# 1. Graft failure. A single lumped annual rate (early rejection/technical loss + ongoing chronic
#    loss), not per-organ half-lives. A failure either relists or is a post-transplant death.
GRAFT_FAILURE_ANNUAL_RATE = 0.055
# 2. Recipient exit with a functioning graft: death from other causes, the graft outliving the
#    recipient, or loss to follow-up - the graft ends without a re-transplant. Sized above the
#    failure rate so eventual relisting is bounded to a realistic fraction of recipients (only
#    ~1 in 6 grafts leads to a relist), not the ~half a failure-only model would produce.
GRAFT_RECIPIENT_EXIT_ANNUAL_RATE = 0.12

# Of the grafts that fail, the fraction whose patient RELISTS rather than dying post-transplant.
# Organ-specific and the main driver of which organs generate re-transplants: a failed kidney
# bridges on dialysis so nearly all relist; a failed heart or lung is usually fatal, so few do.
# Documented approximations (OPTN re-transplant shares: kidney ~10%, thoracic far less).
GRAFT_FAILURE_RELIST_FRACTION = {
    OrganType.Kidney:     0.90,
    OrganType.Liver:      0.45,
    OrganType.Heart:      0.30,
    OrganType.Lungs:      0.35,
    OrganType.Pancreas:   0.75,
    OrganType.Intestines: 0.45,
}
_DEFAULT_RELIST_FRACTION = 0.5

# Re-transplant candidates as a share of all new listings (kidney ~9.6%, liver 3.4%, blended over
# the organ mix). The real 70,600 national additions ALREADY include re-transplants, so exogenous
# generation covers only the first-time share (1 - this) and the graft-failure loop supplies the
# rest endogenously - keeping total inflow calibrated (mean-preserving) rather than double-counting
# re-transplants on top of the national figure. Also the validation TARGET for the emergent share.
# Because the graft pool fills over a graft-lifetime timescale, the emergent share approaches this
# from below at an 8-year horizon (the same "still approaching steady state" caveat the wait-list
# carries), so total inflow runs slightly under national until then. Source: OPTN/SRTR 2024.
# Documented approximation - VERIFY per organ.
RETRANSPLANT_SHARE_OF_LISTINGS = 0.09

# Extra unacceptable HLA antigens a relisting patient gains (antibodies raised by the prior graft),
# widening their cPRA so re-transplant candidates are harder to crossmatch - a real, signature
# effect. A mild bump on the ANTIGEN_POOL_SIZE=50 pool (1-5 antigens -> cPRA ~0.12-0.45): enough
# that re-transplants wait longer, but not so much they pile up unmatched and distort deaths.
RELIST_SENSITIZATION_MIN = 1
RELIST_SENSITIZATION_MAX = 5


def per_round_graft_failure_prob(annual_rate: float = GRAFT_FAILURE_ANNUAL_RATE) -> float:
    """
    Probability a living graft fails during one round, under a constant-hazard model over
    ROUND_DURATION_DAYS - the same conversion mortality.py and removal.py use.

    :param float annual_rate: annualized graft-failure hazard
    :return: per-round graft-failure probability in [0, 1)
    """
    dt_years = ROUND_DURATION_DAYS / DAYS_PER_YEAR
    return 1.0 - math.exp(-annual_rate * dt_years)


def prepare_relist(patient: Patient, rng: Optional[random.Random] = None) -> None:
    """
    Turns a failed-graft recipient into a re-transplant wait-list candidate, in place: marks them
    a re-transplant, resets their wait clock to a fresh listing, re-initializes urgency for the new
    organ failure, and raises sensitization (prior-transplant antibodies) so they are harder to
    match.

    :param Patient patient: the recipient whose graft failed (mutated in place)
    :param random.Random rng: optional seeded source (defaults to the global module)
    """
    source = rng or random
    patient.is_retransplant = True
    patient.rounds_waited = 0
    initialize_urgency(patient, rng)

    extra_count = source.randint(RELIST_SENSITIZATION_MIN, RELIST_SENSITIZATION_MAX)
    new_antigens = source.sample(range(ANTIGEN_POOL_SIZE), extra_count)
    patient.unacceptable_antigens = patient.unacceptable_antigens | frozenset(new_antigens)
    patient.cpra = cpra(patient.unacceptable_antigens)


def simulate_graft_failures(grafts: List[Patient], rng: Optional[random.Random] = None
                            ) -> Tuple[List[Patient], int, List[Patient]]:
    """
    Rolls one round of the two competing graft hazards over a registry of living grafts. Each graft
    either fails (per_round_graft_failure_prob), or its recipient exits with a functioning graft
    (per_round graft-recipient exit), or it survives. A failure then either relists (prepared for
    the wait list) or is a post-transplant death, split by the organ-specific
    GRAFT_FAILURE_RELIST_FRACTION. A recipient exit leaves the registry with no wait-list effect.

    Pure with respect to the registry (returns the partition; the caller rebuilds it), so a graft
    can only fail after surviving at least the round it was transplanted in.

    :param grafts: the living grafts eligible to fail this round (recipients transplanted earlier)
    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: (relisted patients prepared for the wait list, count of post-transplant deaths,
        grafts that survived and remain in the registry)
    """
    source = rng or random
    fail_prob = per_round_graft_failure_prob(GRAFT_FAILURE_ANNUAL_RATE)
    exit_prob = per_round_graft_failure_prob(GRAFT_RECIPIENT_EXIT_ANNUAL_RATE)

    relisted: List[Patient] = []
    survivors: List[Patient] = []
    deaths = 0
    for patient in grafts:
        roll = source.random()
        if roll >= fail_prob + exit_prob:
            survivors.append(patient)  # graft still functioning
            continue
        if roll >= fail_prob:
            continue  # recipient exited with a functioning graft - leaves the registry, no relist
        relist_fraction = GRAFT_FAILURE_RELIST_FRACTION.get(
                patient.organ_needed, _DEFAULT_RELIST_FRACTION)
        if source.random() < relist_fraction:
            prepare_relist(patient, rng)
            relisted.append(patient)
        else:
            deaths += 1
    return relisted, deaths, survivors
