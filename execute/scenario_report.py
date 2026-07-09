"""
Generates shareable snapshot reports comparing allocation strategies over multi-year horizons,
at realistic national scale, on the real US transplant-hospital network - not a statistical
hypothesis test (see benchmark_strategies.py for that), but an illustrative "what does this
strategy actually buy us" comparison meant to be regenerated as the underlying data/strategies
change.

Run directly: `python execute/scenario_report.py`
"""
import argparse
import csv
import os
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

from benchmark_stats import min_achievable_p, seeds_for_significance
from benchmark_strategies import (
    AggregatedMetrics,
    SignificanceResult,
    TrialMetrics,
    compare_to_reference,
    run_benchmark,
)
from import_hospitals import filter_physical_locations, import_nodes, read_membership_csv

from network_simulator.allocation import STRATEGIES
from network_simulator.clinical.removal import OTHER_REMOVAL_ANNUAL_RATE
from network_simulator.Network import Network

# ---- Real-world calibration (OPTN/SRTR 2024 data - see README for full sourcing) ----
# 70,600 new waitlist additions across all organs in 2024 -> per week. PatientGenerator already
# splits this across organs via clinical.frequencies' real kidney-dominant weights.
NATIONAL_WEEKLY_NEW_PATIENTS = round(70_600 / 52)
# 16,989 deceased donors in 2024 -> per week. OrganGenerator already splits organ recovery via
# clinical.frequencies.DONOR_RECOVERY_PROBABILITIES.
NATIONAL_WEEKLY_DECEASED_DONORS = round(16_989 / 52)
# ~7,000 living-donor transplants/year (overwhelmingly kidney) -> per week. A wait-list outflow
# the deceased-donor pipeline never captures - see network_simulator.clinical.living_donor.
NATIONAL_WEEKLY_LIVING_DONORS = round(7_000 / 52)
ROUNDS_PER_YEAR = 52  # one round = 7 days (clinical.mortality.ROUND_DURATION_DAYS)

# Full national scale (--scale 1.0) is real but expensive: a single real_world_circle/1-year/
# 1-seed trial measured 850s, because feasibility checking is O(organs x wait-list size) per
# round and the wait list backlog itself grows into the tens of thousands over a year (a real,
# not synthetic, effect - see the trajectory table). Default to a documented fraction of
# national volume so the default invocation is practical; --scale 1.0 opts into the literal
# national figures for whoever wants to spend the compute.
DEFAULT_SCALE = 0.1


def scaled_weekly_rates(scale: float) -> Tuple[int, int, int]:
    """
    :param float scale: fraction of real national weekly volume (1.0 == literal national figures)
    :return: (patients_per_round, harvests_per_round, living_donors_per_round) at that scale
    """
    return (round(NATIONAL_WEEKLY_NEW_PATIENTS * scale),
           round(NATIONAL_WEEKLY_DECEASED_DONORS * scale),
           round(NATIONAL_WEEKLY_LIVING_DONORS * scale))

DEFAULT_MEMBERSHIP_CSV = (Path(__file__).parent / 'import' / 'optn_membership'
                          / 'optn_membership_2026-07-02.csv')

# Real historical OPTN region adjacency (see import_hospitals.py's module docstring) - forwarded
# to the distance-vector edge-generation logic, unchanged from that script.
NEIGHBOR_REGIONS = {1: [9], 2: [9, 10, 11], 3: [4, 8, 11], 4: [3, 5, 8], 5: [4, 6, 8],
                    6: [5, 7, 8], 7: [6, 8, 10], 8: [3, 4, 5, 6, 7], 9: [1, 2], 10: [2, 7, 11],
                    11: [2, 3, 10]}

DEFAULT_REFERENCE_STRATEGY = 'real_world_circle'


@dataclass
class StrategyTier:
    """One strategy in the curated roster, with a plain-language rationale for its tier."""
    name: str
    label: str
    description: str


