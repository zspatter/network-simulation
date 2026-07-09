import random

from organflow.clinical import mortality, urgency
from organflow.compatibility_markers import OrganType


def test_per_round_death_prob_monotonic_in_acuity():
    probs = [mortality.per_round_death_prob(a) for a in (0.0, 0.25, 0.5, 0.75, 1.0)]
    assert probs == sorted(probs)
    assert all(0.0 <= p < 1.0 for p in probs)


def test_annual_rate_spans_configured_bounds():
    assert mortality.annual_death_rate(0.0) == mortality.ACUITY_MIN_ANNUAL_RATE
    assert mortality.annual_death_rate(1.0) == mortality.ACUITY_MAX_ANNUAL_RATE


def test_rolls_death_is_deterministic_for_same_seed():
    first = [mortality.rolls_death(0.5, random.Random(4)) for _ in range(10)]
    second = [mortality.rolls_death(0.5, random.Random(4)) for _ in range(10)]
    assert first == second


def _cohort_mortality(organ, raw_value, rounds, n=15000, seed=0):
    """Cumulative death fraction for a constant-severity cohort over `rounds`."""
    rng = random.Random(seed)
    acuity = urgency.to_acuity(organ, raw_value)
    dead = 0
    for _ in range(n):
        for _ in range(rounds):
            if mortality.rolls_death(acuity, rng):
                dead += 1
                break
    return dead / n


def test_liver_90day_mortality_matches_meld_bands():
    # ~90 days at ROUND_DURATION_DAYS (7) is ~13 rounds. Targets from published
    # MELD 90-day mortality: ~4% (<=20), ~36% (21-30), ~84% (31-40). Tolerances
    # are generous - these are calibrated approximations, not exact instruments.
    rounds = round(90 / mortality.ROUND_DURATION_DAYS)
    assert abs(_cohort_mortality(OrganType.Liver, 15, rounds) - 0.04) < 0.05
    assert abs(_cohort_mortality(OrganType.Liver, 25, rounds) - 0.36) < 0.10
    assert abs(_cohort_mortality(OrganType.Liver, 35, rounds) - 0.84) < 0.10


def test_kidney_annual_mortality_is_low():
    rounds = round(365 / mortality.ROUND_DURATION_DAYS)
    # dialysis sustains kidney patients: ~6%/yr
    assert abs(_cohort_mortality(OrganType.Kidney, 0, rounds) - 0.06) < 0.04
