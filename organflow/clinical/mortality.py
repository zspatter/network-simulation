"""
Turns a patient's acuity into a per-round wait-list death probability.

Time is discretized into rounds of ROUND_DURATION_DAYS. Acuity in (0, 1] maps
to an annual death-rate via geometric interpolation between a low- and
high-acuity rate, and that rate is converted to a per-round probability with a
constant-hazard (exponential) survival model:
    per_round_death_prob = 1 - exp(-annual_rate(acuity) * ROUND_DURATION_DAYS / 365)

The low/high annual-rate bounds are chosen so the urgency->acuity anchors in
urgency.py reproduce published wait-list mortality roughly (e.g. a high-MELD
liver cohort's ~90-day mortality), with acuity as the single risk axis so the
model stays organ-agnostic here.
"""
from __future__ import annotations

import math
import random
from typing import Optional

ROUND_DURATION_DAYS = 7.0
DAYS_PER_YEAR = 365.0

# Annual death-rate at the extremes of the acuity scale (rate, not probability;
# fed through the exponential survival model below).
ACUITY_MIN_ANNUAL_RATE = 0.05   # acuity -> 0: minimal near-term risk
ACUITY_MAX_ANNUAL_RATE = 12.0   # acuity -> 1: extreme near-term risk


def annual_death_rate(acuity: float) -> float:
    """
    Geometric interpolation of the annual death rate across the acuity scale,
    so risk rises multiplicatively (not linearly) with acuity.

    :param float acuity: patient acuity in [0, 1]
    :return: annualized death rate (hazard)
    """
    ratio = ACUITY_MAX_ANNUAL_RATE / ACUITY_MIN_ANNUAL_RATE
    return ACUITY_MIN_ANNUAL_RATE * (ratio ** acuity)


def per_round_death_prob(acuity: float) -> float:
    """
    Probability that a patient at the given acuity dies during one round,
    under a constant-hazard survival model over ROUND_DURATION_DAYS.

    :param float acuity: patient acuity in [0, 1]
    :return: death probability in [0, 1) for a single round
    """
    dt_years = ROUND_DURATION_DAYS / DAYS_PER_YEAR
    return 1.0 - math.exp(-annual_death_rate(acuity) * dt_years)


def rolls_death(acuity: float, rng: Optional[random.Random] = None) -> bool:
    """
    Draws whether a patient at the given acuity dies this round.

    :param float acuity: patient acuity in [0, 1]
    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: True if the patient dies this round
    """
    source = rng or random
    return source.random() < per_round_death_prob(acuity)
