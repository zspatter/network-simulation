# Methodology

How the simulation is grounded in reality: every model constant, its source, the calibration
target it is meant to reproduce, and the measured result. This is the reference for *why* the
numbers are what they are; the code comments carry the same citations inline.

All figures are regenerable - see [Regenerating these results](#regenerating-these-results).

## 1. What the model is

A discrete-event simulation of US deceased-donor organ allocation. One **round = 7 days**. Each
round: new patients are listed, organs are recovered from deceased donors, an allocation
strategy matches feasible organ/patient pairs, and the patients still waiting deteriorate - some
are transplanted from living donors, some are removed for non-death reasons, and some die. The
whole thing is deterministic under one seeded `random.Random`, so differences between strategies
are attributable to the strategy, not noise.

Four exits and two entries govern the wait-list balance (all calibrated below):

```
      arrivals ──►  WAIT LIST  ──► deceased-donor transplant
   living donor ──►           ──► death
                              ──► non-death removal (too sick / improved / transferred)
```

## 2. Clinical constants and their sources

### Organ viability and operation buffer (hours)

`viability` is the maximum cold-ischemia time; `operation_buffer` is the implant-to-reperfusion
portion of the recipient operation that runs *within* that window (not the full OR time - see
[ADR-0002](adr/0002-operation-buffer-is-implant-to-reperfusion.md)). A match is feasible only if
`viability - transit ≥ operation_buffer`.

| Organ | Viability (max CIT) | Operation buffer | Published CIT range |
|---|---|---|---|
| Heart | 6 h | 1.5 h | 4-6 h |
| Lung | 6 h | 1.5 h | 4-8 h |
| Liver | 12 h | 2.0 h | 8-12 h |
| Kidney | 30 h | 1.0 h | 24-36 h |
| Pancreas | 12 h | 1.5 h | 12-18 h |
| Intestine | 8 h | 2.0 h | 6-8 h |

Source: published cold-ischemia-time ranges (transplant literature). `Organ.get_viability` /
`Organ.get_operation_buffer`.

### Transit time

Door-to-door transport is the faster of two modes, `min(ground, air)` - monotonic and
continuous in distance (see [ADR-0001](adr/0001-transit-model.md)):

```
ground = 0.5 h handling + 1.25 × great_circle_km / 105 km·h⁻¹
air    = 2.5 h fixed overhead + great_circle_km / 750 km·h⁻¹
```

Measured on the real 297-node network: mean transit 4.8 h, coast-to-coast ~15 h. This makes
geography bind for the short-window organs (heart/lung reach ~50% of hospitals within budget)
but not for kidney (30 h budget reaches every hospital). `organflow/distance.py`.

### Generation frequencies

| Quantity | Value | Source |
|---|---|---|
| Blood type | US joint (letter, Rh) table | American Red Cross / Stanford Blood Center |
| Arrival organ mix (flow) | Kidney 50,481 / Liver 15,395 / Heart 6,068 / Lung 3,822 / Pancreas 1,979 / Intestine 128 | OPTN/SRTR 2024 ADR new registrations |
| Prevalence organ mix (stock) | 85% kidney (validation only) | OPTN/SRTR waitlist snapshot |
| Donor recovery / donor | Kidney 0.95 (×2) / Liver 0.75 / Heart 0.30 / Lung 0.20 / Pancreas 0.10 / Intestine 0.03 | per-organ recovery likelihood |
| Donor pathway | DBD 57% / DCD 43% | OPTN/SRTR 2024 (9,705 DBD / 7,284 DCD) |
| Donor quality index | KDPI-style 0-100; DBD mean ~40, DCD mean ~60 (per-pathway Beta) | documented approximation (VERIFY vs organ KDPI) |
| Pediatric share of arrivals | Intestine 25% · Heart 11% · Liver 6% · Kidney/Lung 2% · Pancreas 0.5% | documented approximation (VERIFY vs OPTN) |

Arrivals are drawn from the **additions** mix, not the prevalence snapshot - see
[ADR-0003](adr/0003-arrivals-are-a-flow-not-a-stock.md). Each donor carries a continuous
donor-quality index (KDPI convention, 0 = ideal .. 100 = marginal) that drives discard and graft
survival; DCD donors skew marginal, so DCD organs are discarded more and graft worse than DBD as a
special case - see [ADR-0010](adr/0010-continuous-donor-quality-index.md) (which generalized the
earlier binary DBD/DCD model, [ADR-0008](adr/0008-dcd-vs-dbd-donor-quality.md)). Pediatric
candidates (< 18) get a priority bonus in the policy scorers (`RealWorldScore`,
`ContinuousDistributionScore`) - see [ADR-0009](adr/0009-pediatric-priority.md).
`organflow/clinical/frequencies.py`.

### Urgency, mortality, and the non-transplant exits

| Quantity | Value | Source / calibration |
|---|---|---|
| Native urgency scales | MELD (liver), LAS (lung), status tiers (heart) | mapped to a common acuity in (0,1] |
| Mortality hazard | 0.05/yr (acuity→0) … 12.0/yr (acuity→1), geometric | reproduces e.g. liver MELD 90-day mortality bands |
| Non-death removal | 5%/yr competing risk | too sick / improved / transferred / declined |
| Living-donor transplants | ~7,000/yr (kidney/liver) | OPTN/SRTR 2024 (7,024 living donors) |
| Organ discard (non-use) | Kidney 29.3% / Pancreas 25.1% / Liver 11.5% / Lung 11.3% / Intestine 4.9% / Heart 1.9% (population average; scaled by a mean-preserving donor-quality multiplier, so marginal organs are discarded more) | OPTN/SRTR 2024 ADR, Deceased Organ Donation |

`clinical/urgency.py`, `clinical/mortality.py`, `clinical/removal.py`, `clinical/living_donor.py`,
`clinical/acceptance.py`.

## 3. Calibration: model vs. OPTN/SRTR 2024

Output of `python execute/validate_realism.py` (real network, 10% scale extrapolated to full,
8 years, 3 seeds). Targets are the published 2024 national figures.

| Metric | Model | OPTN 2024 | Ratio |
|---|---|---|---|
| Deceased-donor transplants/yr | 42,010 | 42,048 | **1.00×** |
| Living-donor transplants/yr | 7,280 | 7,024 | 1.04× |
| Organ non-use (discard) rate | 21.8% | 20.7% | 1.05× |
| Wait-list deaths/yr | 7,412 | ~6,000 | 1.24× |
| Wait-list size (still climbing at 8 yr) | 91,030 | ~103,000 | 0.88× |
| Non-death removals/yr | 2,639 | ~8,000 | 0.33× |

The primary flows (transplants, discard, living donors) reproduce reality to within a few
percent. The two weakest matches are **coupled**: the 5%/yr removal rate under-produces removals
(0.33×), which leaves slightly too many patients to die (1.24×). Raising the removal rate would
improve both; it is left as a documented knob because the sensitivity analysis (below) shows the
conclusions do not depend on it.

## 4. Sensitivity analysis

Output of `python execute/sensitivity_analysis.py` (each constant perturbed ±25%, swing in the
outcome from low to high, ranked by effect on wait-list deaths):

| Constant | Deaths swing | Interpretation |
|---|---|---|
| donor recovery prob | -91% | **dominant** - organ supply is the fundamental scarcity |
| air overhead (transit) | +21% | secondary - transit realism gates thoracic feasibility |
| max acuity death rate | +11% | secondary - the mortality calibration itself |
| base discard prob | +11% | secondary - fewer transplants → more deaths |
| ischemia discard / hr | -9% | small (near noise at low seed counts) |
| other removal rate | +2% | **robust** - conclusions do not lean on it |
| graft penalty / hr | 0% | **robust** (affects life-years only) |

Takeaway: any conclusion about lives saved rests primarily on organ supply and transit realism,
and is robust to the removal rate and the graft-survival penalty.

## 5. Continuous-distribution frontier

Output of `python execute/frontier_analysis.py` (sweep the geographic proximity weight of the
continuous-distribution scorer; see [ADR-0004](adr/0004-continuous-distribution-scorer.md)):

| proximity weight | life-years | mean transit | discard |
|---|---|---|---|
| 0 (geography ignored) | 29,182 | 4.60 h | 22.0% |
| 0.5-1.0 (sweet spot) | ~31,500 | 1.5-1.8 h | ~21% |
| 8 (hyper-local) | 31,479 | 1.36 h | 21.1% |

**Non-obvious result**: ignoring geography entirely is *worse* on life-years, because far-flung
organs incur more cold-ischemia discard and worse graft survival. A moderate geographic weight
is Pareto-optimal (more life-years *and* lower transit *and* less discard).

## 6. Regenerating these results

```bash
python execute/validate_realism.py       # §3 model-vs-OPTN table
python execute/sensitivity_analysis.py   # §4 sensitivity sweep
python execute/frontier_analysis.py      # §5 continuous-distribution frontier
python execute/benchmark_performance.py  # performance (fingerprint-checked)
pytest tests/test_calibration.py         # §3 targets as pass/fail guards
```

Data provenance and citations: [DATA_PROVENANCE.md](DATA_PROVENANCE.md). Design decisions:
[adr/](adr/). Engineering + realism findings: [FINDINGS.md](FINDINGS.md).
