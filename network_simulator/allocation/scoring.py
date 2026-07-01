"""
Scoring functions used to rank feasible organ/patient matches.
PriorityScore reproduces the project's original single-factor ranking;
CompositeScore layers in wait time and geography, inspired by real
OPTN/UNOS allocation policy, which weighs medical urgency, time already
spent on the wait list, and travel cost together rather than urgency alone.
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
class ScoreWeights:
    """Coefficients combined by CompositeScore into a single match value."""
    urgency: float = 1.0  # coefficient on patient.priority
    wait_time: float = 2.0  # coefficient on patient.rounds_waited
    geography: float = -0.5  # coefficient on transit_hours (negative: closer scores higher)


@dataclass
class CompositeScore:
    """Ranks matches by urgency, time already spent waiting, and travel cost combined."""
    weights: ScoreWeights = field(default_factory=ScoreWeights)
    name: str = 'composite'

    def score(self, patient: Patient, organ: Organ, transit_hours: float) -> float:
        return (self.weights.urgency * patient.priority
                + self.weights.wait_time * patient.rounds_waited
                + self.weights.geography * transit_hours)
