"""
Real-world frequency distributions for generating patients and donor organs,
plus a seeded weighted-sampling helper. Centralizing the "reality" knobs here
keeps them auditable and lets the generators produce populations whose blood
type / organ-need / organ-supply mixes resemble the actual US transplant
system rather than a uniform fiction.

Sources (approximate, cited for provenance - not exact live figures):
- Blood type: US population distribution (American Red Cross / Stanford Blood
  Center), sampled as a joint (letter, polarity) table rather than an
  independent letter x polarity product, since the real table is joint.
- Organ need: US OPTN wait-list snapshot (~Sept 2024), which is heavily
  kidney-dominated.
- Donor recovery: per-organ recovery likelihood from a deceased donor; kidneys
  are recovered from nearly every donor (and there are two), while heart/lung
  face stricter donor suitability criteria.
"""
from __future__ import annotations

import random
from typing import Dict, List, Optional, Sequence, Tuple, TypeVar

from organflow.BloodType import BloodType
from organflow.compatibility_markers import (
    BloodTypeLetter,
    BloodTypePolarity,
    OrganType,
)

T = TypeVar('T')

# US population blood type distribution (percent). Sampled as a joint table.
US_BLOOD_TYPE_WEIGHTS: Dict[Tuple[BloodTypeLetter, BloodTypePolarity], float] = {
    (BloodTypeLetter.O, BloodTypePolarity.POS):  37.4,
    (BloodTypeLetter.A, BloodTypePolarity.POS):  35.7,
    (BloodTypeLetter.B, BloodTypePolarity.POS):  8.5,
    (BloodTypeLetter.AB, BloodTypePolarity.POS): 3.4,
    (BloodTypeLetter.O, BloodTypePolarity.NEG):  6.6,
    (BloodTypeLetter.A, BloodTypePolarity.NEG):  6.3,
    (BloodTypeLetter.B, BloodTypePolarity.NEG):  1.5,
    (BloodTypeLetter.AB, BloodTypePolarity.NEG): 0.6,
}

# US wait-list *prevalence* by organ (percent) - the standing-list snapshot. Kidney-dominant.
# This is a STOCK, not a flow: it describes who is on the list at a moment, not who joins it.
# Kept for validating a simulated steady-state composition against reality; it is NOT what
# arrivals are drawn from (see US_WAITLIST_ADDITIONS_ORGAN_WEIGHTS and the note there).
US_WAITLIST_ORGAN_WEIGHTS: Dict[OrganType, float] = {
    OrganType.Kidney:     85.0,
    OrganType.Liver:      9.0,
    OrganType.Heart:      3.3,
    OrganType.Pancreas:   1.7,
    OrganType.Lungs:      0.9,
    OrganType.Intestines: 0.2,
}

# US wait-list *additions* by organ - the flow new patients are generated from. These are the
# actual 2024 new-registration counts (used directly as sampling weights; weighted_choice
# normalizes them). Source: OPTN/SRTR 2024 Annual Data Report, Overview
# (https://srtr.hrsa.gov/adr/2024/Overview/), retrieved 2026-07-08. Kidney-pancreas (1,667)
# is folded into Pancreas with pancreas-alone/after-kidney (312), since a one-organ-per-patient
# model can't represent the dual need and the pancreas is the distinguishing organ.
#
# This flow is far less kidney-dominated than the prevalence snapshot above (65% vs 85% kidney):
# kidney candidates wait far longer (dialysis sustains them for years) so they accumulate on the
# standing list out of all proportion to their arrival rate. By Little's law the standing mix is
# roughly (arrival rate x mean wait), so sampling arrivals from the standing mix - as the model
# originally did - over-generates kidney arrivals and inflates the backlog.
US_WAITLIST_ADDITIONS_ORGAN_WEIGHTS: Dict[OrganType, float] = {
    OrganType.Kidney:     50_481.0,
    OrganType.Liver:      15_395.0,
    OrganType.Heart:      6_068.0,
    OrganType.Lungs:      3_822.0,
    OrganType.Pancreas:   1_979.0,  # kidney-pancreas (1,667) + pancreas alone/after-kidney (312)
    OrganType.Intestines: 128.0,
}

# Probability that a given organ is recovered (suitable for transplant) from a
# single deceased donor, evaluated independently per organ. Kidney also yields
# two organs per donor (see KIDNEYS_PER_DONOR). Tuned so aggregate supply stays
# kidney-heavy and below demand.
DONOR_RECOVERY_PROBABILITIES: Dict[OrganType, float] = {
    OrganType.Kidney:     0.95,
    OrganType.Liver:      0.75,
    OrganType.Heart:      0.30,
    OrganType.Lungs:      0.20,
    OrganType.Pancreas:   0.10,
    OrganType.Intestines: 0.03,
}

KIDNEYS_PER_DONOR = 2


def weighted_choice(items: Sequence[T], weights: Sequence[float],
                    rng: Optional[random.Random] = None) -> T:
    """
    Returns one item chosen with probability proportional to its weight.

    Wraps random.choices (weights need not sum to 1). Routing every weighted
    draw through this one helper keeps sampling deterministic and testable
    under a seeded random.Random.

    :param items: values to choose from
    :param weights: relative weight per item (same length as items)
    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: a single chosen item
    """
    source = rng or random
    return source.choices(list(items), weights=list(weights), k=1)[0]


def random_us_blood_type(rng: Optional[random.Random] = None) -> BloodType:
    """
    Returns a BloodType sampled from the US population joint distribution.

    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: a BloodType with realistic (letter, polarity) frequency
    """
    pairs: List[Tuple[BloodTypeLetter, BloodTypePolarity]] = list(US_BLOOD_TYPE_WEIGHTS.keys())
    weights = list(US_BLOOD_TYPE_WEIGHTS.values())
    letter, polarity = weighted_choice(pairs, weights, rng)
    return BloodType(letter, polarity)


def random_waitlist_organ(rng: Optional[random.Random] = None) -> OrganType:
    """
    Returns an OrganType sampled from the US wait-list *prevalence* snapshot
    (kidney-dominant). This is the standing-list mix - use random_arrival_organ to
    generate new patients, since arrivals are a flow, not a stock (see
    US_WAITLIST_ADDITIONS_ORGAN_WEIGHTS).

    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: an OrganType with realistic standing-wait-list frequency
    """
    organs = list(US_WAITLIST_ORGAN_WEIGHTS.keys())
    weights = list(US_WAITLIST_ORGAN_WEIGHTS.values())
    return weighted_choice(organs, weights, rng)


def random_arrival_organ(rng: Optional[random.Random] = None) -> OrganType:
    """
    Returns an OrganType sampled from the US wait-list *additions* mix - the organ a
    newly listed patient needs. Less kidney-dominated than the prevalence snapshot;
    see US_WAITLIST_ADDITIONS_ORGAN_WEIGHTS for why this distinction matters.

    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: an OrganType with realistic new-listing frequency
    """
    organs = list(US_WAITLIST_ADDITIONS_ORGAN_WEIGHTS.keys())
    weights = list(US_WAITLIST_ADDITIONS_ORGAN_WEIGHTS.values())
    return weighted_choice(organs, weights, rng)
