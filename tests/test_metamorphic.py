"""
Metamorphic tests: relations that must hold between the outputs of *related* inputs, even
when we can't state the exact output for any single input. These catch model regressions
that a fixed-value assertion never would - e.g. "more organs can't cost lives."
"""
import random
import statistics
import sys
from os.path import abspath, dirname, join

sys.path.insert(0, join(dirname(dirname(abspath(__file__))), 'execute'))

from benchmark_strategies import run_trial  # noqa: E402

from organflow.allocation import STRATEGIES  # noqa: E402
from organflow.allocation.matchers.optimal import OptimalMatcher  # noqa: E402
from organflow.allocation.scoring import AcuityScore, PriorityScore  # noqa: E402
from organflow.BloodType import BloodType  # noqa: E402
from organflow.compatibility_markers import (  # noqa: E402
    BloodTypeLetter,
    BloodTypePolarity,
    OrganType,
)
from organflow.GraphBuilder import GraphBuilder  # noqa: E402
from organflow.Organ import Organ  # noqa: E402
from organflow.OrganGenerator import OrganGenerator  # noqa: E402
from organflow.OrganList import OrganList  # noqa: E402
from organflow.Patient import Patient  # noqa: E402
from organflow.PatientGenerator import PatientGenerator  # noqa: E402
from organflow.WaitList import WaitList  # noqa: E402


def _network_and_waitlist(seed, n_patients):
    rng = random.Random(seed)
    network = GraphBuilder.graph_builder(8, rng=rng)
    wait_list = WaitList(PatientGenerator.generate_patients(network, n_patients, rng))
    return rng, network, wait_list


def test_adding_organs_to_a_batch_never_reduces_matches():
    rng, network, wait_list = _network_and_waitlist(seed=3, n_patients=30)

    base = OrganList()
    OrganGenerator.generate_organs_to_list(network, 3, base, rng)
    augmented = OrganList(list(base.organ_list))
    OrganGenerator.generate_organs_to_list(network, 3, augmented, rng)  # same organs + more

    matcher, scorer = OptimalMatcher(), PriorityScore()
    base_matches = matcher.allocate(base, wait_list, network, scorer)
    more_matches = matcher.allocate(augmented, wait_list, network, scorer)

    assert len(more_matches.matches) >= len(base_matches.matches)


def test_adding_patients_to_a_batch_never_reduces_matches():
    rng, network, wait_list = _network_and_waitlist(seed=5, n_patients=8)
    organ_list = OrganList()
    OrganGenerator.generate_organs_to_list(network, 6, organ_list, rng)

    matcher, scorer = OptimalMatcher(), PriorityScore()
    few = matcher.allocate(organ_list, wait_list, network, scorer)

    wait_list.add_patients(PatientGenerator.generate_patients(network, 20, rng))
    many = matcher.allocate(organ_list, wait_list, network, scorer)

    assert len(many.matches) >= len(few.matches)


def _mean_deaths(harvests_per_round, seeds):
    return statistics.mean(
            run_trial(seed=seed, strategy=STRATEGIES['real_world_circle'], num_nodes=12,
                      rounds=8, patients_per_round=20, harvests_per_round=harvests_per_round
                      ).waitlist_deaths
            for seed in seeds)


def test_more_donor_supply_does_not_increase_wait_list_deaths():
    # averaged over seeds, abundant organs must not kill more patients than scarce ones - a
    # basic sanity check the whole allocation-plus-mortality pipeline must satisfy
    scarce = _mean_deaths(harvests_per_round=2, seeds=range(6))
    abundant = _mean_deaths(harvests_per_round=15, seeds=range(6))
    assert abundant <= scarce


def test_acuity_scorer_ranks_a_sicker_patient_at_least_as_high():
    # monotonicity of the "sickest first" policy: raising a patient's acuity can only raise
    # (never lower) its allocation score
    o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)
    organ = Organ(OrganType.Liver, o_neg, location=1)
    sicker = Patient('sick', 'n/a', OrganType.Liver, o_neg, 100, 1, acuity=0.9)
    healthier = Patient('well', 'n/a', OrganType.Liver, o_neg, 100, 1, acuity=0.2)

    scorer = AcuityScore()
    assert scorer.score(sicker, organ, 1.0) >= scorer.score(healthier, organ, 1.0)
