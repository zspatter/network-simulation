"""
Named strategies compared by the benchmark harness (see
execute/benchmark_strategies.py) and selectable from the interactive
simulator. Each strategy pairs a MatchingAlgorithm (how matches are chosen)
with a ScoringFunction (how a match is valued) - the two axes are
orthogonal, so the benchmark can attribute a strategy's outcome to the
matching algorithm, the scoring model, or both.
"""
from __future__ import annotations

from dataclasses import dataclass

from network_simulator.allocation.base import AllocationResult, MatchingAlgorithm, ScoringFunction
from network_simulator.allocation.geography import circle_tier, region_tier
from network_simulator.allocation.matchers.greedy import GreedyMatcher
from network_simulator.allocation.matchers.optimal import OptimalMatcher
from network_simulator.allocation.matchers.tiered import TieredMatcher
from network_simulator.allocation.scoring import (
    AcuityScore,
    CompositeScore,
    PriorityScore,
    RealWorldScore,
    ScoreWeights,
)
from network_simulator.Network import Network
from network_simulator.OrganList import OrganList
from network_simulator.WaitList import WaitList

# Composite weighting that leans on acuity (0..1, scaled up to compete with the
# raw wait-time term) rather than the synthetic priority int - a
# clinically-oriented blend of near-term risk, waiting time, and travel cost.
_ACUITY_COMPOSITE_WEIGHTS = ScoreWeights(urgency=0.0, acuity=100.0,
                                         wait_time=2.0, geography=-0.5)


@dataclass
class Strategy:
    """A named (matcher, scorer) pairing that can be run as a single allocation call."""
    name: str
    matcher: MatchingAlgorithm
    scorer: ScoringFunction

    def allocate(self, organ_list: OrganList, wait_list: WaitList,
                network: Network) -> AllocationResult:
        return self.matcher.allocate(organ_list, wait_list, network, self.scorer)


# baseline: today's original allocation behavior (greedy, priority-only)
# optimal_priority: isolates the matching-algorithm effect (same scorer as baseline)
# optimal_composite: isolates the scoring-model effect on top of optimal matching
# greedy_composite: isolates the scoring-model effect on top of greedy matching
# optimal_acuity: "sickest first" - ranks by near-term death risk (the
#     life-saving policy the pre-clinical model couldn't express)
# composite_acuity: acuity + waiting time + geography combined, optimally matched
#
# real_world_* / optimal_real_world_circle: RealWorldScore held fixed across all four,
# varying only the geographic constraint - see allocation.geography and
# allocation.matchers.tiered for the real-policy sourcing behind each:
#   real_world_region: strict adherence to the legacy arbitrary Region/DSA model
#       (removed from real policy 2018-2021, but a real prior baseline to measure against)
#   real_world_circle: strict adherence to the current distance-circle model
#       (still current for kidney, pancreas, and heart)
#   real_world_unconstrained: adherence broken entirely - geography only enters as
#       RealWorldScore's soft efficiency term, approximating where continuous
#       distribution (already live for lung) is headed for the rest
#   optimal_real_world_circle: same constraint as real_world_circle, optimal matching -
#       isolates how much of the real (greedy, sequential-offer) system's outcome is
#       attributable to its match algorithm vs. its geographic constraint
STRATEGIES = {
    'baseline':          Strategy('baseline', GreedyMatcher(), PriorityScore()),
    'optimal_priority':  Strategy('optimal_priority', OptimalMatcher(), PriorityScore()),
    'optimal_composite': Strategy('optimal_composite', OptimalMatcher(), CompositeScore()),
    'greedy_composite':  Strategy('greedy_composite', GreedyMatcher(), CompositeScore()),
    'optimal_acuity':    Strategy('optimal_acuity', OptimalMatcher(), AcuityScore()),
    'composite_acuity':  Strategy('composite_acuity', OptimalMatcher(),
                                  CompositeScore(weights=_ACUITY_COMPOSITE_WEIGHTS)),
    'real_world_region': Strategy('real_world_region',
                                  TieredMatcher(GreedyMatcher(), region_tier), RealWorldScore()),
    'real_world_circle': Strategy('real_world_circle',
                                  TieredMatcher(GreedyMatcher(), circle_tier), RealWorldScore()),
    'real_world_unconstrained': Strategy('real_world_unconstrained',
                                         GreedyMatcher(), RealWorldScore()),
    'optimal_real_world_circle': Strategy('optimal_real_world_circle',
                                          TieredMatcher(OptimalMatcher(), circle_tier),
                                          RealWorldScore()),
}
