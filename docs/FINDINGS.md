# Findings

A durable record of the engineering + realism audit and the work it drove. Every load-bearing
number here was measured directly (profiler, real-network runs, `validate_realism.py`), not
asserted. Regenerate any of it via the commands in [METHODOLOGY.md](METHODOLOGY.md) §6.

## Summary

The codebase was already strong - clean matcher/scorer split, a single feasibility source of
truth, seeded determinism, real distribution-free statistics. The audit found two structural
realism gaps and a set of performance hot paths, all since addressed. The model now reproduces
2024 OPTN/SRTR national figures to within a few percent, runs several times faster, and is
guarded by property, metamorphic, mutation, and calibration tests.

## Realism findings

### R1 - the wait list grew without bound (fixed)

Only two exits existed (transplant, death). Transplants are supply-capped, so death alone had to
balance arrivals - which only happens on a list ~4-5× reality. **Fix**: added living-donor
transplants, non-death removals, and organ discard ([ADR-0007](adr/0007-wait-list-outflow-channels.md)).
Growth went from unbounded to a bounded steady state reproducing the 2024 numbers.

### R2 - geography and viability didn't bind (fixed)

The old transit model gave mean ~2.5 h coast-to-coast with a non-physical discontinuity, so
~99% of hospital pairs cleared every viability window and all strategies tied. **Fix**: a
realistic `min(ground, air)` door-to-door model ([ADR-0001](adr/0001-transit-model.md)). Mean
transit is now ~4.8 h; heart/lung reach ~50% of the network, kidney still 100% - geography binds
as it does in reality.

### R3 - arrivals used the standing-list mix (fixed)

Sampling arrivals from the ~85%-kidney prevalence snapshot over-generated kidney arrivals
(a stock-vs-flow error). **Fix**: sample the additions mix ([ADR-0003](adr/0003-arrivals-are-a-flow-not-a-stock.md)).

### Validation

After the fixes, `validate_realism.py` on the real network reproduces 2024 to within a few
percent - deceased transplants within **38 of 42,048** (1.00×), discard 21.8% vs 20.7% (1.05×),
living donors 1.04×. Full table in [METHODOLOGY.md](METHODOLOGY.md) §3.

## Performance findings

Every optimization was verified with a fingerprint-checked benchmark (`benchmark_performance.py`)
or the profiler - a "faster" claim had to show identical behavior.

| Change | Result |
|---|---|
| Memoize per-source transit; index feasibility by organ/blood type; set-backed collections | **2.0-2.5×**, behavior-preserving |
| Parallelize the seed sweep across processes | **~6×** on 8 workers (embarrassingly parallel) |
| Dict-backed wait list (O(1) remove) + gate/crossmatch micro-opts | feasibility cumulative 17.1 s → 10.7 s on the same trial |

Two "obvious" optimizations were **measured and rejected**: a CSR/scipy graph rewrite (the real
network bypasses graph traversal entirely - transit is direct point-to-point), and geographic
candidate pruning (profiling showed the bottleneck was an O(n) list-remove and the HLA gate, not
distance - kidney reaches every hospital). Measuring first avoided both dead ends.

## Analysis findings

### Sensitivity - what the conclusions depend on

Perturbing each constant ±25% (`sensitivity_analysis.py`): **organ supply (donor recovery)
dominates** lives saved (-91% deaths swing); transit overhead (+21%) and mortality calibration
(+11%) are secondary; conclusions are **robust** to the removal rate (+2%) and graft-survival
penalty (0%). So any lives-saved claim rests on supply and transit realism, not the softer knobs.

### Continuous-distribution frontier - geography isn't free to ignore

Sweeping the geographic weight of a continuous-distribution scorer (`frontier_analysis.py`)
surfaced a non-obvious result: **ignoring geography entirely is worse on life-years** (29,182 vs
~31,500), because far-flung organs incur more discard and worse graft survival. A moderate
weight is Pareto-optimal - more life-years *and* lower transit *and* less discard. This is
exactly the nuance continuous distribution is designed to capture.

## Test rigor

- **100% line/branch coverage** on the package, plus:
- **Property-based** (Hypothesis): blood-type compatibility vs. an independent ABO/Rh truth
  table; feasibility invariant to order; optimal ≥ greedy.
- **Metamorphic**: more organs/patients never reduce matches; more supply never increases deaths.
- **Mutation** (mutmut): 22/24 mutants killed on `BloodType.py`; the 2 survivors are equivalent
  mutants (dead defensive initialization) - every behavior-changing mutant caught.
- **Calibration**: `test_calibration.py` asserts the OPTN targets as pass/fail guards.

## Deliberately not done

- **CSR/scipy graph representation** - measured as not the bottleneck (see above).
- **Native-typing / IntEnum sweep** - churn without behavior gain; P2 already removed the enum
  hot-path cost.
