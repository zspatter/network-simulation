# ADR-0009: Model pediatric priority as a scorer bonus in the policy scorers only

**Date**: 2026-07-09 · **Status**: Accepted

## Context

Real allocation gives pediatric candidates (< 18) substantial priority - very strong for heart
and kidney, and via PELD (rather than MELD) for liver. The model treated every candidate the
same regardless of age, so it could not represent this policy lever or measure what it buys
pediatric patients.

## Decision

Add `Patient.is_pediatric`, generated per an organ-specific fraction (`PEDIATRIC_FRACTION_BY_ORGAN`
- peds are a large share of intestine listings, a small share of kidney/lung). Apply a pediatric
**priority bonus** only in the policy-modeling scorers: a flat `+25` to `RealWorldScore`'s policy
points and a `pediatric_weight` term in `ContinuousDistributionScore`. The comparison-baseline
scorers (`PriorityScore`, `AcuityScore`, `CompositeScore`) are left unchanged, so a benchmark can
still isolate the pediatric effect by holding the scorer's other factors fixed.

The bonus is large but not absolute - decisive on the low-numbered heart status scale, a
strong-but-beatable boost on the wider kidney/lung scales, which is roughly how real policy treats
peds across organs.

## Consequences

- Measured directly: adding the priority raised pediatric transplants ~69% (35 → 59) from the
  same organ pool in a scarce scenario, isolating only the pediatric weight (metamorphic test).
- National calibration is unchanged: the priority *reorders* who among the feasible set is
  matched, adding no inflow or outflow, so total transplants/discard/deaths are unaffected.
- `TrialMetrics` records pediatric seen/transplanted/died, so the equity effect is a first-class,
  measurable outcome.
- The pediatric fractions are documented approximations flagged to verify against the exact OPTN
  pediatric-additions figures (as the arrival mix and discard rates were before being pinned).
