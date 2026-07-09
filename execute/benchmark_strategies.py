"""
Compares allocation strategies (organflow.allocation.STRATEGIES)
over many randomized multi-round simulations. Each trial seeds one
random.Random that drives network topology and every round's patient/organ
arrivals identically across strategies, so only the allocation decision
varies - the comparison isolates matching-algorithm and scoring-model
effects rather than differences in who happened to show up.

Run directly: `python execute/benchmark_strategies.py`
"""
import os
import random
import statistics
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

from benchmark_stats import (
    bootstrap_ci,
    holm_bonferroni,
    paired_effect_size,
    paired_permutation_test,
)

from organflow.allocation import STRATEGIES, AllocationResult, Strategy
from organflow.clinical import acceptance
from organflow.clinical.living_donor import simulate_living_donor_transplants
from organflow.clinical.progression import simulate_round_progression
from organflow.clinical.removal import simulate_round_removals
from organflow.compatibility_markers import OrganType
from organflow.GraphBuilder import GraphBuilder
from organflow.Network import Network
from organflow.OrganGenerator import OrganGenerator
from organflow.OrganList import OrganList
from organflow.PatientGenerator import PatientGenerator
from organflow.WaitList import WaitList

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
    # non-transplant, non-death exits (too sick / improved / transferred / declined) and
    # living-donor transplants - the outflow channels that keep the real list near steady
    # state. Strategy-independent, tracked so the wait-list trajectory is realistic.
    other_removals: int = 0
    living_donor_transplants: int = 0
    # organs matched to a recipient but then declined/discarded (a subset of organs_wasted);
    # only nonzero when run_trial's realistic_outcomes is enabled - see clinical.acceptance
    organs_discarded: int = 0
    # pediatric candidates seen / transplanted / died - lets the benchmark measure whether the
    # pediatric priority in the policy scorers actually helps kids (see allocation.scoring)
    pediatric_seen: int = 0
    pediatric_transplanted: int = 0
    pediatric_deaths: int = 0
    deaths_by_organ: Dict[OrganType, int] = field(
            default_factory=lambda: {organ: 0 for organ in OrganType})
    wait_times_to_transplant: List[int] = field(default_factory=list)
    # transit hours for each transplanted organ (only populated under realistic_outcomes) -
    # the geographic-efficiency axis for the continuous-distribution frontier sweep
    transit_of_transplants: List[float] = field(default_factory=list)
    tier_seen: Dict[str, int] = field(default_factory=lambda: {t: 0 for t in PRIORITY_TIERS})
    tier_matched: Dict[str, int] = field(default_factory=lambda: {t: 0 for t in PRIORITY_TIERS})
    runtime_seconds: float = 0.0
    # (round number, wait list size at the end of that round) - only populated when run_trial's
    # snapshot_interval_rounds is set; this is what shows a growth/backlog *trajectory* rather
    # than just an end-of-run count.
    wait_list_size_snapshots: List[Tuple[int, int]] = field(default_factory=list)

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


@dataclass
class TrialConfig:
    """Per-round knobs for one trial, bundled so the round helpers take a short signature."""
    patients_per_round: int
    harvests_per_round: int
    patient_nodes: Optional[List[int]]
    organ_nodes: Optional[List[int]]
    other_removal_annual_rate: float
    living_donors_per_round: int
    realistic_outcomes: bool
    priority_range: int


