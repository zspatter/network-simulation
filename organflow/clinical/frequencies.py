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
    DonorType,
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

# Fraction of new listings that are pediatric (< 18), by organ. Peds are a small share of the
# kidney/lung lists but a large share of intestine listings (intestinal failure is heavily
# pediatric) and a meaningful share for heart/liver. Documented approximations - VERIFY against
# the exact OPTN pediatric-additions figures before quoting the absolute pediatric counts.
PEDIATRIC_FRACTION_BY_ORGAN: Dict[OrganType, float] = {
    OrganType.Kidney:     0.02,
    OrganType.Liver:      0.06,
    OrganType.Heart:      0.11,
    OrganType.Lungs:      0.02,
    OrganType.Pancreas:   0.005,
    OrganType.Intestines: 0.25,
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

# Deceased-donor pathway split (donation after brain death vs. after circulatory death).
# 2024 counts: 9,705 DBD and 7,284 DCD of 16,989 deceased donors (~57% / 43%). DCD is a large,
# growing share; DCD organs are recovered later, discarded more, and graft slightly worse - see
# clinical.acceptance. Source: OPTN/SRTR 2024 ADR, Deceased Organ Donation.
DONOR_TYPE_WEIGHTS: Dict[DonorType, float] = {
    DonorType.DBD: 9_705.0,
    DonorType.DCD: 7_284.0,
}

# Continuous donor-quality index on the KDPI convention: 0 = ideal (lowest-risk) donor,
# 100 = most marginal. It generalizes the binary DBD/DCD split (see clinical.acceptance) into a
# continuum, so utilization/discard and graft survival vary organ-by-organ rather than by a single
# per-pathway step. A donor's index is drawn from a Beta distribution (bounded on [0, 100], no
# calibration constant to overshoot) whose shape depends on the pathway: DBD donors skew toward the
# ideal end, DCD toward the marginal end, since circulatory-death donation adds warm ischemia and
# selects sicker donors. These are documented approximations (real KDPI is a kidney-specific
# percentile from many donor factors); the shapes are chosen so the pathway *means* land where the
# retired DBD/DCD multipliers did - DBD ~40, DCD ~60 - VERIFY against organ-specific KDPI/quality
# distributions before quoting absolute quality figures.
QUALITY_INDEX_BETA_PARAMS: Dict[DonorType, Tuple[float, float]] = {
    DonorType.DBD: (2.0, 3.0),  # Beta mean 0.40 -> index 40
    DonorType.DCD: (3.0, 2.0),  # Beta mean 0.60 -> index 60
}

# Population-mean donor-quality index across the 57/43 DBD/DCD split: the analytic mean of the two
# pathway Beta means weighted by DONOR_TYPE_WEIGHTS ((0.571*40 + 0.429*60) ~= 48.6). This is the
# reference the mean-preserving discard multiplier is centered on and the neutral default an
# organ carries when its quality is unspecified (see clinical.acceptance, Organ). A test asserts
# the generated population mean matches it, so the calibration can't silently drift.
POPULATION_MEAN_QUALITY_INDEX = 48.6


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


def random_donor_type(rng: Optional[random.Random] = None) -> DonorType:
    """
    Returns a deceased-donor pathway (DBD/DCD) sampled from the US 2024 split (~57% DBD).

    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: a DonorType with realistic frequency
    """
    types = list(DONOR_TYPE_WEIGHTS.keys())
    weights = list(DONOR_TYPE_WEIGHTS.values())
    return weighted_choice(types, weights, rng)


def random_quality_index(donor_type: DonorType, rng: Optional[random.Random] = None) -> float:
    """
    Draws a donor-quality index in [0, 100] (KDPI convention: higher = more marginal) from the
    pathway-specific Beta distribution in QUALITY_INDEX_BETA_PARAMS. DCD donors skew toward the
    marginal end, DBD toward the ideal end.

    :param DonorType donor_type: the donor pathway (sets the distribution shape)
    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: a donor-quality index in [0.0, 100.0]
    """
    source = rng or random
    alpha, beta = QUALITY_INDEX_BETA_PARAMS[donor_type]
    return source.betavariate(alpha, beta) * 100.0


def is_pediatric_arrival(organ_type: OrganType, rng: Optional[random.Random] = None) -> bool:
    """
    Draws whether a newly listed patient for `organ_type` is pediatric, using the
    organ-specific PEDIATRIC_FRACTION_BY_ORGAN.

    :param OrganType organ_type: the organ the patient needs
    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: True if the patient is pediatric
    """
    source = rng or random
    return source.random() < PEDIATRIC_FRACTION_BY_ORGAN.get(organ_type, 0.0)
