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
from network_simulator.clinical.progression import simulate_round_progression
from network_simulator.compatibility_markers import OrganType
from network_simulator.GraphBuilder import GraphBuilder
from network_simulator.OrganGenerator import OrganGenerator
from network_simulator.OrganList import OrganList
from network_simulator.PatientGenerator import PatientGenerator
from network_simulator.WaitList import WaitList

PRIORITY_TIERS = ('low', 'medium', 'high')

# Acuity at/above which a wait-list death is counted as a "high-acuity" death -
# a patient who was dying and whom the strategy failed to transplant in time.
HIGH_ACUITY_THRESHOLD = 0.5

# Rough expected post-transplant life-years by organ (documented approximation,
# used only as a relative "benefit served" proxy - not a survival model).
LIFE_YEARS_BY_ORGAN: Dict[OrganType, float] = {
    OrganType.Kidney:     12.0,
    OrganType.Liver:      11.0,
    OrganType.Heart:      11.0,
    OrganType.Lungs:      6.0,
    OrganType.Pancreas:   10.0,
    OrganType.Intestines: 7.0,
}


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
    life_years_saved: float = 0.0
    waitlist_deaths: int = 0
    deaths_high_acuity: int = 0
    deaths_low_acuity: int = 0
    deaths_by_organ: Dict[OrganType, int] = field(
            default_factory=lambda: {organ: 0 for organ in OrganType})
    wait_times_to_transplant: List[int] = field(default_factory=list)
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

    def median_wait(self) -> float:
        """Median rounds waited before transplant (0.0 if nobody was transplanted)."""
        return statistics.median(self.wait_times_to_transplant) \
            if self.wait_times_to_transplant else 0.0


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
            metrics.life_years_saved += LIFE_YEARS_BY_ORGAN[patient.organ_needed]
            metrics.wait_times_to_transplant.append(patient.rounds_waited)
            metrics.tier_matched[_priority_tier(patient.priority, priority_range)] += 1
        metrics.organs_wasted += len(result.unmatched_organs)

        result.apply(wait_list, organ_list)

        # patients still waiting deteriorate and some die before a match arrives
        for patient in simulate_round_progression(wait_list, rng):
            metrics.waitlist_deaths += 1
            metrics.deaths_by_organ[patient.organ_needed] += 1
            if patient.acuity >= HIGH_ACUITY_THRESHOLD:
                metrics.deaths_high_acuity += 1
            else:
                metrics.deaths_low_acuity += 1

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
    deaths_mean: float
    deaths_high_acuity_mean: float
    median_wait_mean: float
    life_years_mean: float
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
                deaths_mean=statistics.mean(t.waitlist_deaths for t in trials),
                deaths_high_acuity_mean=statistics.mean(t.deaths_high_acuity for t in trials),
                median_wait_mean=statistics.mean(t.median_wait() for t in trials),
                life_years_mean=statistics.mean(t.life_years_saved for t in trials),
                priority_served_mean=statistics.mean(t.total_priority_served for t in trials),
                fairness_spread_mean=statistics.mean(t.fairness_spread() for t in trials),
                runtime_mean=statistics.mean(t.runtime_seconds for t in trials)))

    return aggregated


def print_report(aggregated: List[AggregatedMetrics]) -> None:
    """
    Prints a plain text comparison table - no visualization, per scope. Leads
    with the life-and-death outcomes (deaths, high-acuity deaths) that
    distinguish allocation policies, not just organ throughput.
    """
    header = (f"{'strategy':<20}{'transplanted':>13}{'wasted':>8}{'deaths':>8}"
              f"{'hi-acuity deaths':>18}{'median wait':>13}{'life-years':>12}"
              f"{'runtime (s)':>13}")
    print(header)
    print('-' * len(header))
    for row in aggregated:
        print(f'{row.strategy_name:<20}{row.transplanted_mean:>13.1f}'
             f'{row.wasted_mean:>8.1f}{row.deaths_mean:>8.1f}'
             f'{row.deaths_high_acuity_mean:>18.1f}{row.median_wait_mean:>13.1f}'
             f'{row.life_years_mean:>12.1f}{row.runtime_mean:>13.4f}')


if __name__ == '__main__':
    report = run_benchmark(seeds=range(10), num_nodes=30, rounds=12,
                           patients_per_round=40, harvests_per_round=12)
    print_report(report)
