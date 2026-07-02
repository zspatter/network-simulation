# Network Simulation
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/getit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/zspatter/network-simulation/actions/workflows/ci.yml/badge.svg)](https://github.com/zspatter/network-simulation/actions/workflows/ci.yml)

This project simulates the US deceased-organ-donor transplant matching process across a network of hospitals, and uses that simulation to **compare allocation strategies** - i.e. to answer, empirically, "what's the best way to allocate scarce organs?" rather than assume there's one obvious answer.

At a high level: a network of hospitals is generated (or imported from real coordinates), patients in need of a transplant are added to a wait list, organs are harvested from deceased donors, and an **allocation strategy** decides which feasible organ/patient pairs to actually match. Patients and organs are generated from real-world frequency distributions, patients carry organ-specific medical urgency that worsens while they wait, and patients who wait too long die on the wait list - so a strategy's quality can be judged by lives saved, not just organs transplanted. A benchmark harness runs many randomized, seeded simulations per strategy and reports the comparison.

**<ins>The following criteria determine whether a match is feasible</ins>:**
1. The patient's need must be of the same organ type (kidney, lungs, heart, etc.)
2. The patient must be of a compatible blood type (example: patient: AB-, organ: B-)
3. The organ must be able to be transported to the patient's hospital, and leave enough time to complete the transplant procedure, before it's no longer viable (both are organ-specific - see `Organ.get_viability`/`Organ.get_operation_buffer`)
4. Organ-specific clinical constraints must be met: donor/recipient **size** compatibility for heart and lung, and a negative **HLA crossmatch** (sensitization) for kidney - see `network_simulator.clinical`

**<ins>Which feasible match is chosen depends on the selected allocation strategy</ins>** (see `network_simulator.allocation`) - see [Allocation Strategies](#allocation-strategies) below.

Patients and donor organs are generated from **real US frequency distributions** (blood type, kidney-dominated organ demand, per-organ donor recovery), and patients carry an organ-specific **medical urgency** (MELD for liver, LAS for lung, status tiers for heart) that **deteriorates while they wait**; patients who wait too long **die on the wait list**. This makes the benchmark's central question - which strategy saves the most lives - answerable, not just which strategy transplants the most organs. See [Clinical Realism](#clinical-realism).

## Getting Started

Requires Python 3.12+.

```bash
pip install -e .[dev]      # installs the package plus pytest/mypy/ruff
```

- **Run the interactive simulator** (build a network, generate patients, harvest and allocate organs, pick a strategy from the menu):
  ```bash
  python execute/simulator.py
  ```
- **Compare allocation strategies** (runs every strategy in `STRATEGIES` across several seeded multi-round simulations and prints a comparison table):
  ```bash
  python execute/benchmark_strategies.py
  ```
- **Run the test suite** (100% line/branch coverage on `network_simulator`):
  ```bash
  pytest --cov=network_simulator --cov-report=term-missing
  mypy network_simulator
  ruff check network_simulator execute tests
  ```

## Project Layout

- `network_simulator/` - the installable package: the graph/domain model, generators, the allocation-strategy framework, and the clinical-realism model (see below).
- `execute/` - runnable scripts: the interactive simulator, the strategy benchmark, the real-hospital-network data pipeline, and a handful of smaller demo/export utilities (see [Scripts](#scripts)).
- `tests/` - one test module per source module; run via `pytest`.

## Classes

### <ins>Node</ins>
The smallest element within the network is a Node object. Each node represents a specific hospital where both patients and organs can be located. These will represent the 'addresses' of sources and destinations within the graph based on an organ's location and the matched patient's location.

**<ins>Nodes consist of</ins>:**
1. `node ID` - a unique identifier
2. `label` - describes/names the node
3. `adjacency dictionary` - where the adjacent node's id is the key and another dictionary with two entries is the value. This allows each edge to have two important attributes - weight and status (active or inactive)
4. `status` - indicates if a node is active or inactive. If the node is inactive, all edges contained in the adjacency list are consequently inactive as well
5. `region` / `city` / `state` / `latitude` / `longitude` - optional real-world metadata, populated when a node represents an actual hospital imported from coordinates (see `import_hospitals.py`)

### <ins>Network</ins>
The network is a graph that is represented as a collection of nodes. The network represents the entire network of hospitals. The network will be traversed from node to node to. The weights of individual edges traveled will be added together to represent the total cost of the traveled path.

**<ins>Networks consist of</ins>:**
1. `network dictionary` - contains a collection of `node IDs` that point to their corresponding `Node` objects
2. `label` - describes/names the graph

Edge weight is always **estimated transit time in hours** - the same unit `Organ.viability` is expressed in - whether the network is randomly generated (`GraphBuilder`) or built from real hospital coordinates (`import_hospitals.py`, via `network_simulator.distance`'s haversine calculation). That shared unit is what makes an organ's remaining viability and a Dijkstra shortest-path cost directly comparable.

### <ins>BloodType, Organ, Patient</ins>
- `BloodType` - a letter (O/A/B/AB) and polarity (+/-) pair; checks ABO/Rh compatibility between a prospective donor and recipient in both directions.
- `Organ` - a single donated organ available for transplant: type, blood type, remaining viability (hours), origin/current location, and its transit path once matched. Also carries donor clinical attributes used by the mechanistic feasibility gates: `hla_antigens` (the donor's HLA antigen set) and `donor_size` (body size, for heart/lung size matching).
- `Patient` - an individual on the wait list: name, illness, organ needed, blood type, a legacy `priority` int, location, and `rounds_waited` (incremented once per simulation round). Also carries the clinical state populated by the generator and evolved each round by the deterioration model: `acuity` (0-1 near-term death risk, normalized across organ types), `raw_urgency` (the organ-native score - MELD/LAS/status tier), `body_size`, `unacceptable_antigens` (the patient's anti-HLA antibodies), and `cpra` (their computed sensitization percentage). These clinical fields are deliberately excluded from equality/hashing, since they're mutable per-round state - see the class docstrings for why.

### <ins>OrganList, WaitList</ins>
- `OrganList` - the collection of organs currently available to be allocated.
- `WaitList` - the collection of patients currently waiting for a transplant. `get_prioritized_patients` returns a max-heap by legacy `priority`; `increment_wait_times` bumps every remaining patient's `rounds_waited` once per round.

### <ins>Other Classes</ins>
-  `Dijkstra` - finds all shortest paths from a source node in a given graph
-  `GraphBuilder` - builds a random network with N nodes (edge weights are synthetic but expressed in the same "hours" unit as real networks)
-  `OrganGenerator` - harvests organs from N deceased donors using per-organ recovery probabilities (kidney recovered from nearly every donor and yields two; heart/lung less often) and adds them to an `OrganList`
-  `PatientGenerator` - generates N patients with realistic organ need / blood type / body size / HLA sensitization / initial urgency, plus a location, and adds them to a `WaitList`
-  `ConnectivityChecker` - determines if a given graph is connected 
-  `SubnetworkGenerator` - takes a `Network` and a collection (`OrganList` or `WaitList`) and creates a subnetwork containing only nodes where elements of the collection are present
-  `GraphConverter` - converts a `Network` to a `NetworkX` (graph library) object, optionally including hospital attributes (city/state/region/counts) for visualization or analysis
-  `distance` - computes real-world hospital distances (haversine) and estimated transit time directly from coordinates, instead of scraping a distance-lookup site
-  `clinical` - real-world grounding: frequency distributions, HLA crossmatch + size-matching feasibility gates, and the organ-specific urgency / deterioration / wait-list-mortality model (see [Clinical Realism](#clinical-realism))
-  `exceptions` - `GraphElementError`, raised (and caught internally, with an optional printed message) for invalid graph operations like adding a duplicate node or edge

### <ins>Allocation Strategies</ins>
`network_simulator.allocation` decides *which* feasible organ/patient pairs to actually form. A strategy is a (matcher, scorer) pair - the two axes are independent, so strategies can be compared to see whether a result is driven by the matching algorithm, the scoring model, or both:

- **Matchers** (`allocation.matchers`) - *how* matches are chosen:
  - `GreedyMatcher` - processes organs one at a time, assigning each to its highest-scoring available patient (the project's original behavior)
  - `OptimalMatcher` - solves one allocation batch as a maximum-weight bipartite matching (via `networkx`), so an earlier low-value match can't crowd out a better one available for a later organ
- **Scorers** (`allocation.scoring`) - *how* a match is valued:
  - `PriorityScore` - ranks purely by the patient's priority attribute (the original behavior)
  - `AcuityScore` - ranks by medical acuity (near-term death risk): a "sickest first" policy
  - `CompositeScore` - combines priority, acuity, time already spent on the wait list, and travel cost, inspired by real OPTN/UNOS allocation policy
- `feasibility.feasible_matches_by_organ` is the single source of truth every matcher builds its candidates from - all four feasibility criteria above are applied there once, so comparing strategies only ever measures differences in matching/scoring, never differences in what counts as a valid match.

`STRATEGIES` (in `allocation.strategies`) exposes six named combinations - `baseline`, `optimal_priority`, `optimal_composite`, `greedy_composite`, `optimal_acuity`, and `composite_acuity` - that `execute/benchmark_strategies.py` runs across many randomized, seeded multi-round simulations to compare on organs transplanted, organs wasted, **wait-list deaths** (total and among high-acuity patients), median wait to transplant, and a life-years-saved proxy. `baseline` reproduces the project's original greedy/priority-only behavior, so every other strategy can be measured against it.

### <ins>Clinical Realism</ins>
`network_simulator.clinical` grounds the simulation in real-world data so "which strategy is best" is measured the way real allocation policy is judged - by lives saved, not just organ throughput:

- `frequencies` - US-population blood-type distribution, kidney-dominated wait-list organ demand, and per-organ donor recovery probabilities drive generation, replacing uniform sampling. A single seeded `weighted_choice` helper backs every weighted draw, so generation stays deterministic and testable.
- `hla` / `size` / `gates` - mechanistic feasibility gates: donors carry an HLA antigen set and patients their unacceptable antigens (crossmatch positive iff they intersect; cPRA emerges combinatorially from how broadly sensitized a patient is, so ~70% of generated patients are unsensitized and ~10% are highly sensitized), while heart/lung require donor/recipient size compatibility within an organ-specific tolerance. `GATES_BY_ORGAN` registers which gates apply to which organ, plugging into `feasibility.py` without disturbing the universal blood-type/viability checks.
- `urgency` / `mortality` / `progression` - each organ has a native urgency scale (MELD for liver, LAS for lung, status tiers 1-6 for heart; kidney has no acute scale since dialysis sustains candidates) normalized to a common **acuity** in `(0, 1]` via documented anchor points, so a single scorer can rank across organ types. Urgency worsens each round (`urgency.progress`), and acuity drives a per-round death probability via a constant-hazard survival model over a one-week round (`mortality.per_round_death_prob`), calibrated so a constant-severity cohort reproduces published mortality (e.g. liver MELD 90-day mortality ~4% / ~36% / ~84% across the ≤20 / 21-30 / 31-40 bands, kidney ~6%/yr) - verified directly by `tests/test_mortality.py`. `progression.simulate_round_progression` advances every waiting patient, rolls death, and removes and returns the dead each round; it's kept separate from `WaitList` (a pure collection) and from the matchers (a death is a third outcome, orthogonal to a match), so a caller - today, the benchmark's round loop - applies it explicitly once per round.

All of the above is deterministic under a single seeded `random.Random` per trial: the same seed reproduces the same network, arrivals, matches, and deaths, which is what lets the benchmark attribute differences in outcome to the *strategy* rather than to noise.

### <ins>Simulator</ins>
The `Simulator` (`execute/simulator.py`) is designed to create an interactive experience that can be executed through any console. The simulator does this by harnessing the functionality of the `GraphBuilder`, `PatientGenerator`, `OrganGenerator`, and `network_simulator.allocation` classes, including choosing which allocation strategy to use. This allows users to choose the number of nodes in the network, number of patients on the wait list, and number of bodies to harvest organs from all on the fly.

## Scripts

All scripts live under `execute/` and are run as `python execute/<script>.py` from the repository root.

**Interactive & benchmark**
- `simulator.py` - the interactive console simulator described above.
- `simulation.py` - a small non-interactive scripted demo: builds a hand-written hospital network, generates patients/organs, and runs one allocation pass end-to-end.
- `benchmark_strategies.py` - runs every strategy in `STRATEGIES` across many seeded multi-round simulations and prints the comparison table described in [Allocation Strategies](#allocation-strategies). Also importable (`run_trial`, `run_benchmark`) for custom comparisons.

**Real hospital network data pipeline**
- `import_hospitals.py` - builds a `Network` of real US transplant hospitals from `import/workbooks/National_Transplant_Hospitals_coordinates.xlsx`, with edge weights computed directly from coordinates via `network_simulator.distance` (no scraping).
- `get_coordinates.py` - a one-time utility that geocodes hospital city/state into latitude/longitude via the Bing Maps API, producing the coordinates workbook `import_hospitals.py` consumes. Only needed if the hospital roster is refreshed.
- `export_hospital_network.py` / `export_edgelist.py` - export a previously-built (shelve-serialized) network to GEXF or a plain edge-list file for use in external graph tools.
- `hospital_count.py` - tallies hospitals per US state/region from the source workbook.
- `generate_networks.py` - generates and serializes a batch of random networks (with their patient/organ populations) for reuse across scripts.

**Demo & utility scripts**
- `network_demo.py` - a minimal script exercising the core `Network`/`Node` API.
- `networkx_demo.py` - demonstrates converting a `Network` to `NetworkX` and drawing it with `matplotlib`.
- `subnetwork_demo.py` - demonstrates `SubnetworkGenerator` filtering a network down to only the nodes with active patients/organs.
- `make_tsv.py` - generates a random edge list in TSV format for external I/O.
- `import_edge_list.py` - converts an edge-list file back into a `Network`.
