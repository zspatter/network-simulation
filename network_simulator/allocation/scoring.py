"""
Scoring functions used to rank feasible organ/patient matches.
PriorityScore reproduces the project's original single-factor ranking;
AcuityScore ranks by medical acuity (near-term death risk), a "sickest first"
policy; CompositeScore combines several factors - raw priority, acuity, time
already spent on the wait list, and travel cost - inspired by real OPTN/UNOS
allocation, which weighs urgency, waiting time, and geography together.
RealWorldScore goes further: it scores each organ type on its own real
allocation scale (MELD for liver, LAS for lung, etc.) instead of one uniform
formula - see its class docstring.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from network_simulator.compatibility_markers import OrganType
from network_simulator.Organ import Organ
from network_simulator.Patient import Patient


@dataclass
class PriorityScore:
    """Ranks matches purely by the patient's priority attribute (today's original behavior)."""
    name: str = 'priority'

    def score(self, patient: Patient, organ: Organ, transit_hours: float) -> float:
        return float(patient.priority)


@dataclass
class AcuityScore:
    """
    Ranks matches purely by the patient's acuity (near-term death risk) - a
    "sickest first" policy. Because acuity is organ-normalized, this ranks
    coherently across organ types, favoring the acutely dying (high-MELD
    livers, high-status hearts, high-LAS lungs) over dialysis-sustained kidney
    candidates.
    """
    name: str = 'acuity'

    def score(self, patient: Patient, organ: Organ, transit_hours: float) -> float:
        return patient.acuity


@dataclass
class ScoreWeights:
    """Coefficients combined by CompositeScore into a single match value."""
    urgency: float = 1.0  # coefficient on patient.priority
    wait_time: float = 2.0  # coefficient on patient.rounds_waited
    geography: float = -0.5  # coefficient on transit_hours (negative: closer scores higher)
    acuity: float = 0.0  # coefficient on patient.acuity (0..1); default 0 keeps legacy behavior


@dataclass
class CompositeScore:
    """Ranks matches by priority, acuity, time already spent waiting, and travel cost combined."""
    weights: ScoreWeights = field(default_factory=ScoreWeights)
    name: str = 'composite'

    def score(self, patient: Patient, organ: Organ, transit_hours: float) -> float:
        return (self.weights.urgency * patient.priority
                + self.weights.acuity * patient.acuity
                + self.weights.wait_time * patient.rounds_waited
                + self.weights.geography * transit_hours)


# Tiered cPRA sensitization bonus mirroring the real KAS points table: highly sensitized
# candidates (cPRA >=99%) get a large bonus since almost no donor is compatible for them,
# tapering off below that. See network_simulator.clinical.hla for how cpra is computed.
_CPRA_BONUS_TIERS = ((0.99, 50.0), (0.90, 24.0), (0.20, 5.0))

# Modest coefficient on transit_hours representing the "placement efficiency" factor real
# continuous-distribution policy weighs alongside medical urgency - much smaller than
# CompositeScore's geography term, since here geography's primary lever is the hard tier
# constraint a TieredMatcher applies on top (see allocation.matchers.tiered), not the score.
_GEOGRAPHY_EFFICIENCY_WEIGHT = -0.1

# A floor under every organ's native policy points, applied before the geography term.
# Native points can legitimately be 0 (e.g. a freshly-listed, unsensitized kidney
# candidate has 0 wait-time and 0 cPRA points) or, for lung, close to 0 (LAS is drawn
# from a gaussian clamped to [0, 100]). Without a floor those cases could score <=0 once
# the geography penalty is applied, and OptimalMatcher drops any edge with weight <= 0 -
# same reasoning as urgency.ACUITY_FLOOR. 5.0 comfortably exceeds the worst-case geography
# penalty (kidney's 30h viability cap * 0.1 = 3.0, the largest of any organ).
_MIN_POLICY_FLOOR = 5.0


def _kidney_points(patient: Patient) -> float:
    wait_points = float(patient.rounds_waited)
    cpra_points = 0.0
    for threshold, bonus in _CPRA_BONUS_TIERS:
        if patient.cpra >= threshold:
            cpra_points = bonus
            break
    return wait_points + cpra_points


def _liver_points(patient: Patient) -> float:
    return patient.raw_urgency  # MELD, 6-40 - liver ranks by MELD directly


def _heart_points(patient: Patient) -> float:
    return 7.0 - patient.raw_urgency  # status tier 1 (most urgent) .. 6 -> higher = more urgent


def _lung_points(patient: Patient) -> float:
    return patient.raw_urgency  # LAS, 0-100 - already the real UNOS composite lung score


def _fallback_points(patient: Patient) -> float:
    # pancreas/intestine have no native acute scale in this model (see clinical.urgency);
    # fall back to acuity, scaled to a comparable order of magnitude to the other branches
    return patient.acuity * 10.0


_POLICY_POINTS_BY_ORGAN = {
    OrganType.Kidney: _kidney_points,
    OrganType.Liver:  _liver_points,
    OrganType.Heart:  _heart_points,
    OrganType.Lungs:  _lung_points,
}


@dataclass
class RealWorldScore:
    """
    Approximates current OPTN/UNOS allocation policy, organ by organ, instead of one
    uniform formula: kidney (KAS-style wait-time + cPRA sensitization points), liver
    (MELD directly), heart (status tier, inverted so higher = more urgent), lung (LAS
    directly - LAS *is* the real composite lung allocation score). Pancreas/intestine
    have no native acute scale in this model and fall back to acuity.

    Geography enters only as a small continuous "placement efficiency" term here - real
    hard geographic constraints (the legacy Region model, or the current distance-circle
    model) are modeled separately as a matcher-level constraint, not a scoring term - see
    allocation.matchers.tiered.TieredMatcher and allocation.geography. That split is what
    lets the benchmark isolate the constraint's effect: pair this scorer with a plain
    matcher (no constraint) vs. a TieredMatcher (strict adherence) and compare outcomes.
    """
    name: str = 'real_world'

    def score(self, patient: Patient, organ: Organ, transit_hours: float) -> float:
        policy_points_fn = _POLICY_POINTS_BY_ORGAN.get(patient.organ_needed, _fallback_points)
        policy_points = max(_MIN_POLICY_FLOOR, policy_points_fn(patient))
        return policy_points + _GEOGRAPHY_EFFICIENCY_WEIGHT * transit_hours


@dataclass
class ContinuousDistributionScore:
    """
    A "continuous distribution" allocation score: a single weighted sum of point factors -
    medical urgency, waiting time, geographic proximity, and sensitization - with NO hard
    geographic boundary, which is the direction OPTN policy is moving (lung has been fully
    continuous-distribution since March 2023; heart and liver are in progress). Unlike the
    circle/region models (a hard tier constraint applied by TieredMatcher), geography here is
    just one more continuously-weighted term, so an exceptionally sick distant candidate can
    still out-score a marginal local one.

    All factors are placed on a roughly 0-100 scale so the weights are directly comparable.
    The weights are intentionally exposed as fields so a sweep can trace the medical-benefit-
    versus-geography trade-off frontier (see execute/frontier_analysis.py): raising
    proximity_weight keeps organs local (lower transit, less cold-ischemia waste) at the cost
    of skipping sicker faraway candidates.
    """
    medical_weight: float = 1.0        # coefficient on acuity (near-term death risk), 0..1
    wait_weight: float = 0.5           # coefficient on rounds_waited
    proximity_weight: float = 1.0      # coefficient on geographic proximity (closer scores higher)
    sensitization_weight: float = 0.5  # coefficient on cPRA (hard-to-match candidates), 0..1
    name: str = 'continuous_distribution'

    def score(self, patient: Patient, organ: Organ, transit_hours: float) -> float:
        # proximity in (0, 1]: 1 at the door, decaying smoothly with transit - continuous, with
        # no boundary. Every term is scaled onto ~0..100 so the weights are directly comparable.
        proximity = 1.0 / (1.0 + transit_hours)
        return (self.medical_weight * patient.acuity * 100.0
                + self.wait_weight * patient.rounds_waited
                + self.proximity_weight * proximity * 100.0
                + self.sensitization_weight * patient.cpra * 100.0)
