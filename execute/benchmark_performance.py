"""
Performance benchmark harness - measures wall-clock cost of the simulation hot
paths (feasibility, shortest-path, allocation, collection ops) on fixed, seeded
workloads, and diffs a run against a saved baseline.

This exists to make performance work *measurable*: capture a baseline, apply an
optimization, and quantify the change on an identical workload rather than
eyeballing it. It is deliberately dependency-free and uses the synthetic
GraphBuilder network (no geocoding) so a run is fully reproducible offline.

Each scenario records a workload *fingerprint* (organs transplanted, deaths,
final wait-list size) alongside its timing. For a behavior-preserving
optimization the fingerprint must be identical between baseline and candidate -
if it drifts, the comparison is measuring two different workloads and the
speedup is not apples-to-apples. Behavior-changing work (e.g. a new removal
channel) is expected to shift the fingerprint; re-baseline after it lands.

Usage:
    python execute/benchmark_performance.py --out benchmarks/baseline.json
    python execute/benchmark_performance.py --compare benchmarks/baseline.json
"""
from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from benchmark_strategies import run_trial

from organflow.allocation import STRATEGIES


@dataclass
class Scenario:
    """A fixed, seeded workload. `trial_kwargs` is forwarded to run_trial."""
    name: str
    description: str
    strategy: str
    seed: int
    trial_kwargs: Dict[str, int]


# Scenarios chosen to stress distinct hot paths. Sized so each takes a few seconds
# at baseline - large enough that the wait-list grows into the thousands (where
# feasibility's O(organs x waitlist) and the collections' O(n^2) membership bite),
# small enough that a full sweep stays well under a minute.
SCENARIOS: List[Scenario] = [
    Scenario('growth_greedy',
             'Growing wait list, greedy/priority - stresses feasibility O(organs x waitlist) '
             'and O(n^2) wait-list membership.',
             'baseline', seed=0,
             trial_kwargs=dict(num_nodes=40, rounds=40, patients_per_round=160,
                               harvests_per_round=45)),
    Scenario('growth_optimal',
             'Growing wait list, optimal matching - adds LAP solve cost on top of feasibility.',
             'optimal_composite', seed=0,
             trial_kwargs=dict(num_nodes=40, rounds=40, patients_per_round=160,
                               harvests_per_round=45)),
    Scenario('wide_network',
             'Larger network, tiered real-world - stresses shortest-path (Dijkstra per origin) '
             'over many nodes.',
             'real_world_circle', seed=0,
             trial_kwargs=dict(num_nodes=220, rounds=16, patients_per_round=90,
                               harvests_per_round=24)),
]


@dataclass
class ScenarioResult:
    name: str
    best_seconds: float
    mean_seconds: float
    repeats: int
    # workload fingerprint - must match across behavior-preserving optimizations
    transplanted: int
    waitlist_deaths: int
    final_wait_list: int


@dataclass
class BenchmarkResult:
    label: str
    python: str
    machine: str
    scenarios: List[ScenarioResult] = field(default_factory=list)


def run_scenario(scenario: Scenario, repeats: int) -> ScenarioResult:
    strategy = STRATEGIES[scenario.strategy]
    timings: List[float] = []
    metrics = None
    for _ in range(repeats):
        start = time.perf_counter()
        metrics = run_trial(scenario.seed, strategy, **scenario.trial_kwargs)
        timings.append(time.perf_counter() - start)

    assert metrics is not None
    final = metrics.wait_list_size_snapshots[-1][1] if metrics.wait_list_size_snapshots else 0
    # final wait-list size is derived from a snapshot; request one on the last round
    return ScenarioResult(
            name=scenario.name,
            best_seconds=min(timings),
            mean_seconds=statistics.mean(timings),
            repeats=repeats,
            transplanted=metrics.organs_transplanted,
            waitlist_deaths=metrics.waitlist_deaths,
            final_wait_list=final)


def run_all(repeats: int, label: str,
            scenarios: Sequence[Scenario] = SCENARIOS) -> BenchmarkResult:
    result = BenchmarkResult(label=label, python=platform.python_version(),
                             machine=platform.platform())
    for scenario in scenarios:
        # ensure a final-round snapshot so the fingerprint captures wait-list size
        kwargs = dict(scenario.trial_kwargs)
        kwargs['snapshot_interval_rounds'] = kwargs['rounds']
        scen = Scenario(scenario.name, scenario.description, scenario.strategy,
                        scenario.seed, kwargs)
        print(f'  {scenario.name:16s} ...', end='', flush=True)
        res = run_scenario(scen, repeats)
        print(f' {res.best_seconds:8.3f}s (best of {repeats})  '
              f'[tx={res.transplanted} deaths={res.waitlist_deaths} '
              f'wl={res.final_wait_list}]')
        result.scenarios.append(res)
    return result


def _fmt_delta(baseline: float, candidate: float) -> str:
    if baseline <= 0:
        return 'n/a'
    speedup = baseline / candidate if candidate > 0 else float('inf')
    pct = (candidate - baseline) / baseline * 100.0
    return f'{speedup:5.2f}x  ({pct:+6.1f}%)'


def print_comparison(baseline: BenchmarkResult, candidate: BenchmarkResult) -> None:
    by_name: Dict[str, ScenarioResult] = {s.name: s for s in baseline.scenarios}
    print(f"\nComparison: '{candidate.label}' vs baseline '{baseline.label}'")
    header = (f"{'scenario':16s}{'baseline':>11}{'candidate':>11}{'speedup':>20}"
              f"{'fingerprint':>16}")
    print(header)
    print('-' * len(header))
    for cand in candidate.scenarios:
        base = by_name.get(cand.name)
        if base is None:
            print(f'{cand.name:16s}{"(new)":>11}')
            continue
        same = (base.transplanted == cand.transplanted
                and base.waitlist_deaths == cand.waitlist_deaths
                and base.final_wait_list == cand.final_wait_list)
        fingerprint = 'identical' if same else 'CHANGED'
        print(f'{cand.name:16s}{base.best_seconds:>10.3f}s{cand.best_seconds:>10.3f}s'
              f'{_fmt_delta(base.best_seconds, cand.best_seconds):>20}{fingerprint:>16}')
    print("\n(fingerprint 'CHANGED' => behavior differs; the speedup is not apples-to-apples)")


def _load(path: Path) -> BenchmarkResult:
    data = json.loads(path.read_text())
    scenarios = [ScenarioResult(**s) for s in data.pop('scenarios')]
    return BenchmarkResult(scenarios=scenarios, **data)


def _save(result: BenchmarkResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(result), indent=2))


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--repeats', type=int, default=3,
                        help='Timed repeats per scenario; the best is reported (default: 3)')
    parser.add_argument('--label', default=None,
                        help='Label stored with this run (default: a timestamp)')
    parser.add_argument('--out', default=None,
                        help='Write results JSON to this path')
    parser.add_argument('--compare', default=None,
                        help='Compare this run against a previously-saved baseline JSON')
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    label = args.label or time.strftime('%Y-%m-%d_%H%M%S')

    print(f'Running performance benchmark (label={label!r}, repeats={args.repeats})...')
    result = run_all(args.repeats, label)

    if args.out:
        _save(result, Path(args.out))
        print(f'Wrote {args.out}')

    if args.compare:
        baseline = _load(Path(args.compare))
        print_comparison(baseline, result)


if __name__ == '__main__':
    main()
