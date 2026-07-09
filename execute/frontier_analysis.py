"""
Continuous-distribution frontier sweep: the medical-benefit-versus-geography trade-off.

Holds a continuous-distribution scorer's medical/wait/sensitization weights fixed and sweeps
its geographic proximity_weight from 0 (geography ignored - the sickest candidate wins wherever
they are) upward (organs increasingly kept local). For each weight it runs seeded trials and
reports the outcomes on both axes of the policy debate:

  benefit / utility : life-years saved, wait-list deaths
  geographic cost   : mean transit of transplanted organs (cold-ischemia / logistics burden),
                      organ discard rate
  equity            : fairness spread across priority tiers

The result traces the actual trade-off frontier rather than asserting one point is best - which
is the whole question continuous distribution raises. Runs on a small coordinate network (no
geocoding) since the trade-off is relative.

Run directly: `python execute/frontier_analysis.py [--seeds 5] [--years 3]`
"""
from __future__ import annotations

import argparse
import statistics
from dataclasses import dataclass
from typing import List, Optional, Sequence

from benchmark_strategies import run_trial

from organflow.allocation import Strategy
from organflow.allocation.matchers.optimal import OptimalMatcher
from organflow.allocation.scoring import ContinuousDistributionScore
from organflow.clinical.removal import OTHER_REMOVAL_ANNUAL_RATE
from organflow.Network import Network
from organflow.Node import Node

_CITIES = [(1, 'Chicago', 41.88, -87.63), (2, 'Boston', 42.36, -71.06),
           (3, 'Los Angeles', 34.05, -118.24), (4, 'Houston', 29.76, -95.37),
           (5, 'Atlanta', 33.75, -84.39), (6, 'Denver', 39.74, -104.99),
           (7, 'Seattle', 47.61, -122.33), (8, 'Miami', 25.76, -80.19)]

# Geography emphasis to sweep: 0 = geography ignored, rising = organs kept ever more local.
DEFAULT_PROXIMITY_WEIGHTS = (0.0, 0.5, 1.0, 2.0, 4.0, 8.0)


def _coordinate_network() -> Network:
    return Network({i: Node(i, name, latitude=la, longitude=lo)
                    for i, name, la, lo in _CITIES})


@dataclass
class FrontierPoint:
    proximity_weight: float
    life_years: float
    deaths: float
    mean_transit: float
    discard_rate: float
    fairness_spread: float


def run_frontier(proximity_weights: Sequence[float], seeds: int, rounds: int,
                 patients_per_round: int, harvests_per_round: int) -> List[FrontierPoint]:
    """Runs the sweep and returns one aggregated FrontierPoint per proximity weight."""
    points: List[FrontierPoint] = []
    for weight in proximity_weights:
        strategy = Strategy(f'continuous_w{weight}', OptimalMatcher(),
                            ContinuousDistributionScore(proximity_weight=weight))
        life_years, deaths, transits, discards, spreads = [], [], [], [], []
        for seed in range(seeds):
            m = run_trial(seed=seed, strategy=strategy, rounds=rounds,
                          patients_per_round=patients_per_round,
                          harvests_per_round=harvests_per_round, network=_coordinate_network(),
                          other_removal_annual_rate=OTHER_REMOVAL_ANNUAL_RATE,
                          living_donors_per_round=3, realistic_outcomes=True)
            recovered = m.organs_transplanted + m.organs_wasted
            life_years.append(m.life_years_saved)
            deaths.append(m.waitlist_deaths)
            transits.append(statistics.mean(m.transit_of_transplants)
                            if m.transit_of_transplants else 0.0)
            discards.append(m.organs_discarded / recovered if recovered else 0.0)
            spreads.append(m.fairness_spread())
        points.append(FrontierPoint(
                proximity_weight=weight, life_years=statistics.mean(life_years),
                deaths=statistics.mean(deaths), mean_transit=statistics.mean(transits),
                discard_rate=statistics.mean(discards),
                fairness_spread=statistics.mean(spreads)))
    return points


def format_frontier(points: List[FrontierPoint]) -> str:
    header = (f"{'proximity wt':>13}{'life-years':>12}{'deaths':>9}"
              f"{'mean transit(h)':>17}{'discard':>9}{'fairness spread':>17}")
    lines = [header, '-' * len(header)]
    for p in points:
        lines.append(f'{p.proximity_weight:>13.1f}{p.life_years:>12,.0f}{p.deaths:>9,.0f}'
                     f'{p.mean_transit:>17.2f}{p.discard_rate:>8.1%}{p.fairness_spread:>17.3f}')
    lines.append('')
    lines.append('Reading up the proximity-weight column trades medical reach for locality: '
                 'higher weight\nkeeps organs local (lower mean transit, less ischemia waste) '
                 'but can skip sicker faraway\ncandidates. The best point depends on how you '
                 'value lives vs. logistics - that is the frontier.')
    return '\n'.join(lines)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--weights', default=None,
                        help='Comma-separated proximity weights (default: 0,0.5,1,2,4,8)')
    parser.add_argument('--seeds', type=int, default=5, help='Seeds per weight (default: 5)')
    parser.add_argument('--years', type=int, default=3, help='Simulated years (default: 3)')
    parser.add_argument('--patients-per-round', type=int, default=30)
    parser.add_argument('--harvests-per-round', type=int, default=8)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    weights = ([float(w) for w in args.weights.split(',')] if args.weights
               else list(DEFAULT_PROXIMITY_WEIGHTS))
    print(f'Continuous-distribution frontier: proximity weights {weights}, '
          f'{args.seeds} seeds, {args.years}yr ...\n')
    points = run_frontier(weights, args.seeds, args.years * 52,
                          args.patients_per_round, args.harvests_per_round)
    print(format_frontier(points))


if __name__ == '__main__':
    main()
