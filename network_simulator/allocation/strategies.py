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
from network_simulator.allocation.matchers.greedy import GreedyMatcher
from network_simulator.allocation.matchers.optimal import OptimalMatcher
from network_simulator.allocation.scoring import (
    AcuityScore,
    CompositeScore,
    PriorityScore,
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
STRATEGIES = {
    'baseline':          Strategy('baseline', GreedyMatcher(), PriorityScore()),
    'optimal_priority':  Strategy('optimal_priority', OptimalMatcher(), PriorityScore()),
    'optimal_composite': Strategy('optimal_composite', OptimalMatcher(), CompositeScore()),
    'greedy_composite':  Strategy('greedy_composite', GreedyMatcher(), CompositeScore()),
    'optimal_acuity':    Strategy('optimal_acuity', OptimalMatcher(), AcuityScore()),
    'composite_acuity':  Strategy('composite_acuity', OptimalMatcher(),
                                  CompositeScore(weights=_ACUITY_COMPOSITE_WEIGHTS)),
}
