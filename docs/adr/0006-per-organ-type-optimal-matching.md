# ADR-0006: Optimal matching is per-organ-type LAP (scipy), not one global graph match

**Date**: 2026-07-08 · **Status**: Accepted

## Context

`OptimalMatcher` finds the maximum-weight matching for an allocation batch so an early low-value
match can't crowd out a better later one. The original implementation used networkx's
general-graph `max_weight_matching` over every organ at once. On a real national-scale backlog
(tens of thousands of kidney candidates) that both took minutes and could crash outright.

## Decision

Solve **one `scipy.optimize.linear_sum_assignment` (Hungarian/Jonker-Volgenant) per organ type**.
Organ types never share candidates (a patient needs one organ type), so the global bipartite
graph decomposes into independent per-type components anyway - solving them separately is exact,
not an approximation. scipy's LAP solver is specialized for exactly this rectangular assignment
problem.

## Consequences

- Handles a several-hundred × tens-of-thousands matrix in well under a second (vs. minutes /
  crashes), which is what makes national-scale scenario reports feasible.
- Adds a `scipy` dependency - justified by the scale requirement.
- A property test asserts the optimal total score is never below the greedy heuristic's, guarding
  the optimality claim.
