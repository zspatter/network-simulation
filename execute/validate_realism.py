"""
Regenerable model-validation report: runs the reality-calibrated simulation on the
real hospital network and prints how its aggregate behavior compares to published
2024 OPTN/SRTR figures - arrivals, deceased/living transplants, wait-list deaths,
organ non-use, and the standing wait-list size and composition.

This turns the ad-hoc calibration checks into a committed, rerunnable artifact: run
it after any change to the clinical constants to confirm the model still tracks
reality. It is the companion to tests/test_calibration.py (which guards the same
targets as pass/fail assertions).

Run directly: `python execute/validate_realism.py [--scale 0.1] [--years 8]`
Sources: OPTN/SRTR 2024 Annual Data Report (https://srtr.hrsa.gov/adr/2024/),
retrieved 2026-07-08.
"""
from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

from benchmark_strategies import run_trial
from scenario_report import DEFAULT_MEMBERSHIP_CSV, build_network, scaled_weekly_rates

from organflow.allocation import STRATEGIES
from organflow.clinical.removal import OTHER_REMOVAL_ANNUAL_RATE
from organflow.clinical.retransplant import RETRANSPLANT_SHARE_OF_LISTINGS

# ---- Published 2024 OPTN/SRTR national figures (full scale) ----
OPTN_2024 = {
    'new_registrations_per_year': 70_600,
    'deceased_donors_per_year': 16_989,
    'deceased_transplants_per_year': 42_048,
    'living_transplants_per_year': 7_024,
    'overall_non_use_rate': 0.207,
    # standing (point-prevalence) wait list, not the flow-inclusive 167k "ever listed in 2024"
    'waitlist_snapshot': 103_000,
    'kidney_share_of_waitlist': 0.86,
    # re-transplant candidates as a share of all new listings (kidney ~9.6%, liver 3.4%, blended)
    'retransplant_share_of_listings': RETRANSPLANT_SHARE_OF_LISTINGS,
}


@dataclass
class ValidationRow:
    metric: str
    model: float
    target: float
    unit: str

    def ratio(self) -> float:
        return self.model / self.target if self.target else float('nan')


def run_validation(network, patient_nodes: List[int], organ_nodes: List[int],
                   scale: float, years: int, seeds: int) -> Dict[str, float]:
    """
    Runs the reality-calibrated real_world_circle strategy over `years` years at `scale`,
    averaged across `seeds`, and returns full-scale-extrapolated model metrics.
    """
    patients_per_round, harvests_per_round, living_per_round = scaled_weekly_rates(scale)
    rounds = years * 52

    totals = {k: 0.0 for k in ('transplanted', 'discarded', 'wasted', 'deaths', 'living',
                               'removals', 'final_size', 'kidney_final', 'first_time',
                               'retransplant')}
    for seed in range(seeds):
        m = run_trial(seed=seed, strategy=STRATEGIES['real_world_circle'], rounds=rounds,
                      patients_per_round=patients_per_round, harvests_per_round=harvests_per_round,
                      network=network, patient_nodes=patient_nodes, organ_nodes=organ_nodes,
                      snapshot_interval_rounds=rounds, living_donors_per_round=living_per_round,
                      other_removal_annual_rate=OTHER_REMOVAL_ANNUAL_RATE, realistic_outcomes=True)
        totals['transplanted'] += m.organs_transplanted
        totals['discarded'] += m.organs_discarded
        totals['wasted'] += m.organs_wasted
        totals['deaths'] += m.waitlist_deaths
        totals['living'] += m.living_donor_transplants
        totals['removals'] += m.other_removals
        totals['first_time'] += m.first_time_listings
        totals['retransplant'] += m.retransplant_listings
        final = m.wait_list_size_snapshots[-1][1] if m.wait_list_size_snapshots else 0
        totals['final_size'] += final

    per_seed = {k: v / seeds for k, v in totals.items()}
    recovered = per_seed['transplanted'] + per_seed['wasted']
    all_listings = per_seed['first_time'] + per_seed['retransplant']
    to_full = 1.0 / scale
    return {
        'deceased_transplants_per_year': per_seed['transplanted'] / years * to_full,
        'living_transplants_per_year': per_seed['living'] / years * to_full,
        'deaths_per_year': per_seed['deaths'] / years * to_full,
        'removals_per_year': per_seed['removals'] / years * to_full,
        'non_use_rate': per_seed['discarded'] / recovered if recovered else 0.0,
        'retransplant_share': per_seed['retransplant'] / all_listings if all_listings else 0.0,
        'waitlist_final': per_seed['final_size'] * to_full,
    }


def comparison_rows(model: Dict[str, float]) -> List[ValidationRow]:
    """Builds the model-vs-OPTN comparison table. Pure, so it is unit-testable."""
    return [
        ValidationRow('Deceased-donor transplants/yr', model['deceased_transplants_per_year'],
                      OPTN_2024['deceased_transplants_per_year'], 'count'),
        ValidationRow('Living-donor transplants/yr', model['living_transplants_per_year'],
                      OPTN_2024['living_transplants_per_year'], 'count'),
        ValidationRow('Wait-list deaths/yr', model['deaths_per_year'], 6_000, 'count'),
        ValidationRow('Non-death removals/yr', model['removals_per_year'], 8_000, 'count'),
        ValidationRow('Organ non-use rate', model['non_use_rate'],
                      OPTN_2024['overall_non_use_rate'], 'rate'),
        ValidationRow('Re-transplant share of listings', model['retransplant_share'],
                      OPTN_2024['retransplant_share_of_listings'], 'rate'),
        ValidationRow('Wait-list size (approaching)', model['waitlist_final'],
                      OPTN_2024['waitlist_snapshot'], 'count'),
    ]


def _format_table(rows: List[ValidationRow]) -> str:
    header = f"{'metric':<34}{'model (full-scale)':>20}{'OPTN 2024':>14}{'ratio':>9}"
    lines = [header, '-' * len(header)]
    for row in rows:
        if row.unit == 'rate':
            model_s, target_s = f'{row.model:.1%}', f'{row.target:.1%}'
        else:
            model_s, target_s = f'{row.model:,.0f}', f'{row.target:,.0f}'
        lines.append(f'{row.metric:<34}{model_s:>20}{target_s:>14}{row.ratio():>8.2f}x')
    return '\n'.join(lines)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--scale', type=float, default=0.1,
                        help='Fraction of national volume to simulate (default: 0.1)')
    parser.add_argument('--years', type=int, default=8,
                        help='Simulated years - the wait list needs several to approach '
                             'steady state (default: 8)')
    parser.add_argument('--seeds', type=int, default=3, help='Seeds to average (default: 3)')
    parser.add_argument('--membership-csv', default=str(DEFAULT_MEMBERSHIP_CSV))
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    os.environ.setdefault('PYTHONHASHSEED', '0')

    print(f'Building the real hospital network from {args.membership_csv} ...')
    network, transplant_hospital_ids, opo_ids = build_network(args.membership_csv)
    print(f'  {len(network.network_dict)} nodes; running {args.years}yr x {args.seeds} seed(s) '
          f'at scale {args.scale} ...\n')

    model = run_validation(network, list(transplant_hospital_ids),
                           list(transplant_hospital_ids | opo_ids),
                           args.scale, args.years, args.seeds)
    print(_format_table(comparison_rows(model)))
    print('\nNote: model figures are extrapolated from the simulated scale to full national '
          'volume.\nWait-list size is still approaching steady state at this horizon; run more '
          'years for a\ncloser match. Targets: OPTN/SRTR 2024 Annual Data Report.')


if __name__ == '__main__':
    main()
