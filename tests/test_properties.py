"""
Property-based tests (Hypothesis): invariants that must hold across *all* inputs, not just
the hand-picked cases the example-based tests cover. These catch the edge cases and the
"I didn't think of that input" bugs that line coverage cannot.
"""
import random

from hypothesis import given, settings
from hypothesis import strategies as st

from organflow.allocation.feasibility import feasible_matches_by_organ
from organflow.allocation.matchers.greedy import GreedyMatcher
from organflow.allocation.matchers.optimal import OptimalMatcher
from organflow.allocation.scoring import PriorityScore
from organflow.BloodType import BloodType
from organflow.clinical import acceptance
from organflow.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from organflow.GraphBuilder import GraphBuilder
from organflow.OrganGenerator import OrganGenerator
from organflow.OrganList import OrganList
from organflow.PatientGenerator import PatientGenerator
from organflow.WaitList import WaitList

_LETTERS = list(BloodTypeLetter)
_POLARITIES = list(BloodTypePolarity)

# ABO antigens each blood-type letter carries - the medically-correct rule, derived
# independently of BloodType's bitmask implementation so this is a genuine cross-check.
_ABO_ANTIGENS = {
    BloodTypeLetter.O: frozenset(),
    BloodTypeLetter.A: frozenset('A'),
    BloodTypeLetter.B: frozenset('B'),
    BloodTypeLetter.AB: frozenset('AB'),
}


@given(st.sampled_from(_LETTERS), st.sampled_from(_POLARITIES),
       st.sampled_from(_LETTERS), st.sampled_from(_POLARITIES))
def test_blood_compatibility_matches_independent_abo_rh_rule(rl, rp, dl, dp):
    recipient, donor = BloodType(rl, rp), BloodType(dl, dp)
    # a recipient can receive a donor organ iff the donor's ABO antigens are a subset of the
    # recipient's, and the recipient is Rh+ or the donor is Rh-
    abo_ok = _ABO_ANTIGENS[dl] <= _ABO_ANTIGENS[rl]
    rh_ok = rp.value >= dp.value
    expected = abo_ok and rh_ok

    assert recipient.is_compatible_recipient(donor) is expected
    # the two directions must agree: D can donate to R iff R can receive from D
    assert donor.is_compatible_donor(recipient) is expected


@given(a=st.floats(0.0, 100.0), b=st.floats(0.0, 100.0))
def test_donor_quality_effects_are_monotonic(a, b):
    lo, hi = min(a, b), max(a, b)
    # a more marginal organ (higher quality index) is never discarded less often and never grafts
    # better than a less marginal one - the whole point of the continuous quality axis
    assert acceptance.quality_discard_multiplier(hi) >= acceptance.quality_discard_multiplier(lo)
    assert acceptance.quality_graft_factor(hi) <= acceptance.quality_graft_factor(lo)
    assert acceptance.discard_probability(OrganType.Kidney, 2.0, hi) >= \
           acceptance.discard_probability(OrganType.Kidney, 2.0, lo)
    assert acceptance.graft_survival_factor(2.0, hi) <= acceptance.graft_survival_factor(2.0, lo)


@given(seed=st.integers(0, 10_000), n_patients=st.integers(4, 40), n_donors=st.integers(2, 8))
@settings(max_examples=40, deadline=None)
def test_feasibility_is_invariant_to_wait_list_order(seed, n_patients, n_donors):
    rng = random.Random(seed)
    network = GraphBuilder.graph_builder(8, rng=rng)
    patients = PatientGenerator.generate_patients(network, n_patients, rng)
    organ_list = OrganList()
    OrganGenerator.generate_organs_to_list(network, n_donors, organ_list, rng)

    feasible_ordered = feasible_matches_by_organ(organ_list, WaitList(patients), network)
    shuffled = list(patients)
    rng.shuffle(shuffled)
    feasible_shuffled = feasible_matches_by_organ(organ_list, WaitList(shuffled), network)

    # which patients are feasible for an organ is a property of the pair, not the list order
    for organ in organ_list.organ_list:
        assert {p.patient_id for p, _ in feasible_ordered[organ]} == \
               {p.patient_id for p, _ in feasible_shuffled[organ]}


def _total_score(result, feasibility, scorer) -> float:
    transit = {(organ.organ_id, patient.patient_id): hours
               for organ, pairs in feasibility.items() for patient, hours in pairs}
    return sum(scorer.score(patient, organ, transit[(organ.organ_id, patient.patient_id)])
               for organ, patient in result.matches)


@given(seed=st.integers(0, 10_000), n_patients=st.integers(6, 40), n_donors=st.integers(2, 10))
@settings(max_examples=40, deadline=None)
def test_optimal_matcher_total_score_never_below_greedy(seed, n_patients, n_donors):
    rng = random.Random(seed)
    network = GraphBuilder.graph_builder(8, rng=rng)
    wait_list = WaitList(PatientGenerator.generate_patients(network, n_patients, rng))
    organ_list = OrganList()
    OrganGenerator.generate_organs_to_list(network, n_donors, organ_list, rng)

    scorer = PriorityScore()
    feasibility = feasible_matches_by_organ(organ_list, wait_list, network)
    greedy = GreedyMatcher().allocate(organ_list, wait_list, network, scorer, feasibility)
    optimal = OptimalMatcher().allocate(organ_list, wait_list, network, scorer, feasibility)

    # the maximum-weight assignment can never total less than the greedy heuristic's
    assert _total_score(optimal, feasibility, scorer) >= \
           _total_score(greedy, feasibility, scorer) - 1e-9
