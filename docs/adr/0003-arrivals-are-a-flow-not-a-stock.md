# ADR-0003: Arrivals sample the additions mix, not the prevalence snapshot

**Date**: 2026-07-08 · **Status**: Accepted

## Context

New patients need an organ-need distribution. The model originally sampled arrivals from the
**standing wait-list composition** (~85% kidney). But the standing list is a *stock*, not a
*flow*: kidney candidates dominate it largely because dialysis sustains them for years, so they
accumulate out of proportion to their arrival rate. By Little's law, `prevalence ≈ arrival_rate ×
mean_wait`. Sampling arrivals from prevalence therefore over-generates kidney arrivals and
inflates the backlog.

## Decision

Sample arrivals from a distinct **additions** distribution - the actual 2024 OPTN new-registration
counts by organ (kidney ~65%, not 85%). Keep the prevalence snapshot separately, used only to
validate the *resulting* steady-state composition.

## Consequences

- Two distributions in `frequencies.py`: `US_WAITLIST_ADDITIONS_ORGAN_WEIGHTS` (flow, drives
  generation) and `US_WAITLIST_ORGAN_WEIGHTS` (stock, validation).
- Corrects the largest structural contributor to unrealistic backlog growth, alongside the
  missing outflow channels ([ADR-0007](0007-wait-list-outflow-channels.md)).
- The exact counts are pinned to the 2024 ADR - see
  [DATA_PROVENANCE.md](../DATA_PROVENANCE.md).
