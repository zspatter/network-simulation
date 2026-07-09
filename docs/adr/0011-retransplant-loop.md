# ADR-0011: Model graft failure and re-transplantation as an endogenous feedback loop

**Date**: 2026-07-09 · **Status**: Accepted

## Context

A transplant was a terminal event: the recipient left the simulation for good. But a real graft can
fail, and when it does the patient may relist as a re-transplant candidate - ~9.6% of kidney
transplants and 3.4% of liver candidates are re-transplants (OPTN/SRTR 2024). Missing this left out
a real, sizeable inflow and, more importantly, the *feedback* it carries: worse graft outcomes
produce more relisting, so demand is coupled to the quality of past allocations, not just to
exogenous arrivals. Re-transplant candidates are also more sensitized (prior-graft antibodies), so
they are harder to match - an equity/access effect the model could not show.

## Decision

Add a **graft registry** of living recipients (populated under `realistic_outcomes`). Each round two
competing constant-hazard risks act on each graft (`clinical.retransplant`):

- **Graft failure** (~5.5%/yr): the graft fails. By an organ-specific relist fraction (kidney 90%,
  heart 30%, …) the patient either **relists** - reset wait clock, re-initialized urgency, and a
  cPRA bump for prior-graft antibodies - or is a **post-transplant death**.
- **Recipient exit** (~12%/yr): the recipient dies of other causes or the graft outlives them. This
  competing risk is essential - without it, a constant failure hazard would eventually fail *every*
  graft and relist ~half of all recipients, whereas most recipients in reality die with a working
  graft. It bounds eventual relisting to a realistic ~1-in-6 of recipients.

Post-transplant deaths are tracked **separately** from wait-list deaths (the patient had already
left the list via transplant), so they never inflate the wait-list-death calibration.

**Calibration is mean-preserving.** The national 70,600 additions already include re-transplants, so
exogenous generation is reduced to the first-time share `(1 - RETRANSPLANT_SHARE_OF_LISTINGS)` and
the loop supplies the rest - re-transplants are redistributed *within* the calibrated total, not
added on top of it. (An early additive version, generating 70,600 first-time arrivals *plus*
relists, double-counted re-transplants and pushed wait-list size to 1.07x and deaths to 1.41x; the
split restored both.)

## Consequences

- Calibration held or improved: deceased transplants stay 1.00x of 42,048, and wait-list deaths
  landed at 1.00x of ~6,000 (from 1.24x) - reducing first-time arrivals to make room for
  re-transplants brought total inflow into line with the death outflow. Non-use and living-donor
  transplants are unchanged. Verified with `validate_realism.py`.
- The re-transplant share is a first-class, measurable outcome and a new validation row. It
  **ramps**: the graft pool fills over a graft-lifetime timescale, so the emergent share is ~6% at
  the 8-year horizon and reaches the ~9% target only near steady state (~20 years) - the same "still
  approaching steady state" caveat the wait-list size carries. Pre-seeding a steady-state graft pool
  would remove the ramp and is the natural future refinement.
- A metamorphic test asserts the feedback loop directly: more donor supply -> more grafts -> more
  later graft failures -> more re-transplant listings.
- The blended graft-failure rate and the recipient-exit rate are documented approximations tuned so
  eventual relisting matches the observed share; per-organ graft-survival curves are a flagged
  VERIFY item for future refinement.