# The confirmed 4-tier delta: real_world_circle (today's policy) held fixed as the reference,
# then increasingly ambitious changes, each annotated with how hard it would be to actually
# implement - not just how well it scores.
CURATED_STRATEGIES: List[StrategyTier] = [
    StrategyTier(
            'real_world_circle', 'Current policy',
            'Strict adherence to the current distance-circle model (what kidney, pancreas, and '
            'heart allocation actually do today): greedy, sequential-offer matching.'),
    StrategyTier(
            'optimal_real_world_circle', 'Easy win',
            'Identical policy scoring, but a computed global-optimum match instead of '
            'sequential greedy offers - a backend algorithm change, not a policy fight.'),
    StrategyTier(
            'real_world_unconstrained', 'Medium lift',
            'Same scoring, geographic constraint dropped entirely - mirrors where continuous '
            'distribution (already live for lung) is headed for the other organs.'),
    StrategyTier(
            'composite_acuity', 'Theoretical ceiling',
            'Acuity, wait time, and geography combined, optimally matched - maximizes lives '
            'saved but reshapes prioritization philosophy, the hardest lift politically.'),
]


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--horizon-years', default='1,5,10',
                        help='Comma-separated simulated-year horizons (default: 1,5,10)')
    parser.add_argument('--strategies', default='curated',
                        help="'curated' (default, the 4-tier delta), 'all' (every strategy in "
                             "network_simulator.allocation.STRATEGIES), or an explicit "
                             "comma-separated list of strategy names")
    parser.add_argument('--seeds', type=int, default=None,
                        help='Seeds per horizon (default: 8 for the 1-year horizon, 3 for '
                             'longer ones - runtime compounds with horizon length; note the '
                             'significance test needs >=7 seeds to be able to reach p<0.05 '
                             'at all, so low seed counts get a descriptive-only significance '
                             'table)')
    parser.add_argument('--scale', type=float, default=DEFAULT_SCALE,
                        help='Fraction of real national weekly arrival/donor volume to '
                             f'simulate (default: {DEFAULT_SCALE}). 1.0 = literal national '
                             'figures (~1358 patients/week, ~327 donors/week) - real but slow: '
                             'a single 1-year/1-seed trial measured ~850s per strategy.')
    parser.add_argument('--formats', default='markdown,csv',
                        help='Comma-separated output formats: markdown, csv, pdf (pdf needs '
                             'the optional reportlab dependency; default: markdown,csv)')
    parser.add_argument('--workers', type=int, default=os.cpu_count() or 1,
                        help='Parallel worker processes for the (independent, seeded) trials '
                             '(default: all CPU cores). 1 forces a sequential run.')
    parser.add_argument('--output-dir', default=None,
                        help='Output directory (default: reports/<timestamp>/)')
    parser.add_argument('--membership-csv', default=str(DEFAULT_MEMBERSHIP_CSV),
                        help='Path to the OPTN membership CSV (default: the bundled snapshot)')
    return parser.parse_args(argv)


def resolve_strategy_names(spec: str) -> List[str]:
    """
    :param str spec: 'curated', 'all', or a comma-separated list of STRATEGIES keys
    :return: the resolved list of strategy names
    :raises ValueError: if spec names a strategy that doesn't exist
    """
    if spec == 'curated':
        return [tier.name for tier in CURATED_STRATEGIES]
    if spec == 'all':
        return list(STRATEGIES.keys())

    names = [name.strip() for name in spec.split(',')]
    unknown = [name for name in names if name not in STRATEGIES]
    if unknown:
        raise ValueError(f'Unknown strategy name(s): {unknown}. '
                         f'Available: {sorted(STRATEGIES.keys())}')
    return names


