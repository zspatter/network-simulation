"""
Scoring functions used to rank feasible organ/patient matches.
PriorityScore reproduces the project's original single-factor ranking;
AcuityScore ranks by medical acuity (near-term death risk), a "sickest first"
policy; CompositeScore combines several factors - raw priority, acuity, time
already spent on the wait list, and travel cost - inspired by real OPTN/UNOS
allocation, which weighs urgency, waiting time, and geography together.
"""
from __future__ import annotations

from dataclasses import dataclass, field

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
