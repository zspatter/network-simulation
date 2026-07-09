"""
One-at-a-time sensitivity analysis over the model's documented-approximation constants.

Each clinical constant (removal hazard, mortality rate, discard rates, transit overhead,
donor recovery, ...) is perturbed up and down by a fixed fraction while everything else is
held fixed, and the effect on the headline outcomes (wait-list deaths, life-years, discard
rate, final wait-list size) is measured across seeded trials. The result tells you which
constants a conclusion is *robust to* versus *sensitive to* - so a finding like "acuity
strategies save lives" can be reported with the caveat of which assumptions it leans on.

Runs on a small hand-built coordinate network (no geocoding) so the perturbation sweep is
cheap; sensitivities are relative, so absolute scale is not needed.

Run directly: `python execute/sensitivity_analysis.py [--factor 0.25] [--seeds 4]`
"""
from __future__ import annotations

import argparse
import statistics
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence

from benchmark_strategies import run_trial

from network_simulator import distance
from network_simulator.allocation import STRATEGIES
from network_simulator.clinical import acceptance, frequencies, mortality, removal
from network_simulator.Network import Network
from network_simulator.Node import Node

_CITIES = [(1, 'Chicago', 41.88, -87.63), (2, 'Boston', 42.36, -71.06),
           (3, 'Los Angeles', 34.05, -118.24), (4, 'Houston', 29.76, -95.37),
           (5, 'Atlanta', 33.75, -84.39), (6, 'Denver', 39.74, -104.99),
           (7, 'Seattle', 47.61, -122.33), (8, 'Miami', 25.76, -80.19)]


def _coordinate_network() -> Network:
    return Network({i: Node(i, name, latitude=la, longitude=lo)
                    for i, name, la, lo in _CITIES})


@dataclass
class Knob:
    """A model constant to perturb. `set_factor` multiplies it; `reset` restores it."""
    label: str
    set_factor: Callable[[float], None]
    reset: Callable[[], None]


def _scalar_knob(label: str, module, attr: str) -> Knob:
    base = getattr(module, attr)
    return Knob(label,
                set_factor=lambda f: setattr(module, attr, base * f),
                reset=lambda: setattr(module, attr, base))


def _dict_knob(label: str, module, attr: str, cap: float = 0.99) -> Knob:
    # Mutate the dict *in place* (not rebind): other modules imported this same dict object
    # by reference (e.g. OrganGenerator holds DONOR_RECOVERY_PROBABILITIES), so rebinding the
    # module attribute wouldn't reach them - only an in-place edit does.
    live = getattr(module, attr)
    base = dict(live)

    def set_factor(f: float) -> None:
        live.clear()
        live.update({k: min(cap, v * f) for k, v in base.items()})

    def reset() -> None:
        live.clear()
        live.update(base)

    return Knob(label, set_factor, reset)


def build_knobs() -> List[Knob]:
    return [
        _scalar_knob('other_removal_rate', removal, 'OTHER_REMOVAL_ANNUAL_RATE'),
        _scalar_knob('max_acuity_death_rate', mortality, 'ACUITY_MAX_ANNUAL_RATE'),
        _dict_knob('base_discard_prob', acceptance, 'BASE_DISCARD_PROB'),
        _scalar_knob('ischemia_discard_per_hour', acceptance, 'ISCHEMIA_DISCARD_PER_HOUR'),
        _scalar_knob('graft_penalty_per_hour', acceptance, 'GRAFT_PENALTY_PER_HOUR'),
        _scalar_knob('air_overhead_hours', distance, 'AIR_OVERHEAD_HOURS'),
        _dict_knob('donor_recovery_prob', frequencies, 'DONOR_RECOVERY_PROBABILITIES'),
    ]


