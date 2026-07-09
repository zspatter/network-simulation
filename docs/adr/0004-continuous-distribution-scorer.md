# ADR-0004: Model continuous distribution as a weighted scorer; sweep its geography weight

**Date**: 2026-07-08 · **Status**: Accepted

## Context

Real OPTN policy is moving from hard geographic boundaries (regions → distance circles) to
**continuous distribution**, where distance is one continuously-weighted point factor with no
boundary (already live for lung; heart and liver in progress). The existing geographic models in
the codebase are all hard constraints applied by `TieredMatcher`. To study where policy is
headed, the model needs a soft, continuous geography term — and, more importantly, a way to ask
"how much geographic weight is right?" rather than assuming an answer.

## Decision

Add `ContinuousDistributionScore`: a single weighted sum of medical urgency, waiting time,
geographic proximity, and sensitization, with **no hard boundary**. Expose the weights as fields
so `execute/frontier_analysis.py` can sweep the proximity weight and trace the trade-off frontier
rather than reporting one point.

## Consequences

- The sweep surfaced a non-obvious, policy-relevant result: ignoring geography entirely is
  *worse* on life-years (far-flung organs waste more and graft worse), so a moderate geographic
  weight is Pareto-optimal. See [METHODOLOGY.md](../METHODOLOGY.md) §5.
- `TrialMetrics` records per-transplant transit to provide the geographic-cost axis.
- The hard-constraint tier models remain, so the benchmark can compare "hard boundary" vs.
  "continuous" head to head.