def default_seeds_for_horizon(years: int) -> int:
    """
    Fewer seeds for longer horizons, since per-trial runtime compounds with horizon length.

    The 1-year default is 8 because the sign-flip permutation test's p-value floor is
    2/2^n: at the old default of 5 seeds, Holm-corrected significance at 0.05 was
    mathematically unattainable no matter how large the true effect (see
    benchmark_stats.seeds_for_significance - 7 is the minimum for 3 comparisons). Longer
    horizons keep a cheap 3-seed default for the descriptive tables; the report annotates
    their significance section as unattainable rather than presenting it as a negative
    finding.
    """
    return 8 if years == 1 else 3


def build_network(membership_csv_path: str) -> Tuple[Network, Set[int], Set[int]]:
    """Builds the real network via import_hospitals' pipeline - see that module's docstring."""
    rows = filter_physical_locations(read_membership_csv(membership_csv_path))
    return import_nodes(rows, NEIGHBOR_REGIONS)


@dataclass
class HorizonResult:
    """Everything generated for one simulated-year horizon."""
    years: int
    seeds: int
    aggregated: List[AggregatedMetrics]
    trials_by_strategy: Dict[str, List[TrialMetrics]] = field(default_factory=dict)
    significance: List[SignificanceResult] = field(default_factory=list)


def run_horizon(years: int, strategy_names: List[str], seeds: int, network: Network,
                patient_nodes: List[int], organ_nodes: List[int], patients_per_round: int,
                harvests_per_round: int, living_donors_per_round: int = 0,
                other_removal_annual_rate: float = OTHER_REMOVAL_ANNUAL_RATE,
                workers: int = 1) -> HorizonResult:
    """
    Runs every strategy in strategy_names over `years` simulated years (rounds = years * 52),
    on the given real network. Arrival/donor rates are the caller's responsibility (see
    scaled_weekly_rates()) rather than hardcoded here, so this stays cheap to call with a small
    rate in tests instead of paying national-scale cost for a two-node sanity check.

    The non-transplant outflow channels (living-donor transplants, non-death removals) are
    enabled here, since this is the reality-calibrated path - unlike the bare strategy benchmark,
    which leaves them off to isolate the allocation decision.
    """
    rounds = years * ROUNDS_PER_YEAR
    aggregated, trials_by_strategy = run_benchmark(
            strategy_names=strategy_names, seeds=range(seeds), rounds=rounds,
            patients_per_round=patients_per_round, harvests_per_round=harvests_per_round,
            network=network, patient_nodes=patient_nodes, organ_nodes=organ_nodes,
            snapshot_interval_rounds=ROUNDS_PER_YEAR,
            living_donors_per_round=living_donors_per_round,
            other_removal_annual_rate=other_removal_annual_rate,
            realistic_outcomes=True, workers=workers)

    significance: List[SignificanceResult] = []
    if seeds >= 2 and DEFAULT_REFERENCE_STRATEGY in trials_by_strategy:
        significance = compare_to_reference(trials_by_strategy,
                                            reference=DEFAULT_REFERENCE_STRATEGY)

    return HorizonResult(years=years, seeds=seeds, aggregated=aggregated,
                         trials_by_strategy=trials_by_strategy, significance=significance)


def _final_wait_list_size_mean(trials: List[TrialMetrics]) -> float:
    """Mean of each trial's last wait_list_size_snapshots entry - the end-of-horizon backlog."""
    finals = [trial.wait_list_size_snapshots[-1][1] for trial in trials
             if trial.wait_list_size_snapshots]
    return statistics.mean(finals) if finals else 0.0


def _summary_rows(result: HorizonResult) -> List[List[str]]:
    """Human-readable summary table rows (markdown/PDF): thousands separators throughout.
    summary.csv formats its own raw values - separators inside numbers aren't CSV-safe."""
    rows: List[List[str]] = []
    for row in result.aggregated:
        final_size = _final_wait_list_size_mean(result.trials_by_strategy[row.strategy_name])
        rows.append([row.strategy_name, f'{row.transplanted_mean:,.0f}',
                    f'{row.wasted_mean:,.0f}', f'{row.deaths_mean:,.0f}',
                    f'{row.deaths_high_acuity_mean:,.0f}', f'{row.median_wait_mean:.1f}',
                    f'{row.life_years_mean:,.0f}', f'{final_size:,.0f}'])
    return rows