def _measure(seeds: int, rounds: int, patients_per_round: int,
             harvests_per_round: int) -> Dict[str, float]:
    """Mean headline outcomes across `seeds` fresh-network trials at the current constants."""
    deaths, life_years, discard_rates, final_sizes = [], [], [], []
    for seed in range(seeds):
        m = run_trial(seed=seed, strategy=STRATEGIES['real_world_circle'], rounds=rounds,
                      patients_per_round=patients_per_round, harvests_per_round=harvests_per_round,
                      network=_coordinate_network(), snapshot_interval_rounds=rounds,
                      # read dynamically so the other_removal_rate knob's perturbation is applied
                      other_removal_annual_rate=removal.OTHER_REMOVAL_ANNUAL_RATE,
                      living_donors_per_round=3, realistic_outcomes=True)
        recovered = m.organs_transplanted + m.organs_wasted
        deaths.append(m.waitlist_deaths)
        life_years.append(m.life_years_saved)
        discard_rates.append(m.organs_discarded / recovered if recovered else 0.0)
        final_sizes.append(m.wait_list_size_snapshots[-1][1] if m.wait_list_size_snapshots else 0)
    return {'deaths': statistics.mean(deaths), 'life_years': statistics.mean(life_years),
            'discard': statistics.mean(discard_rates), 'final_size': statistics.mean(final_sizes)}


@dataclass
class Sensitivity:
    knob: str
    deaths_swing_pct: float   # % change in deaths from low to high perturbation
    life_years_swing_pct: float
    discard_swing_pct: float


def _swing(low: float, high: float, base: float) -> float:
    return (high - low) / base * 100.0 if base else 0.0


def run_sensitivity(factor: float, seeds: int, rounds: int, patients_per_round: int,
                    harvests_per_round: int) -> List[Sensitivity]:
    """Perturbs each knob by +/-factor and returns the resulting swing in each headline outcome."""
    trial = dict(seeds=seeds, rounds=rounds, patients_per_round=patients_per_round,
                 harvests_per_round=harvests_per_round)

    results: List[Sensitivity] = []
    for knob in build_knobs():
        try:
            knob.set_factor(1.0 - factor)
            low = _measure(**trial)
            knob.set_factor(1.0 + factor)
            high = _measure(**trial)
        finally:
            knob.reset()
        base = _measure(**trial)
        results.append(Sensitivity(
                knob=knob.label,
                deaths_swing_pct=_swing(low['deaths'], high['deaths'], base['deaths']),
                life_years_swing_pct=_swing(low['life_years'], high['life_years'],
                                            base['life_years']),
                discard_swing_pct=_swing(low['discard'], high['discard'], base['discard'])))

    # rank by absolute effect on the "lives" outcome - what the conclusions most depend on
    results.sort(key=lambda s: abs(s.deaths_swing_pct), reverse=True)
    return results


def format_report(results: List[Sensitivity], factor: float) -> str:
    header = (f"{'constant (+/-' + str(int(factor * 100)) + '%)':<28}"
              f"{'deaths swing':>14}{'life-yrs swing':>16}{'discard swing':>15}")
    lines = [header, '-' * len(header)]
    for row in results:
        lines.append(f'{row.knob:<28}{row.deaths_swing_pct:>13.1f}%'
                     f'{row.life_years_swing_pct:>15.1f}%{row.discard_swing_pct:>14.1f}%')
    lines.append('')
    lines.append('Swing = % change in the outcome from the low to the high perturbation, '
                 'ranked by\neffect on wait-list deaths. Large swing = a conclusion leaning on '
                 'that constant is\nsensitive to it; near-zero = robust.')
    return '\n'.join(lines)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--factor', type=float, default=0.25,
                        help='Perturbation fraction, e.g. 0.25 = +/-25%% (default: 0.25)')
    parser.add_argument('--seeds', type=int, default=4, help='Seeds per perturbation (default: 4)')
    parser.add_argument('--years', type=int, default=3, help='Simulated years (default: 3)')
    parser.add_argument('--patients-per-round', type=int, default=30)
    parser.add_argument('--harvests-per-round', type=int, default=8)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    print(f'Sensitivity sweep: +/-{args.factor:.0%}, {args.seeds} seeds, {args.years}yr ...\n')
    results = run_sensitivity(args.factor, args.seeds, args.years * 52,
                              args.patients_per_round, args.harvests_per_round)
    print(format_report(results, args.factor))


if __name__ == '__main__':
    main()
