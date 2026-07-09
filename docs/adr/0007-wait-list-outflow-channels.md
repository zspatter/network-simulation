# ADR-0007: Model all four wait-list exits, not just transplant and death

**Date**: 2026-07-08 · **Status**: Accepted

## Context

The original model had only two exits: deceased-donor transplant and death. Transplants are
capped by donor supply, so they can't scale with the list; that left death as the only
size-dependent outflow, forcing the wait list to grow until deaths alone balanced arrivals. That
happens only on an unrealistically large, unrealistically sick list - the model implied a
steady-state ~4-5× reality.

## Decision

Add the real channels the two-exit model omitted:

- **Living-donor transplants** (`clinical/living_donor.py`) - ~7,000/yr, kidney/liver, independent
  of the deceased-donor match run.
- **Non-death removals** (`clinical/removal.py`) - a competing risk for "too sick to transplant /
  condition improved / transferred / declined."
- **Organ acceptance/discard** (`clinical/acceptance.py`) - a recovered organ offered to a
  candidate may be declined and ultimately discarded; base rates are the observed 2024 non-use
  figures, rising with cold ischemia.

All are strategy-independent, off by default in the bare strategy benchmark (to isolate the
allocation decision) and on in the reality-calibrated scenario report.

## Consequences

- Wait-list growth goes from unbounded (~4-5× reality) to a bounded steady state that reproduces
  the 2024 numbers - deceased transplants within 6 of 42,048. See
  [METHODOLOGY.md](../METHODOLOGY.md) §3.
- Discard closes the remaining gap: without it the model over-transplanted and the list
  undershot ~½ reality.
- A conservation-invariant test asserts every patient ends each round as exactly one of waiting /
  transplanted / living-transplanted / died / removed.