def _trajectory_rows(trials_by_strategy: Dict[str, List[TrialMetrics]],
                     thousands_separators: bool = True) -> List[List[str]]:
    """One row per (strategy, year), averaging wait-list size across seeds at that year mark.

    :param bool thousands_separators: True for the human-readable markdown/PDF tables;
        trajectory.csv passes False, since separators inside numbers aren't CSV-safe
    """
    size_format = ',.0f' if thousands_separators else '.0f'
    rows: List[List[str]] = []
    for name, trials in trials_by_strategy.items():
        sizes_by_round: Dict[int, List[int]] = {}
        for trial in trials:
            for round_number, size in trial.wait_list_size_snapshots:
                sizes_by_round.setdefault(round_number, []).append(size)
        for round_number in sorted(sizes_by_round):
            year = round_number // ROUNDS_PER_YEAR
            rows.append([name, str(year),
                        format(statistics.mean(sizes_by_round[round_number]), size_format)])
    return rows


def _significance_rows(results: List[SignificanceResult]) -> List[List[str]]:
    return [[r.strategy_name, r.metric, f'{r.mean_diff:,.2f}',
            f'[{r.ci_low:,.2f}, {r.ci_high:,.2f}]', f'{r.effect_size:.2f}',
            f'{r.adjusted_p_value:.3f}', 'yes' if r.is_significant() else 'no']
           for r in results]


def _significance_floor_note(seeds: int, results: List[SignificanceResult],
                             alpha: float = 0.05) -> Optional[str]:
    """
    A plain-language warning when significance is mathematically unattainable: the
    sign-flip permutation test's p-value floor is 2/2^seeds, and Holm correction
    multiplies the best-ranked comparison by the comparison count - so at low seed counts
    every row is guaranteed non-significant regardless of how large the true effect is
    (an early report presented exactly that as a negative finding).

    :return: the warning string, or None when `seeds` gives the test a real chance
    """
    comparisons = len({r.strategy_name for r in results})
    if comparisons == 0:
        return None
    floor = min(1.0, min_achievable_p(seeds) * comparisons)
    if floor <= alpha:
        return None
    return (f'**Note**: with {seeds} seeds and {comparisons} comparisons, the smallest '
            f'Holm-adjusted p-value this test can produce is {floor:.3f} - significance at '
            f'{alpha} is mathematically unattainable at this seed count, so "no significant '
            f'result" here is a property of the sample size, not evidence about the '
            f'strategies. Rerun with `--seeds {seeds_for_significance(alpha, comparisons)}` '
            f'or more to give the test a real chance; until then, read the confidence '
            f'intervals and effect sizes as the primary evidence.')


def _markdown_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    lines = ['| ' + ' | '.join(headers) + ' |',
            '| ' + ' | '.join('---' for _ in headers) + ' |']
    lines.extend('| ' + ' | '.join(str(cell) for cell in row) + ' |' for row in rows)
    return '\n'.join(lines)


def _strategy_tier_lookup(strategy_names: Sequence[str]) -> List[StrategyTier]:
    """Tiers present in strategy_names, in CURATED_STRATEGIES' narrative order - not whatever
    (e.g. alphabetical) order strategy_names happens to be in."""
    present = set(strategy_names)
    return [tier for tier in CURATED_STRATEGIES if tier.name in present]