def _record_allocation(result: AllocationResult, network: Network, wait_list: WaitList,
                       organ_list: OrganList, metrics: TrialMetrics, config: TrialConfig,
                       rng: random.Random) -> None:
    """
    Accrues transplant/discard/waste metrics for one allocation and removes the recipients who
    actually received an organ. With realistic_outcomes a matched organ may be declined
    (cold-ischemia-dependent) and discarded - counted as wasted, its patient kept waiting - and
    a transplanted organ's life-years are scaled by a cold-ischemia graft-survival penalty.
    """
    transplanted_patients = []
    for organ, patient in result.matches:
        transit_hours = 0.0
        if config.realistic_outcomes:
            transit_hours = network.transit_from(organ.origin_location)[patient.location]
            if acceptance.is_discarded(organ.organ_type, transit_hours, organ.donor_type, rng):
                # declined down the match run -> wasted; the patient keeps waiting
                metrics.organs_wasted += 1
                metrics.organs_discarded += 1
                continue

        life_years = LIFE_YEARS_BY_ORGAN[patient.organ_needed]
        if config.realistic_outcomes:
            life_years *= acceptance.graft_survival_factor(transit_hours, organ.donor_type)

        metrics.organs_transplanted += 1
        metrics.total_priority_served += patient.priority
        metrics.life_years_saved += life_years
        metrics.wait_times_to_transplant.append(patient.rounds_waited)
        metrics.transit_of_transplants.append(transit_hours)
        metrics.tier_matched[_priority_tier(patient.priority, config.priority_range)] += 1
        if patient.is_pediatric:
            metrics.pediatric_transplanted += 1
        transplanted_patients.append(patient)
    metrics.organs_wasted += len(result.unmatched_organs)

    if config.realistic_outcomes:
        # only the accepted recipients leave the list; discarded organs' patients stay
        for patient in transplanted_patients:
            wait_list.remove_patient(patient)
        organ_list.empty_list()
    else:
        result.apply(wait_list, organ_list)


def _record_outflows(wait_list: WaitList, metrics: TrialMetrics, config: TrialConfig,
                     rng: random.Random) -> None:
    """One round's non-allocation exits: deaths (with deterioration), then non-death removals,
    then living-donor transplants off the survivors."""
    for patient in simulate_round_progression(wait_list, rng):
        metrics.waitlist_deaths += 1
        metrics.deaths_by_organ[patient.organ_needed] += 1
        if patient.acuity >= HIGH_ACUITY_THRESHOLD:
            metrics.deaths_high_acuity += 1
        else:
            metrics.deaths_low_acuity += 1
        if patient.is_pediatric:
            metrics.pediatric_deaths += 1

    metrics.other_removals += len(
            simulate_round_removals(wait_list, config.other_removal_annual_rate, rng))
    metrics.living_donor_transplants += len(
            simulate_living_donor_transplants(wait_list, config.living_donors_per_round, rng))


def _simulate_round(strategy: Strategy, network: Network, wait_list: WaitList,
                    metrics: TrialMetrics, config: TrialConfig, rng: random.Random) -> None:
    """One round: generate arrivals, harvest and allocate organs, then deterioration/outflow.
    Mutates wait_list and metrics. Kept as three named steps so a round is testable and the
    rng draw order (arrivals -> organs -> allocation/discard -> deaths -> removals -> living)
    stays explicit and reproducible."""
    new_patients = PatientGenerator.generate_patients(
            network, config.patients_per_round, rng, eligible_nodes=config.patient_nodes)
    wait_list.add_patients(new_patients)
    for patient in new_patients:
        metrics.tier_seen[_priority_tier(patient.priority, config.priority_range)] += 1
        if patient.is_pediatric:
            metrics.pediatric_seen += 1

    organ_list = OrganList()
    OrganGenerator.generate_organs_to_list(
            network, config.harvests_per_round, organ_list, rng, eligible_nodes=config.organ_nodes)

    result = strategy.allocate(organ_list, wait_list, network)
    _record_allocation(result, network, wait_list, organ_list, metrics, config, rng)
    _record_outflows(wait_list, metrics, config, rng)
    wait_list.increment_wait_times()


