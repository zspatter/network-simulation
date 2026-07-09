# ADR-0002: Operation buffer is implant-to-reperfusion, not full OR time

**Date**: 2026-07-08 · **Status**: Accepted

## Context

Feasibility requires `viability - transit ≥ operation_buffer`. The original buffers were the
**full operating-room durations** (heart 5 h, liver 8 h, …). Once [ADR-0001](0001-transit-model.md)
made transit realistic (mean ~4.8 h), a heart (6 h viability - 5 h buffer = 1 h transit budget)
became essentially untransplantable - no recipient is within 1 h.

## Decision

Redefine the operation buffer as only the **implant-to-reperfusion** portion of the recipient
operation - the part that actually runs *inside* the cold-ischemia window. Reperfusion restarts
the organ's blood supply partway through the operation; everything after it no longer draws down
the cold-ischemia budget. Approximate anastomosis-to-reperfusion times: kidney 1 h,
heart/lung/pancreas 1.5 h, liver/intestine 2 h.

## Consequences

- Heart/lung transit budget becomes ~4.5 h - realistic regional reach.
- Sizing the buffer as full OR time was double-counting: the post-reperfusion hours were being
  subtracted from a budget they don't belong to.
- `Organ.get_operation_buffer` and its test document this framing explicitly.