def _methodology_section(network_node_count: int, transplant_hospital_count: int,
                         opo_count: int, strategy_names: Sequence[str],
                         seeds_by_horizon: Dict[int, int], scale: float,
                         patients_per_round: int, harvests_per_round: int) -> str:
    tiers = _strategy_tier_lookup(strategy_names)
    strategy_lines = '\n'.join(f'- **{tier.label}** (`{tier.name}`): {tier.description}'
                              for tier in tiers)
    other_names = [name for name in strategy_names
                  if name not in {tier.name for tier in tiers}]
    if other_names:
        strategy_lines += '\n' + '\n'.join(f'- `{name}`' for name in other_names)
    horizon_lines = '\n'.join(f'- {years}-year horizon: {seeds} seed(s)'
                             for years, seeds in sorted(seeds_by_horizon.items()))
    scale_note = ('literal national figures' if scale == 1.0
                 else f'{scale:.0%} of real national volume - absolute counts below scale '
                      'accordingly; relative comparisons between strategies still hold')

    return (
        '## Methodology\n\n'
        f'- **Network**: {network_node_count} real nodes from the OPTN membership directory '
        f'(`hrsa.gov/optn/about/membership/optn-membership-database`) - '
        f'{transplant_hospital_count} transplant hospitals, {opo_count} Organ Procurement '
        'Organizations - geocoded via the US Census Bureau geocoder (Nominatim fallback for '
        'addresses Census could not match). See `execute/import_hospitals.py`.\n'
        f'- **Arrival calibration** (OPTN/SRTR 2024, real national rates: '
        f'{NATIONAL_WEEKLY_NEW_PATIENTS:,} new patients/week from 70,600/year across all '
        f'organs, {NATIONAL_WEEKLY_DECEASED_DONORS:,} deceased donors/week from 16,989/year): '
        f'this report simulates {scale_note} - {patients_per_round:,} patients/week, '
        f'{harvests_per_round:,} donors/week. One simulated round = 1 week.\n'
        '- **Strategies compared**:\n'
        f'{strategy_lines}\n'
        '- **Seeds per horizon** (fewer for longer horizons - runtime compounds with horizon '
        f'length):\n{horizon_lines}\n'
    )


def build_markdown_report(horizon_results: List[HorizonResult], network_node_count: int,
                          transplant_hospital_count: int, opo_count: int, scale: float,
                          patients_per_round: int, harvests_per_round: int) -> str:
    strategy_names = sorted({name for result in horizon_results
                            for name in result.trials_by_strategy})
    seeds_by_horizon = {result.years: result.seeds for result in horizon_results}

    sections = ['# National Allocation Strategy Scenario Report', '',
               _methodology_section(network_node_count, transplant_hospital_count, opo_count,
                                    strategy_names, seeds_by_horizon, scale, patients_per_round,
                                    harvests_per_round)]

    summary_headers = ['strategy', 'transplanted', 'wasted', 'deaths', 'hi-acuity deaths',
                       'median wait', 'life-years', 'final wait list']
    trajectory_headers = ['strategy', 'year', 'wait list size']
    significance_headers = ['strategy', 'metric', 'mean diff', '95% CI', 'effect size',
                            'adj. p', 'sig']

    for result in horizon_results:
        sections.append(f'## {result.years}-Year Horizon ({result.seeds} seed(s))')

        sections.append('### Summary\n' + _markdown_table(summary_headers,
                                                          _summary_rows(result)))

        sections.append('### Wait-List Size Trajectory (by year)\n' + _markdown_table(
                trajectory_headers, _trajectory_rows(result.trials_by_strategy)))

        if result.significance:
            significance_section = (f'### Significance vs. `{DEFAULT_REFERENCE_STRATEGY}`\n'
                                    + _markdown_table(significance_headers,
                                                      _significance_rows(result.significance)))
            floor_note = _significance_floor_note(result.seeds, result.significance)
            if floor_note:
                significance_section += '\n\n' + floor_note
            sections.append(significance_section)

    return '\n\n'.join(sections) + '\n'