def run_trial(seed: int, strategy: Strategy, num_nodes: int = 30, rounds: int = 10,
             patients_per_round: int = 15, harvests_per_round: int = 5,
             network: Optional[Network] = None, patient_nodes: Optional[List[int]] = None,
             organ_nodes: Optional[List[int]] = None,
             snapshot_interval_rounds: Optional[int] = None,
             other_removal_annual_rate: float = 0.0,
             living_donors_per_round: int = 0,
             realistic_outcomes: bool = False) -> TrialMetrics:
    """
    Runs one multi-round simulation for a single strategy: builds one
    network, then repeats (generate patients -> harvest organs -> allocate
    -> increment wait times on the remainder) for `rounds` rounds.

    :param int seed: seeds every round's arrivals (and network topology, if `network` isn't
        passed); reused identically across strategies within a benchmark trial
    :param Strategy strategy: the (matcher, scorer) pairing to evaluate
    :param int num_nodes: hospitals in the generated network - ignored if `network` is passed
    :param int rounds: number of arrival/allocation rounds to simulate
    :param int patients_per_round: new patients generated each round
    :param int harvests_per_round: bodies harvested for organs each round
    :param network: optional pre-built network (e.g. the real imported hospital network - see
        execute.import_hospitals) to use instead of building a synthetic one via GraphBuilder.
        Useful when the network itself doesn't change across seeds/strategies and shouldn't be
        rebuilt every trial.
    :param patient_nodes: optional node ids patients may be located at, forwarded to
        PatientGenerator as its `eligible_nodes` - e.g. real transplant-hospital nodes only
    :param organ_nodes: optional node ids organs may originate at, forwarded to OrganGenerator
        as its `eligible_nodes` - e.g. real transplant-hospital + OPO nodes
    :param snapshot_interval_rounds: if set, records (round number, wait list size) into
        TrialMetrics.wait_list_size_snapshots every time the round number is a multiple of this
        (e.g. 52 for a yearly snapshot) - shows a growth trajectory, not just an end-of-run count
    :param other_removal_annual_rate: annualized hazard of a non-death, non-transplant wait-list
        removal (too sick / improved / transferred / declined); 0 disables it (default, so the
        toy benchmark and tests are unaffected). The reality-calibrated scenario report enables it
        - see organflow.clinical.removal.
    :param living_donors_per_round: number of living-donor transplants per round, drawn off
        eligible kidney/liver waiters; 0 disables it (default) - see
        organflow.clinical.living_donor.
    :param realistic_outcomes: when True, each matched organ may be declined/discarded with a
        cold-ischemia-dependent probability (a matched-but-discarded organ counts as wasted and
        its patient stays on the list), and transplanted organs' life-years are scaled down by a
        cold-ischemia graft-survival penalty. Off by default (so the bare strategy comparison and
        tests are unaffected); the reality-calibrated scenario report enables it - see
        organflow.clinical.acceptance.
    :return: aggregate metrics for the trial
    """
    rng = random.Random(seed)
    if network is None:
        network = GraphBuilder.graph_builder(num_nodes, rng=rng)
    wait_list = WaitList()
    metrics = TrialMetrics()
    config = TrialConfig(
            patients_per_round=patients_per_round, harvests_per_round=harvests_per_round,
            patient_nodes=patient_nodes, organ_nodes=organ_nodes,
            other_removal_annual_rate=other_removal_annual_rate,
            living_donors_per_round=living_donors_per_round,
            realistic_outcomes=realistic_outcomes,
            priority_range=100 + patients_per_round)  # matches PatientGenerator's randrange(100+n)

    start = time.perf_counter()
    for round_number in range(1, rounds + 1):
        _simulate_round(strategy, network, wait_list, metrics, config, rng)

        if snapshot_interval_rounds and round_number % snapshot_interval_rounds == 0:
            metrics.wait_list_size_snapshots.append((round_number, len(wait_list.wait_list)))

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


def _aggregate_trials(name: str, trials: List[TrialMetrics]) -> AggregatedMetrics:
    """Collapses one strategy's per-seed trials into mean/stdev summary metrics."""
    transplanted = [t.organs_transplanted for t in trials]
    return AggregatedMetrics(
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
            runtime_mean=statistics.mean(t.runtime_seconds for t in trials))


