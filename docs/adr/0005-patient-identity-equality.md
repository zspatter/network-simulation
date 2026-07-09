# ADR-0005: `Patient` uses identity equality; matchers apply side effects explicitly

**Date**: 2026-07-08 · **Status**: Accepted

## Context

`Patient` originally defined `__eq__` over eight fields while `__hash__` used only `patient_id`
— an inconsistent hash/eq contract that is fragile in the sets and dicts the matchers use to
track claimed patients (mutating a patient's per-round state could change equality but not hash).
It also carried six hand-written ordering dunders.

## Decision

Make `Patient` equality (and hash) **identity by `patient_id`** — a patient who has deteriorated
is still the same patient. Remove the ordering dunders: the wait-list priority queue sorts on
`(-priority, insertion_counter, patient)` tuples whose unique counter means `Patient` is never
compared, and nothing else orders patients.

Relatedly, matchers stay **side-effect-free** — they return an `AllocationResult`; the caller
(benchmark round loop, CLI) applies removals and deaths explicitly. A death is a third outcome,
orthogonal to matching.

## Consequences

- Hash/eq are consistent and stable across a patient's mutable lifetime — safe for set membership.
- The ordering dunders were dead code; removing them cut ~60 lines.
- The explicit-side-effects convention is what lets progression, removal, and living-donor
  transplants each plug into the round loop as separate, testable steps.
