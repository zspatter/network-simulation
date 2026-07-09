# ADR-0008: Model DCD vs DBD donor quality as a mean-preserving discard/graft modifier

**Date**: 2026-07-09 · **Status**: Accepted

## Context

US deceased donors follow two pathways: donation after brain death (DBD) and donation after
circulatory death (DCD). DCD organs endure a warm-ischemia interval between withdrawal of support
and cold perfusion, so they are recovered later, discarded more often, and graft somewhat worse.
DCD is now a large and growing share - 7,284 of 16,989 deceased donors in 2024 (~43%). The model
treated all donors identically, so it could not represent this quality difference or study the
utilization questions (marginal-organ acceptance) that current policy debates center on.

## Decision

Add donor pathway as a **donor-level attribute** (`Organ.donor_type`, a `DonorType` enum),
generated per donor from the 2024 57%/43% split. DCD raises discard and lowers graft survival via
per-pathway multipliers in `clinical.acceptance`.

Crucially, the discard multipliers (DBD ×0.78, DCD ×1.30) are **mean-preserving** over the
57/43 split: `0.57 × 0.78 + 0.43 × 1.30 ≈ 1.0`. So `BASE_DISCARD_PROB` remains the population
average matching the observed 2024 non-use, and the split merely *redistributes* discard toward
DCD rather than inflating the total.

## Consequences

- National calibration is unchanged: deceased transplants stay at 1.00× of 42,048 and organ
  non-use at 21.7% vs. the observed 20.7% - verified with `validate_realism.py` after the change.
  Donor quality now shows up in *outcomes* (which organs are wasted, how long grafts last)
  without perturbing the validated aggregates.
- A test asserts the multipliers are mean-preserving, so the calibration can't silently drift if
  the multipliers or the split are edited.
- This is the hook for future marginal-organ / KDPI-style utilization work: a continuous
  donor-quality index would generalize the binary DBD/DCD split.
