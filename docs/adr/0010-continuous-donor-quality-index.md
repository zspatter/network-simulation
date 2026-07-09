# ADR-0010: Generalize DBD/DCD into a continuous donor-quality index

**Date**: 2026-07-09 · **Status**: Accepted

## Context

[ADR-0008](0008-dcd-vs-dbd-donor-quality.md) modeled donor quality as a binary: every organ was
either DBD or DCD, and each pathway carried a single discard/graft multiplier. Real donor quality
is a continuum, not two buckets - the utilization questions current policy debates center on
(should a marginal organ be accepted or discarded? which recipient should get it?) are about
*where on that continuum* an organ sits, which a binary cannot express. ADR-0008 itself flagged a
continuous index as the natural next step.

## Decision

Add a continuous **donor-quality index** per organ on the KDPI convention (0 = ideal donor ..
100 = most marginal; `Organ.quality_index`). A donor's index is drawn from a pathway-specific Beta
distribution (`clinical.frequencies.random_quality_index`): DBD skews toward the ideal end
(mean ~40), DCD toward the marginal end (mean ~60), so the DBD/DCD distinction is retained as the
*shape selector* rather than being the quality model itself. Discard and graft survival are then
driven by the index, not by the pathway:

- **Discard**: a linear multiplier on `BASE_DISCARD_PROB` centered on the population-mean index
  (`POPULATION_MEAN_QUALITY_INDEX`), so it is **mean-preserving** - an average organ multiplies by
  1.0, better organs below, marginal above, and the population mean stays 1.0. The slope is sized
  so the pathway means land near the retired 0.78/1.30 DBD/DCD multipliers.
- **Graft**: organs at or better than the mean graft at full; marginal organs graft progressively
  worse (a pure life-years scaler, sized so a DCD-typical organ grafts ~8% worse, matching the old
  straight DCD reduction).

The binary `DONOR_TYPE_*_MULTIPLIER` dicts are removed. `donor_type` stays on `Organ` as a
reported attribute and the quality-distribution selector.

## Consequences

- National calibration is unchanged: deceased-donor transplants stay at 1.00x of 42,048 and organ
  non-use at 21.8% vs. the observed 20.7% - verified with `validate_realism.py` after the change.
  Mean-preservation is guarded by a test that samples the whole donor population and asserts the
  average discard multiplier is ~1.0, so the calibration can't silently drift if the slope, the
  Beta shapes, or the pathway split are edited.
- Donor quality is now a measurable *utilization* outcome, not just a per-organ knob: `TrialMetrics`
  records the mean quality index of transplanted vs discarded organs, and a metamorphic test
  asserts discarded organs are more marginal on average than transplanted ones (the continuous
  index preferentially wasting marginal organs, which the binary could only assert at two points).
- This is the hook for longevity-matching / marginal-organ-acceptance policy work: a scorer term on
  `quality_index` (e.g. steering high-index kidneys to older recipients, as KDPI-EPTS does) now has
  a continuous quality signal to act on. Left out of scope here - this record covers only the
  utilization/outcome axis, matching what the DBD/DCD model did.
- The pathway Beta shapes and the index-to-discard slope are documented approximations flagged to
  verify against organ-specific KDPI/quality distributions before quoting absolute quality figures.
