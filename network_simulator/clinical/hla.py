"""
Simplified HLA sensitization / crossmatch model.

Real organ matching (kidney especially) is gated by HLA compatibility: a
recipient who has formed antibodies against certain HLA antigens will reject a
donor carrying any of those antigens (a "positive crossmatch"). How broadly a
patient is sensitized is summarized clinically by cPRA - the percentage of the
donor pool they are incompatible with - and highly sensitized patients
(cPRA ~98-100%) wait far longer because almost no donor is acceptable.

This module abstracts that mechanistically but tractably: a fixed pool of
antigen ids, donors carry a small random antigen set, and patients carry a set
of "unacceptable" antigens (their antibodies). Crossmatch is positive iff those
sets intersect. cPRA is then the exact probability a random donor is
incompatible, computed combinatorially. All draws are seeded/deterministic.
"""
from __future__ import annotations

import math
import random
from typing import FrozenSet, Optional

# Size of the antigen universe and how many antigens a donor carries. These are
# deliberately small stand-ins for the real HLA system (hundreds of alleles
# across the A/B/DR loci); the pool size and draw count are chosen so the
# sensitization tiers below yield a realistic spread of cPRA values.
ANTIGEN_POOL_SIZE = 50
DONOR_ANTIGEN_COUNT = 6


def donor_antigens(rng: Optional[random.Random] = None) -> FrozenSet[int]:
    """
    Returns a donor's HLA antigen set: DONOR_ANTIGEN_COUNT distinct antigen ids
    drawn from the pool.

    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: frozenset of antigen ids
    """
    source = rng or random
    return frozenset(source.sample(range(ANTIGEN_POOL_SIZE), DONOR_ANTIGEN_COUNT))


def patient_unacceptable_antigens(rng: Optional[random.Random] = None) -> FrozenSet[int]:
    """
    Returns the set of antigens a patient has antibodies against (their
    "unacceptable" antigens). Modeled in three tiers so the resulting cPRA
    distribution resembles reality: most patients unsensitized (cPRA 0), a
    sizeable minority low-to-moderately sensitized, and a ~10% highly
    sensitized tail (cPRA near 1). Documented approximation, not clinical.

    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: frozenset of antigen ids the patient rejects
    """
    source = rng or random
    roll = source.random()
    if roll < 0.70:
        count = 0                          # unsensitized
    elif roll < 0.90:
        count = source.randint(1, 5)       # low-to-moderately sensitized
    else:
        count = source.randint(15, 45)     # highly sensitized tail
    return frozenset(source.sample(range(ANTIGEN_POOL_SIZE), count))


def crossmatch_positive(organ_antigens: FrozenSet[int],
                        unacceptable: FrozenSet[int]) -> bool:
    """
    Returns True if the crossmatch is POSITIVE (incompatible): the donor carries
    at least one antigen the recipient has antibodies against.

    :param organ_antigens: the donor organ's HLA antigen set
    :param unacceptable: the recipient's unacceptable-antigen set
    :return: True if incompatible, False if the pair is crossmatch-negative
    """
    # ~70% of candidates are unsensitized (empty antibody set); short-circuit before building
    # the set intersection, since this runs once per candidate kidney in feasibility.
    return bool(unacceptable) and bool(organ_antigens & unacceptable)


def cpra(unacceptable: FrozenSet[int]) -> float:
    """
    Calculated Panel Reactive Antibody: the exact probability that a random
    donor (carrying DONOR_ANTIGEN_COUNT antigens drawn from the pool) is
    incompatible with a patient who rejects the given unacceptable antigens.

    cPRA = 1 - P(donor avoids every unacceptable antigen)
         = 1 - C(pool - |unacceptable|, k) / C(pool, k)

    :param unacceptable: the patient's unacceptable-antigen set
    :return: cPRA in [0, 1]
    """
    m = len(unacceptable)
    if m == 0:
        return 0.0
    acceptable = ANTIGEN_POOL_SIZE - m
    if acceptable < DONOR_ANTIGEN_COUNT:
        return 1.0  # too few clean antigens remain for any compatible donor
    p_avoid = (math.comb(acceptable, DONOR_ANTIGEN_COUNT)
               / math.comb(ANTIGEN_POOL_SIZE, DONOR_ANTIGEN_COUNT))
    return 1.0 - p_avoid