def _run_all_trials(names: List[str], seeds: List[int], workers: int,
                    trial_kwargs: dict) -> Dict[str, List[TrialMetrics]]:
    """
    Runs every (strategy, seed) trial and returns them grouped by strategy in seed order.
    Trials are independent and fully seeded, so a parallel run is bit-for-bit identical to a
    sequential one - results are keyed by (name, seed) and reassembled in order, never by
    completion order. workers == 1 stays a plain sequential loop (no process-pool overhead).
    """
    if workers <= 1:
        return {name: [run_trial(seed, STRATEGIES[name], **trial_kwargs) for seed in seeds]
                for name in names}

    completed: Dict[Tuple[str, int], TrialMetrics] = {}
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(run_trial, seed, STRATEGIES[name], **trial_kwargs): (name, seed)
                   for name in names for seed in seeds}
        for future in as_completed(futures):
            completed[futures[future]] = future.result()
    return {name: [completed[(name, seed)] for seed in seeds] for name in names}


def run_benchmark(strategy_names: Optional[Iterable[str]] = None,
                  seeds: Iterable[int] = range(30), workers: int = 1, **trial_kwargs
                  ) -> Tuple[List[AggregatedMetrics], Dict[str, List[TrialMetrics]]]:
    """
    Runs run_trial() for every (strategy, seed) pair and aggregates the
    results per strategy. 30 seeds (up from an earlier 10) balances runtime
    against statistical power - see compare_to_reference/required_sample_size
    in benchmark_stats for sizing this deliberately rather than guessing.

    :param strategy_names: subset of STRATEGIES to compare (defaults to all)
    :param seeds: seeds to run each strategy over
    :param int workers: process-pool size for running trials in parallel (default 1 =
        sequential). Trials are independent and seeded, so any worker count yields identical
        results; use os.cpu_count() to parallelize the (embarrassingly parallel) sweep.
    :param trial_kwargs: forwarded to run_trial (num_nodes, rounds, etc.)
    :return: (per-strategy aggregated metrics, per-strategy per-seed raw trials -
        the latter is what compare_to_reference needs for paired comparisons,
        since aggregates alone can't be re-paired by seed)
    """
    names = list(strategy_names) if strategy_names is not None else list(STRATEGIES.keys())
    seeds = list(seeds)

    trials_by_strategy = _run_all_trials(names, seeds, workers, trial_kwargs)
    aggregated = [_aggregate_trials(name, trials_by_strategy[name]) for name in names]
    return aggregated, trials_by_strategy


def print_report(aggregated: List[AggregatedMetrics]) -> None:
    """
    Prints a plain text comparison table - no visualization, per scope. Leads
    with the life-and-death outcomes (deaths, high-acuity deaths) that
    distinguish allocation policies, not just organ throughput.
    """
    header = (f"{'strategy':<28}{'transplanted':>13}{'wasted':>8}{'deaths':>8}"
              f"{'hi-acuity deaths':>18}{'median wait':>13}{'life-years':>12}"
              f"{'runtime (s)':>13}")
    print(header)
    print('-' * len(header))
    for row in aggregated:
        print(f'{row.strategy_name:<28}{row.transplanted_mean:>13.1f}'
             f'{row.wasted_mean:>8.1f}{row.deaths_mean:>8.1f}'
             f'{row.deaths_high_acuity_mean:>18.1f}{row.median_wait_mean:>13.1f}'
             f'{row.life_years_mean:>12.1f}{row.runtime_mean:>13.4f}')


# The two outcomes the README already centers as the "lives saved" question - kept to just
# these two (rather than every metric) to avoid a combinatorial explosion of comparisons.
SIGNIFICANCE_METRICS = ('waitlist_deaths', 'life_years_saved')

# real_world_circle (strict adherence to the current distance-circle model - see
# organflow.allocation.geography) is the default significance reference: the
# question worth a corrected p-value is "does this beat what US policy actually does
# today," not "does this beat this project's original synthetic baseline."
DEFAULT_REFERENCE_STRATEGY = 'real_world_circle'


