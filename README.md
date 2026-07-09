# OrganFlow
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/getit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/zspatter/organflow/actions/workflows/ci.yml/badge.svg)](https://github.com/zspatter/organflow/actions/workflows/ci.yml)

This project simulates the US deceased-organ-donor transplant matching process across a network of hospitals, and uses that simulation to **compare allocation strategies** - i.e. to answer, empirically, "what's the best way to allocate scarce organs?" rather than assume there's one obvious answer.

At a high level: a network of hospitals is generated (or imported from real coordinates), patients in need of a transplant are added to a wait list, organs are harvested from deceased donors, and an **allocation strategy** decides which feasible organ/patient pairs to actually match. Patients and organs are generated from real-world frequency distributions, patients carry organ-specific medical urgency that worsens while they wait, and patients who wait too long die on the wait list - so a strategy's quality can be judged by lives saved, not just organs transplanted. A benchmark harness runs many randomized, seeded simulations per strategy and reports the comparison.

**<ins>The following criteria determine whether a match is feasible</ins>:**
1. The patient's need must be of the same organ type (kidney, lungs, heart, etc.)
2. The patient must be of a compatible blood type (example: patient: AB-, organ: B-)
3. The organ must be able to be transported to the patient's hospital and still leave enough of its cold-ischemia budget for the implant-to-reperfusion step before it's no longer viable (both are organ-specific - see `Organ.get_viability`/`Organ.get_operation_buffer`; the operation buffer is the portion of the recipient operation that runs *within* the cold-ischemia window, not the full OR time)
4. Organ-specific clinical constraints must be met: donor/recipient **size** compatibility for heart and lung, and a negative **HLA crossmatch** (sensitization) for kidney - see `organflow.clinical`

**<ins>Which feasible match is chosen depends on the selected allocation strategy</ins>** (see `organflow.allocation`) - see [Allocation Strategies](#allocation-strategies) below.

Patients and donor organs are generated from **real US frequency distributions** (blood type, kidney-dominated organ demand, per-organ donor recovery), and patients carry an organ-specific **medical urgency** (MELD for liver, LAS for lung, status tiers for heart) that **deteriorates while they wait**; patients who wait too long **die on the wait list**. This makes the benchmark's central question - which strategy saves the most lives - answerable, not just which strategy transplants the most organs. See [Clinical Realism](#clinical-realism).

## Getting Started

Requires Python 3.12+.

```bash
pip install -e .[dev]      # installs the package plus pytest/mypy/ruff
pip install -e .[report]   # optional: adds reportlab, for scenario_report.py's PDF output
```

- **Run the interactive simulator** (build a network, generate patients, harvest and allocate organs, pick a strategy from the menu):
  ```bash
  python execute/simulator.py
  ```
- **Compare allocation strategies** (runs every strategy in `STRATEGIES` across several seeded multi-round simulations and prints a comparison table):
  ```bash
  python execute/benchmark_strategies.py
  ```
- **Generate a national scenario report** (real hospital network, multi-year horizons, Markdown/CSV/PDF output - see [Scenario Reports](#scenario-reports)):
  ```bash
  python execute/scenario_report.py
  ```
- **Run the test suite** (100% line/branch coverage on `organflow`):
  ```bash
  pytest --cov=organflow --cov-report=term-missing
  mypy organflow
  ruff check organflow execute tests
  ```

## Project Layout

- `organflow/` - the installable package: the graph/domain model, generators, the allocation-strategy framework, and the clinical-realism model (see below).
- `execute/` - runnable scripts: the interactive simulator, the strategy benchmark, the real-hospital-network data pipeline, the analysis tools (validation, sensitivity, frontier), and a handful of smaller demo/export utilities (see [Scripts](#scripts)).
- `tests/` - one test module per source module, plus property, metamorphic, and calibration suites; run via `pytest`.
- `docs/` - the model reference: [METHODOLOGY.md](docs/METHODOLOGY.md) (every constant, source, calibration target, and validation result), [DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md) (data sources with citations), [FINDINGS.md](docs/FINDINGS.md) (the engineering + realism audit), and [ADRs](docs/adr/) (dated decision records).

## <ins>Allocation Strategies</ins>
`organflow.allocation` decides *which* feasible organ/patient pairs to actually form. A strategy is a (matcher, scorer) pair - the two axes are independent, so strategies can be compared to see whether a result is driven by the matching algorithm, the scoring model, or both:

- **Matchers** (`allocation.matchers`) - *how* matches are chosen:
  - `GreedyMatcher` - processes organs one at a time, assigning each to its highest-scoring available patient (the project's original behavior)
  - `OptimalMatcher` - solves one allocation batch as a maximum-weight bipartite matching (one `scipy.optimize.linear_sum_assignment` per organ type - the Hungarian/Jonker-Volgenant algorithm, built for exactly this rectangular assignment problem), so an earlier low-value match can't crowd out a better one available for a later organ. Originally used `networkx`'s general-graph matching to avoid a scipy dependency, but that algorithm both took minutes and could crash outright once a real wait-list backlog reached tens of thousands of candidates (measured directly against the real national-scale network - see [Scenario Reports](#scenario-reports)); scipy's LAP solver handles that same scale in well under a second.
  - `TieredMatcher` - wraps either matcher with a hard geographic constraint (see [Geographic Allocation Constraints](#geographic-allocation-constraints) below): an organ is only offered outside its current tier once no candidate remains inside it, mirroring the real "match run" waterfall (local, then regional, then national) instead of a single global optimization that treats geography as just another score input
- **Scorers** (`allocation.scoring`) - *how* a match is valued:
  - `PriorityScore` - ranks purely by the patient's priority attribute (the original behavior)
  - `AcuityScore` - ranks by medical acuity (near-term death risk): a "sickest first" policy
  - `CompositeScore` - combines priority, acuity, time already spent on the wait list, and travel cost, inspired by real OPTN/UNOS allocation policy, using hand-picked uniform weights across every organ
  - `RealWorldScore` - scores each organ on its *own* real allocation scale instead of one uniform formula: kidney (KAS-style wait-time + cPRA sensitization points), liver (MELD directly), heart (status tier, inverted), lung (LAS directly - LAS *is* the real composite lung allocation score). Geography enters only as a small continuous "placement efficiency" term here; hard geographic constraints are the `TieredMatcher`'s job, not the scorer's - see below.
- `feasibility.feasible_matches_by_organ` is the single source of truth every matcher builds its candidates from - all four feasibility criteria above are applied there once, so comparing strategies only ever measures differences in matching/scoring, never differences in what counts as a valid match.

`STRATEGIES` (in `allocation.strategies`) exposes ten named combinations that `execute/benchmark_strategies.py` runs across many randomized, seeded multi-round simulations to compare on organs transplanted, organs wasted, **wait-list deaths** (total and among high-acuity patients), median wait to transplant, and a life-years-saved proxy:

- `baseline`, `optimal_priority`, `optimal_composite`, `greedy_composite`, `optimal_acuity`, `composite_acuity` - as before; `baseline` reproduces the project's original greedy/priority-only behavior.
- `real_world_region`, `real_world_circle`, `real_world_unconstrained`, `optimal_real_world_circle` - hold `RealWorldScore` fixed and vary only the geographic constraint, to directly measure what that constraint costs or buys (see below). `real_world_circle` - strict adherence to the geographic model most organs are allocated under today - is the benchmark's default statistical-significance reference (see [Statistical Rigor](#statistical-rigor)), not `baseline`.

#### Geographic Allocation Constraints

Real OPTN policy historically allocated within fixed, arbitrary boundaries - 11 "Regions" and 58 Donation Service Areas (DSAs) - which HRSA found in 2018 "have not and cannot be justified" and directed removed. They were eliminated from kidney/pancreas policy in 2021 and from liver/lung/heart policy in 2018-2020, replaced by concentric distance **circles** (150/250/500 nautical miles from the donor hospital) - still current for kidney, pancreas, and heart. Lung moved further, in March 2023, to **continuous distribution**, where distance is one continuously-weighted point factor with no hard boundary at all; liver/heart continuous distribution is in progress. Sources: [Removal of DSA and Region from Kidney Allocation Policy](https://www.hrsa.gov/optn/professionals/resources/kidney-pancreas/kidney-allocation-system/removal-dsa-region-kidney-allocation-policy), [Continuous Distribution overview](https://www.hrsa.gov/optn/policies-bylaws/policy-issues/continuous-distribution), [Continuous distribution - heart](https://optn.transplant.hrsa.gov/policies-bylaws/a-closer-look/continuous-distribution/continuous-distribution-heart/).

`organflow.allocation.geography` gives the benchmark three points on that spectrum, each a `TierClassifier` consumed by `TieredMatcher`:
- `region_tier` - strict adherence to the legacy arbitrary-region model (`Node.region`; synthetic networks get an arbitrary round-robin region assignment from `GraphBuilder`, real hospital networks use the actual historical OPTN region data imported by `import_hospitals.py`)
- `circle_tier` - strict adherence to the current distance-circle model, via documented transit-hour thresholds approximating the real 150/250/500 NM circles
- `national_tier` - no hard constraint (single tier); pairing this with `RealWorldScore`'s soft geography term approximates where continuous distribution is headed

Comparing `real_world_region` vs. `real_world_circle` vs. `real_world_unconstrained` in the benchmark report (same scorer, only the constraint differs) directly answers "what does this geographic constraint cost or buy us," in lives saved, wait times, and fairness spread.

## <ins>Statistical Rigor</ins>
`execute/benchmark_stats.py` (pure Python, no new dependency) turns the benchmark's per-strategy averages into defensible comparisons instead of just eyeballing means:
- **Paired permutation testing** (`paired_permutation_test`) - strategies within one benchmark run share seeds (identical network topology and arrivals; see `run_trial`), so comparisons are paired, not independent-sample. A distribution-free sign-flip test avoids assuming normality for count metrics like deaths.
- **Bootstrap confidence intervals** (`bootstrap_ci`) on the mean difference, not just a point estimate.
- **Paired effect size** (`paired_effect_size`, Cohen's d) reported alongside p-values, so "statistically significant" isn't conflated with "practically meaningful."
- **Holm-Bonferroni correction** (`holm_bonferroni`) across the multiple strategies compared against one reference in a single run, controlling the family-wise error rate.
- **Sample-size planning** (`required_sample_size`) - given a pilot run's observed variance, computes how many seeds are actually needed to detect a minimum effect of interest, rather than guessing at a seed count.

`benchmark_strategies.compare_to_reference` runs this for every strategy against `real_world_circle` (current real allocation policy for most organs) on the two outcomes the README already centers as the "lives saved" question - `waitlist_deaths` and `life_years_saved` - and `print_significance_report` prints the result as a second plain-text table alongside the main comparison.

## <ins>Scenario Reports</ins>
`execute/scenario_report.py` answers a different question than the benchmark above: not "is this difference statistically significant at toy scale," but "what does this strategy actually buy the country, over years, on the real network" - a shareable, regenerable snapshot document rather than a hypothesis test.

- **Real network**: builds the network once via `import_hospitals.py`'s pipeline (see [Real Hospital Network Data Pipeline](#scripts) below) and reuses it across every strategy/seed/horizon in the run, since (unlike the benchmark's per-seed synthetic topology) the real network doesn't change.
- **Real calibration**: arrivals, donor recovery, and the non-transplant outflow channels are calibrated to OPTN/SRTR 2024 figures - 70,600 new waitlist additions/year (≈1,358/week), 16,989 deceased donors/year (≈327/week), ~7,000 living-donor transplants/year (≈135/week), and a ~5%/year non-death removal hazard, at full scale (`--scale 1.0`). `run_trial`'s round loop generates new patients every round alongside matches, deaths, living-donor transplants, and other removals - so the wait-list trajectory reflects all four real exits/entries, not just transplant and death (which alone forced the list to grow ~4-5x past reality before balancing).
- **`--scale` default is 0.1** (10% of national volume), not 1.0: a single real `real_world_circle`/1-year/1-seed trial at full scale measured **850 seconds** and, before the `OptimalMatcher` fix above, two of four curated strategies crashed outright, because feasibility checking is `O(organs x wait-list size)` per round and the wait-list backlog itself realistically grows into the tens of thousands over a year. At the default 10% scale the same trial completes in ~17 seconds, and the wait-list trajectory scales down proportionally (confirmed directly: ~2,738 at 10% scale vs. ~27,065 at full scale for the same year). Relative comparisons between strategies hold at reduced scale; absolute counts don't claim to be literal national totals unless `--scale 1.0` is used.
- **Curated strategy roster** (`--strategies curated`, the default) isolates a deliberate 4-tier delta rather than comparing all ten `STRATEGIES` by default:
  1. **Current policy** - `real_world_circle`: what kidney/pancreas/heart allocation actually does today.
  2. **Easy win** - `optimal_real_world_circle`: identical policy scoring, but a computed global optimum instead of sequential greedy offers - a backend algorithm change, not a policy fight.
  3. **Medium lift** - `real_world_unconstrained`: same scoring, geographic constraint dropped entirely - mirrors where continuous distribution (already live for lung) is headed for the rest.
  4. **Theoretical ceiling** - `composite_acuity`: acuity + wait time + geography combined, optimally matched - maximizes lives saved but reshapes prioritization philosophy, the hardest lift politically.

  `--strategies all` runs the full `STRATEGIES` roster instead, or an explicit comma-separated list - **configurable so more compute can be spent for a more complete comparison** when wanted, rather than the curated subset being the only option.
- **Configurable horizons and seeds**: `--horizon-years` (default `1,5,10`), `--seeds` (default 5 for the 1-year horizon, 3 for longer ones - runtime compounds with horizon length).
- **Output**: a Markdown report (methodology, per-horizon summary table, year-by-year wait-list-size trajectory, and a significance table reusing `compare_to_reference` when seeds ≥ 2) plus matching CSVs (`--formats markdown,csv`, the default) for pivoting in Excel/pandas; PDF is opt-in (`--formats markdown,csv,pdf`) via the optional `reportlab` dependency, rendered by `scenario_report_pdf.py` so the default path never imports it.

## <ins>Clinical Realism</ins>
`organflow.clinical` grounds the simulation in real-world data so "which strategy is best" is measured the way real allocation policy is judged - by lives saved, not just organ throughput:

- `frequencies` - US-population blood-type distribution, organ demand, and per-organ donor recovery probabilities drive generation, replacing uniform sampling. A single seeded `weighted_choice` helper backs every weighted draw, so generation stays deterministic and testable. Organ need is drawn from the wait-list **additions** mix (a flow), which is deliberately less kidney-dominated than the **prevalence** snapshot (a stock): kidney candidates wait far longer, so they accumulate on the standing list out of proportion to their arrival rate (Little's law), and sampling arrivals from the prevalence mix over-generates kidney arrivals and inflates the backlog.
- `removal` / `living_donor` - the wait-list outflow channels besides transplant and death: a non-death removal competing risk (too sick to transplant / condition improved / transferred / declined) and living-donor transplants (overwhelmingly kidney). A model with only transplant and death as exits cannot balance arrivals except by growing the list - and its death count - unrealistically; these are what let it approach a steady state. Both are strategy-independent and enabled on the reality-calibrated scenario-report path, left off in the bare strategy benchmark so they don't muddy the allocation comparison.
- `acceptance` - what happens to a *matched* organ, so geography and donor quality cost lives rather than only eligibility. A matched organ can still be declined and discarded (a terminal non-use probability calibrated to the 2024 organ-specific rates, rising with accumulated cold ischemia), and a transplanted organ's life-years are scaled down by cold-ischemia time. Donor quality is a continuous **index** (KDPI convention, 0 = ideal .. 100 = marginal) drawn per donor - DCD donors skew marginal - that drives both effects on a continuum, generalizing the earlier binary DBD/DCD split; its discard multiplier is **mean-preserving**, so it redistributes discard toward marginal organs without moving the calibrated national non-use rate. Enabled on the reality-calibrated path (`realistic_outcomes`), so the benchmark can measure which organs get wasted and how long grafts last, not just how many matches formed.
- `retransplant` - the feedback loop the other channels miss: a transplanted recipient enters a graft registry, and each round their graft can **fail** (competing with the recipient dying of other causes with a still-working graft, which most do). A failure either **relists** the patient as a re-transplant candidate - more sensitized than before (prior-graft antibodies raise cPRA), so harder to match - or is a post-transplant death, tracked apart from wait-list deaths. This couples demand to the quality of past allocations (worse graft survival breeds more relisting). Re-transplants are part of the calibrated national additions, so first-time arrivals are generated at *(1 - the re-transplant share)* and the loop supplies the rest, keeping total inflow calibrated. Enabled under `realistic_outcomes`.
- `hla` / `size` / `gates` - mechanistic feasibility gates: donors carry an HLA antigen set and patients their unacceptable antigens (crossmatch positive iff they intersect; cPRA emerges combinatorially from how broadly sensitized a patient is, so ~70% of generated patients are unsensitized and ~10% are highly sensitized), while heart/lung require donor/recipient size compatibility within an organ-specific tolerance. `GATES_BY_ORGAN` registers which gates apply to which organ, plugging into `feasibility.py` without disturbing the universal blood-type/viability checks.
- `urgency` / `mortality` / `progression` - each organ has a native urgency scale (MELD for liver, LAS for lung, status tiers 1-6 for heart; kidney has no acute scale since dialysis sustains candidates) normalized to a common **acuity** in `(0, 1]` via documented anchor points, so a single scorer can rank across organ types. Urgency worsens each round (`urgency.progress`), and acuity drives a per-round death probability via a constant-hazard survival model over a one-week round (`mortality.per_round_death_prob`), calibrated so a constant-severity cohort reproduces published mortality (e.g. liver MELD 90-day mortality ~4% / ~36% / ~84% across the ≤20 / 21-30 / 31-40 bands, kidney ~6%/yr) - verified directly by `tests/test_mortality.py`. `progression.simulate_round_progression` advances every waiting patient, rolls death, and removes and returns the dead each round; it's kept separate from `WaitList` (a pure collection) and from the matchers (a death is a third outcome, orthogonal to a match), so a caller - today, the benchmark's round loop - applies it explicitly once per round.

All of the above is deterministic under a single seeded `random.Random` per trial: the same seed reproduces the same network, arrivals, matches, and deaths, which is what lets the benchmark attribute differences in outcome to the *strategy* rather than to noise.

## <ins>Simulator</ins>
`execute/simulator.py` (`SimulatorSession`) is an interactive console tool for exploring a single allocation pass by hand: build a synthetic network of N hospitals, generate a wait list, harvest organs from N donors, and allocate them with a strategy you pick from the menu (any entry in `STRATEGIES`). It uses the same generators and allocation framework as the benchmark, so it exercises the real feasibility gates and every current strategy.

It is a **single-round demonstrator**, not the full model: it does not run the multi-round clinical dynamics (deterioration, wait-list mortality, non-death removals, living-donor transplants, organ discard) that drive the lives-saved comparison - those live in the round loop of `benchmark_strategies.py` / `scenario_report.py`. Reach for the simulator to get a feel for how a strategy forms matches; reach for the benchmark or scenario report for outcomes.

## Scripts

All scripts live under `execute/` and are run as `python execute/<script>.py` from the repository root.

**Interactive, benchmark & scenario reports**
- `simulator.py` - the interactive console simulator described above.
- `simulation.py` - a small non-interactive scripted demo: builds a hand-written hospital network, generates patients/organs, and runs one allocation pass end-to-end.
- `benchmark_strategies.py` - runs every strategy in `STRATEGIES` across many seeded multi-round simulations and prints the comparison table described in [Allocation Strategies](#allocation-strategies), followed by the paired-significance table described in [Statistical Rigor](#statistical-rigor). Also importable (`run_trial`, `run_benchmark`, `compare_to_reference`) for custom comparisons.
- `benchmark_stats.py` - the pure-Python statistical helpers (permutation test, bootstrap CI, effect size, Holm-Bonferroni correction, sample-size planning) `benchmark_strategies.py` uses - see [Statistical Rigor](#statistical-rigor).
- `benchmark_performance.py` - a runtime benchmark harness for the simulation hot paths. Runs fixed, seeded workloads and can diff a run against a saved baseline (`--out`/`--compare`), recording a workload *fingerprint* (organs transplanted, deaths, final wait-list size) alongside timing so a behavior-preserving optimization can be proven apples-to-apples (identical fingerprint, lower time) rather than eyeballed.

**Analysis & validation** (see [docs/METHODOLOGY.md](docs/METHODOLOGY.md))
- `validate_realism.py` - runs the reality-calibrated model on the real network and prints a model-vs-OPTN-2024 table (deceased/living transplants, deaths, non-use rate, wait-list size). The regenerable companion to `tests/test_calibration.py`.
- `sensitivity_analysis.py` - perturbs each documented-approximation constant ±25% one at a time and reports the swing in the headline outcomes, so a conclusion can be reported with the assumptions it leans on.
- `frontier_analysis.py` - sweeps the geographic weight of the continuous-distribution scorer and traces the medical-benefit-vs-geography trade-off frontier.
- `scenario_report.py` / `scenario_report_pdf.py` - the national scenario report generator described in [Scenario Reports](#scenario-reports); `scenario_report_pdf.py` holds the optional PDF rendering so the `reportlab` import only happens when `--formats` includes `pdf`.

**Real hospital network data pipeline**
- `import_hospitals.py` - builds a `Network` of real US transplant-system locations from the OPTN membership directory CSV (`import/optn_membership/`, downloaded from `hrsa.gov/optn/about/membership/optn-membership-database`), keeping only `Transplant Hospital` and `Independent OPO`/`Hospital Based OPO` rows (the only member types that are physical locations this simulation places patients or organs at - see the module docstring for why some rows share a `centerCode` but still get separate nodes). Coordinates come from the free US Census Bureau batch geocoder, with a rate-limited Nominatim (OpenStreetMap) fallback for the institutional-campus addresses Census can't match (e.g. "One Medical Center Drive") - no API key needed for either. Edge weights are computed directly from those coordinates via `organflow.distance` (no scraping). This replaced an older 2019 xlsx + Bing Maps pipeline; Bing Maps' free/basic tier was retired by Microsoft on June 30, 2025.
- `export_hospital_network.py` / `export_edgelist.py` - export a previously-built (shelve-serialized) network to GEXF or a plain edge-list file for use in external graph tools.
- `hospital_count.py` - tallies hospitals per US state/region from the same membership CSV.
- `generate_networks.py` - generates and serializes a batch of random networks (with their patient/organ populations) for reuse across scripts.

**Demo & utility scripts**
- `network_demo.py` - a minimal script exercising the core `Network`/`Node` API.
- `networkx_demo.py` - demonstrates converting a `Network` to `NetworkX` and drawing it with `matplotlib`.
- `subnetwork_demo.py` - demonstrates `SubnetworkGenerator` filtering a network down to only the nodes with active patients/organs.
- `make_tsv.py` - generates a random edge list in TSV format for external I/O.
- `import_edge_list.py` - converts an edge-list file back into a `Network`.