def write_csv_outputs(horizon_results: List[HorizonResult], output_dir: Path) -> None:
    with (output_dir / 'summary.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['horizon_years', 'strategy', 'transplanted', 'wasted', 'deaths',
                         'hi_acuity_deaths', 'median_wait', 'life_years',
                         'final_wait_list_size'])
        for result in horizon_results:
            for row in result.aggregated:
                final_size = _final_wait_list_size_mean(
                        result.trials_by_strategy[row.strategy_name])
                writer.writerow([result.years, row.strategy_name,
                                f'{row.transplanted_mean:.2f}', f'{row.wasted_mean:.2f}',
                                f'{row.deaths_mean:.2f}', f'{row.deaths_high_acuity_mean:.2f}',
                                f'{row.median_wait_mean:.2f}', f'{row.life_years_mean:.2f}',
                                f'{final_size:.2f}'])

    with (output_dir / 'trajectory.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['horizon_years', 'strategy', 'year', 'wait_list_size'])
        for result in horizon_results:
            for row in _trajectory_rows(result.trials_by_strategy, thousands_separators=False):
                writer.writerow([result.years, *row])

    with (output_dir / 'significance.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['horizon_years', 'strategy', 'metric', 'mean_diff', 'ci_low', 'ci_high',
                         'effect_size', 'adjusted_p_value', 'significant'])
        for result in horizon_results:
            for r in result.significance:
                writer.writerow([result.years, r.strategy_name, r.metric, r.mean_diff, r.ci_low,
                                r.ci_high, r.effect_size, r.adjusted_p_value,
                                r.is_significant()])


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)

    horizon_years = [int(y.strip()) for y in args.horizon_years.split(',')]
    strategy_names = resolve_strategy_names(args.strategies)
    formats = [f.strip() for f in args.formats.split(',')]
    patients_per_round, harvests_per_round, living_donors_per_round = scaled_weekly_rates(
            args.scale)

    print(f'Building the real hospital network from {args.membership_csv} ...')
    network, transplant_hospital_ids, opo_ids = build_network(args.membership_csv)
    patient_nodes = list(transplant_hospital_ids)
    organ_nodes = list(transplant_hospital_ids | opo_ids)
    print(f'  {len(network.network_dict)} nodes ({len(transplant_hospital_ids)} transplant '
         f'hospitals, {len(opo_ids)} OPOs)')
    print(f'  scale={args.scale} -> {patients_per_round} patients/week, '
         f'{harvests_per_round} donors/week, {living_donors_per_round} living donors/week, '
         f'{OTHER_REMOVAL_ANNUAL_RATE:.0%}/yr other removals')

    output_dir = Path(args.output_dir) if args.output_dir \
        else Path('reports') / time.strftime('%Y-%m-%d_%H%M%S')
    output_dir.mkdir(parents=True, exist_ok=True)

    horizon_results = []
    for years in horizon_years:
        seeds = args.seeds if args.seeds is not None else default_seeds_for_horizon(years)
        rounds = years * ROUNDS_PER_YEAR
        print(f'Running {years}-year horizon ({seeds} seed(s), {rounds} rounds, '
             f'{len(strategy_names)} strategies)...')
        start = time.perf_counter()
        horizon_results.append(
                run_horizon(years, strategy_names, seeds, network, patient_nodes, organ_nodes,
                           patients_per_round, harvests_per_round,
                           living_donors_per_round=living_donors_per_round,
                           workers=args.workers))
        print(f'  done in {time.perf_counter() - start:.1f}s')

    if 'markdown' in formats:
        markdown_path = output_dir / 'report.md'
        markdown_path.write_text(build_markdown_report(
                horizon_results, len(network.network_dict), len(transplant_hospital_ids),
                len(opo_ids), args.scale, patients_per_round, harvests_per_round))
        print(f'Wrote {markdown_path}')

    if 'csv' in formats:
        write_csv_outputs(horizon_results, output_dir)
        print(f'Wrote CSV tables to {output_dir}')

    if 'pdf' in formats:
        from scenario_report_pdf import write_pdf_report
        pdf_path = output_dir / 'report.pdf'
        write_pdf_report(horizon_results, pdf_path, len(network.network_dict),
                         len(transplant_hospital_ids), len(opo_ids))
        print(f'Wrote {pdf_path}')


if __name__ == '__main__':
    main()