@dataclass
class SignificanceResult:
    """One strategy's paired comparison against the reference, for one metric."""
    strategy_name: str
    metric: str
    mean_diff: float
    ci_low: float
    ci_high: float
    effect_size: float
    p_value: float
    adjusted_p_value: float = 1.0

    def is_significant(self, alpha: float = 0.05) -> bool:
        return self.adjusted_p_value < alpha


def compare_to_reference(trials_by_strategy: Dict[str, List[TrialMetrics]],
                         reference: str = DEFAULT_REFERENCE_STRATEGY,
                         metrics: Iterable[str] = SIGNIFICANCE_METRICS,
                         num_resamples: int = 2000,
                         rng: Optional[random.Random] = None) -> List[SignificanceResult]:
    """
    Paired comparison of every other strategy in trials_by_strategy against `reference`,
    seed-for-seed (see run_trial's seed reuse - within one benchmark run, strategies see
    identical network/arrival/harvest seeds, so per-seed differences isolate the
    allocation decision). Holm-corrects p-values within each metric across all compared
    strategies (not across metrics, since those answer different questions).

    :param trials_by_strategy: per-strategy per-seed trials, as returned by run_benchmark
    :param reference: strategy name every other strategy is compared against
    :param metrics: TrialMetrics attribute names to compare
    :param num_resamples: forwarded to paired_permutation_test/bootstrap_ci
    :param rng: optional seeded source (defaults to a fresh random.Random per call)
    """
    if reference not in trials_by_strategy:
        raise ValueError(f'reference strategy {reference!r} not found in trials_by_strategy')

    source = rng or random.Random()
    reference_trials = trials_by_strategy[reference]
    results: List[SignificanceResult] = []

    for metric in metrics:
        reference_values = [getattr(trial, metric) for trial in reference_trials]
        raw_p_by_strategy: Dict[str, float] = {}
        pending: Dict[str, SignificanceResult] = {}

        for name, trials in trials_by_strategy.items():
            if name == reference:
                continue
            values = [getattr(trial, metric) for trial in trials]
            diffs = [value - ref for value, ref in zip(values, reference_values)]

            p_value = paired_permutation_test(diffs, num_resamples=num_resamples, rng=source)
            ci_low, ci_high = bootstrap_ci(diffs, num_resamples=num_resamples, rng=source)

            raw_p_by_strategy[name] = p_value
            pending[name] = SignificanceResult(
                    strategy_name=name, metric=metric, mean_diff=statistics.mean(diffs),
                    ci_low=ci_low, ci_high=ci_high, effect_size=paired_effect_size(diffs),
                    p_value=p_value)

        adjusted = holm_bonferroni(raw_p_by_strategy)
        for name, result in pending.items():
            result.adjusted_p_value = adjusted[name]
            results.append(result)

    return results


def print_significance_report(results: List[SignificanceResult], alpha: float = 0.05,
                              reference: str = DEFAULT_REFERENCE_STRATEGY) -> None:
    """Plain text table of compare_to_reference's output - no plots, per scope."""
    print(f"\nSignificance vs. '{reference}' (Holm-corrected within each metric, "
         f"alpha={alpha}):")
    header = (f"{'strategy':<28}{'metric':<18}{'mean diff':>11}{'95% CI':>20}"
              f"{'effect size':>13}{'adj. p':>9}  sig")
    print(header)
    print('-' * len(header))
    for row in results:
        ci = f'[{row.ci_low:.2f}, {row.ci_high:.2f}]'
        marker = '*' if row.is_significant(alpha) else ''
        print(f'{row.strategy_name:<28}{row.metric:<18}{row.mean_diff:>11.2f}{ci:>20}'
             f'{row.effect_size:>13.2f}{row.adjusted_p_value:>9.3f}  {marker}')


if __name__ == '__main__':
    report, trials_by_strategy = run_benchmark(seeds=range(30), num_nodes=30, rounds=12,
                                               patients_per_round=40, harvests_per_round=12,
                                               workers=os.cpu_count() or 1)
    print_report(report)

    significance = compare_to_reference(trials_by_strategy)
    print_significance_report(significance)
