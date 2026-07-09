# Architecture Decision Records

Short, dated records of the load-bearing modeling and design decisions — the *why* behind
choices that aren't obvious from the code. Each is immutable once accepted; a later reversal
gets a new record that supersedes the old one.

| # | Decision | Date |
|---|---|---|
| [0001](0001-transit-model.md) | Door-to-door transit is `min(ground, air)`, not a single speed | 2026-07-08 |
| [0002](0002-operation-buffer-is-implant-to-reperfusion.md) | Operation buffer is implant-to-reperfusion, not full OR time | 2026-07-08 |
| [0003](0003-arrivals-are-a-flow-not-a-stock.md) | Arrivals sample the additions mix, not the prevalence snapshot | 2026-07-08 |
| [0004](0004-continuous-distribution-scorer.md) | Model continuous distribution as a weighted scorer; sweep its geography weight | 2026-07-08 |
| [0005](0005-patient-identity-equality.md) | `Patient` uses identity equality; matchers apply side effects explicitly | 2026-07-08 |
| [0006](0006-per-organ-type-optimal-matching.md) | Optimal matching is per-organ-type LAP (scipy), not one global graph match | 2026-07-08 |
| [0007](0007-wait-list-outflow-channels.md) | Model all four wait-list exits, not just transplant and death | 2026-07-08 |
| [0008](0008-dcd-vs-dbd-donor-quality.md) | Model DCD vs DBD donor quality as a mean-preserving discard/graft modifier | 2026-07-09 |
