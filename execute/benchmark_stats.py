"""
Pure-Python statistical helpers for comparing allocation strategies
(execute/benchmark_strategies.py). No new dependency - this follows the same precedent as
network_simulator.allocation.matchers.optimal, which uses networkx instead of scipy for
its own reasons. Two strategies run over the *same* seeds within a benchmark (see
run_benchmark's seed reuse), so comparisons here are paired, not independent-sample: a
sign-flip permutation test and a paired effect size, not a two-sample t-test.
"""
from __future__ import annotations

import math
import random
import statistics
from typing import Dict, List, Optional, Tuple


def paired_permutation_test(diffs: List[float], num_resamples: int = 2000,
                            rng: Optional[random.Random] = None) -> float:
    """
    Two-sided sign-flip permutation test p-value for H0: the paired differences have mean
    0. Distribution-free - appropriate here since outcome metrics (deaths, life-years) are
    counts, not normally distributed.

    :param diffs: per-seed (strategy - reference) differences for one metric
    :param int num_resamples: number of random sign-flip resamples
    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: two-sided p-value in (0, 1]
    """
    if not diffs:
        return 1.0
    source = rng or random
    observed = abs(statistics.mean(diffs))
    if observed == 0.0:
        return 1.0

    at_least_as_extreme = 0
    for _ in range(num_resamples):
        resampled = [d if source.random() < 0.5 else -d for d in diffs]
        if abs(statistics.mean(resampled)) >= observed - 1e-12:
            at_least_as_extreme += 1

    # +1/+1 (Monte Carlo) smoothing avoids reporting p=0.0 from a finite resample count
    return (at_least_as_extreme + 1) / (num_resamples + 1)


def bootstrap_ci(values: List[float], num_resamples: int = 2000, confidence: float = 0.95,
                 rng: Optional[random.Random] = None) -> Tuple[float, float]:
    """
    Percentile bootstrap confidence interval on the mean of `values`.

    :param values: sample to estimate a CI for (e.g. per-seed metric values, or per-seed
        paired differences)
    :param int num_resamples: number of bootstrap resamples
    :param float confidence: confidence level, e.g. 0.95 for a 95% CI
    :param random.Random rng: optional seeded source (defaults to the global module)
    :return: (lower, upper) bound of the CI on the mean
    """
    if not values:
        return (0.0, 0.0)
    source = rng or random
    n = len(values)

    means = sorted(statistics.mean(values[source.randrange(n)] for _ in range(n))
                   for _ in range(num_resamples))

    tail = (1 - confidence) / 2
    lo_idx = max(0, int(tail * num_resamples))
    hi_idx = min(num_resamples - 1, int((1 - tail) * num_resamples) - 1)
    return (means[lo_idx], means[hi_idx])


def paired_effect_size(diffs: List[float]) -> float:
    """
    Paired Cohen's d: mean(diffs) / stdev(diffs). Reported alongside p-values so
    "statistically significant" isn't conflated with "practically meaningful."

    :param diffs: per-seed (strategy - reference) differences for one metric
    :return: paired Cohen's d (0.0 if fewer than 2 diffs or no variance)
    """
    if len(diffs) < 2:
        return 0.0
    sd = statistics.stdev(diffs)
    if sd == 0.0:
        return 0.0
    return statistics.mean(diffs) / sd


def holm_bonferroni(p_values: Dict[str, float]) -> Dict[str, float]:
    """
    Holm step-down adjustment controlling the family-wise error rate across multiple
    comparisons (e.g. every strategy compared against one reference in a single benchmark
    run) - less conservative than plain Bonferroni while still valid.

    :param p_values: {comparison name: raw p-value}
    :return: {comparison name: Holm-adjusted p-value}, monotonically non-decreasing in
        rank and capped at 1.0
    """
    m = len(p_values)
    ranked = sorted(p_values.items(), key=lambda item: item[1])

    adjusted: Dict[str, float] = {}
    running_max = 0.0
    for i, (name, p) in enumerate(ranked):
        running_max = max(running_max, (m - i) * p)
        adjusted[name] = min(1.0, running_max)
    return adjusted


def _inverse_normal_cdf(p: float) -> float:
    """
    Standard normal quantile function (inverse CDF), via Acklam's rational approximation
    (accurate to ~1.15e-9) - avoids a scipy dependency for required_sample_size.

    :param float p: probability in (0, 1)
    :return: z such that P(Z <= z) == p for standard normal Z
    """
    if not 0.0 < p < 1.0:
        raise ValueError('p must be in (0, 1)')

    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
        1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
        6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
        -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
        3.754408661907416e+00]

    p_low = 0.02425
    p_high = 1 - p_low

    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p <= p_high:
        q = p - 0.5
        r = q * q
        return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
               (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    q = math.sqrt(-2 * math.log(1 - p))
    return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
            ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)


def required_sample_size(std_diff: float, min_effect: float, alpha: float = 0.05,
                         power: float = 0.8) -> int:
    """
    Normal-approximation sample size for a paired comparison: how many seeds are needed to
    reliably detect a difference of at least `min_effect`, given the paired differences'
    standard deviation observed in a pilot run - rather than guessing at a seed count.

    :param float std_diff: standard deviation of the paired per-seed differences (e.g.
        from a pilot benchmark run)
    :param float min_effect: smallest true mean difference worth detecting
    :param float alpha: two-sided significance level
    :param float power: desired probability of detecting an effect of size `min_effect`
    :return: required number of paired seeds, rounded up
    """
    if std_diff <= 0.0:
        raise ValueError('std_diff must be positive')
    if min_effect <= 0.0:
        raise ValueError('min_effect must be positive')

    z_alpha = _inverse_normal_cdf(1 - alpha / 2)
    z_beta = _inverse_normal_cdf(power)
    n = ((z_alpha + z_beta) * std_diff / min_effect) ** 2
    return math.ceil(n)
