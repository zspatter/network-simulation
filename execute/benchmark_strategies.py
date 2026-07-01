"""
Compares allocation strategies (network_simulator.allocation.STRATEGIES)
over many randomized multi-round simulations. Each trial seeds one
random.Random that drives network topology and every round's patient/organ
arrivals identically across strategies, so only the allocation decision
varies - the comparison isolates matching-algorithm and scoring-model
effects rather than differences in who happened to show up.

Run directly: `python execute/benchmark_strategies.py`
"""
import random
import statistics
import time
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from network_simulator.allocation import STRATEGIES, Strategy
from network_simulator.GraphBuilder import GraphBuilder
from network_simulator.OrganGenerator import OrganGenerator
from network_simulator.OrganList import OrganList
from network_simulator.PatientGenerator import PatientGenerator
from network_simulator.WaitList import WaitList

PRIORITY_TIERS = ('low', 'medium', 'high')


def _priority_tier(priority: int, priority_range: int) -> str:
    """
    Buckets a priority value into thirds of the range PatientGenerator can
    actually produce (randrange(100 + patients_per_round)) - fixed absolute
    thresholds would silently leave the top tier empty for the harness's
    default round sizes, since priority is generated relative to batch size,
    not on a fixed universal scale.
    """
    third = priority_range / 3
    if priority < third:
        return 'low'
    if priority < 2 * third:
        return 'medium'
    return 'high'


@dataclass
class TrialMetrics:
    """Outcome of one multi-round simulation for a single strategy."""
    organs_transplanted: int = 0
    organs_wasted: int = 0
    total_priority_served: float = 0.0
    tier_seen: Dict[str, int] = field(default_factory=lambda: {t: 0 for t in PRIORITY_TIERS})
    tier_matched: Dict[str, int] = field(default_factory=lambda: {t: 0 for t in PRIORITY_TIERS})
    runtime_seconds: float = 0.0

    def tier_match_rates(self) -> Dict[str, float]:
        return {t: (self.tier_matched[t] / self.tier_seen[t] if self.tier_seen[t] else 0.0)
               for t in PRIORITY_TIERS}

    def fairness_spread(self) -> float:
        """max - min match rate across priority tiers; lower is more even/fair."""
        rates = list(self.tier_match_rates().values())
        return max(rates) - min(rates) if rates else 0.0


def run_trial(seed: int, strategy: Strategy, num_nodes: int = 30, rounds: int = 10,
             patients_per_round: int = 15, harvests_per_round: int = 5) -> TrialMetrics:
    """
    Runs one multi-round simulation for a single strategy: builds one
    network, then repeats (generate patients -> harvest organs -> allocate
    -> increment wait times on the remainder) for `rounds` rounds.

    :param int seed: seeds the network topology and every round's arrivals;
        reused identically across strategies within a benchmark trial
    :param Strategy strategy: the (matcher, scorer) pairing to evaluate
    :param int num_nodes: hospitals in the generated network
    :param int rounds: number of arrival/allocation rounds to simulate
    :param int patients_per_round: new patients generated each round
    :param int harvests_per_round: bodies harvested for organs each round
    :return: aggregate metrics for the trial
    """
    rng = random.Random(seed)
    network = GraphBuilder.graph_builder(num_nodes, rng=rng)
    wait_list = WaitList()
    metrics = TrialMetrics()
    priority_range = 100 + patients_per_round  # matches PatientGenerator's randrange(100 + n)

    start = time.perf_counter()
    for _ in range(rounds):
        new_patients = PatientGenerator.generate_patients(network, patients_per_round, rng)
        wait_list.add_patients(new_patients)
        for patient in new_patients:
            metrics.tier_seen[_priority_tier(patient.priority, priority_range)] += 1

        organ_list = OrganList()
        OrganGenerator.generate_organs_to_list(network, harvests_per_round, organ_list, rng)

        result = strategy.allocate(organ_list, wait_list, network)
        for organ, patient in result.matches:
            metrics.organs_transplanted += 1
            metrics.total_priority_served += patient.priority
            metrics.tier_matched[_priority_tier(patient.priority, priority_range)] += 1
        metrics.organs_wasted += len(result.unmatched_organs)

        result.apply(wait_list, organ_list)
        wait_list.increment_wait_times()

    metrics.runtime_seconds = time.perf_counter() - start
    return metrics


@dataclass
class AggregatedMetrics:
    """Mean/stdev of TrialMetrics across every seed for one strategy."""
    strategy_name: str
    transplanted_mean: float
    transplanted_stdev: float
    wasted_mean: float
    priority_served_mean: float
    fairness_spread_mean: float
    runtime_mean: float


def run_benchmark(strategy_names: Optional[Iterable[str]] = None,
                  seeds: Iterable[int] = range(10), **trial_kwargs) -> List[AggregatedMetrics]:
    """
    Runs run_trial() for every (strategy, seed) pair and aggregates the
    results per strategy.

    :param strategy_names: subset of STRATEGIES to compare (defaults to all)
    :param seeds: seeds to run each strategy over
    :param trial_kwargs: forwarded to run_trial (num_nodes, rounds, etc.)
    """
    names = list(strategy_names) if strategy_names is not None else list(STRATEGIES.keys())
    aggregated = []

    for name in names:
        strategy = STRATEGIES[name]
        trials = [run_trial(seed, strategy, **trial_kwargs) for seed in seeds]

        transplanted = [t.organs_transplanted for t in trials]
        aggregated.append(AggregatedMetrics(
                strategy_name=name,
                transplanted_mean=statistics.mean(transplanted),
                transplanted_stdev=statistics.stdev(transplanted) if len(transplanted) > 1 else 0.0,
                wasted_mean=statistics.mean(t.organs_wasted for t in trials),
                priority_served_mean=statistics.mean(t.total_priority_served for t in trials),
                fairness_spread_mean=statistics.mean(t.fairness_spread() for t in trials),
                runtime_mean=statistics.mean(t.runtime_seconds for t in trials)))

    return aggregated


def print_report(aggregated: List[AggregatedMetrics]) -> None:
    """Prints a plain text comparison table - no visualization, per scope."""
    columns = ('strategy', 'transplanted', '+/-', 'wasted', 'priority served',
              'fairness spread', 'runtime (s)')
    header = f'{columns[0]:<20}{columns[1]:>13}{columns[2]:>7}{columns[3]:>9}' \
             f'{columns[4]:>17}{columns[5]:>17}{columns[6]:>13}'
    print(header)
    print('-' * len(header))
    for row in aggregated:
        print(f'{row.strategy_name:<20}{row.transplanted_mean:>13.1f}'
             f'{row.transplanted_stdev:>7.1f}{row.wasted_mean:>9.1f}'
             f'{row.priority_served_mean:>17.1f}{row.fairness_spread_mean:>17.3f}'
             f'{row.runtime_mean:>13.4f}')


if __name__ == '__main__':
    report = run_benchmark(seeds=range(10), num_nodes=30, rounds=10,
                           patients_per_round=15, harvests_per_round=5)
    print_report(report)
