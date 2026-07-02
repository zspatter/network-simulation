"""
Shared interfaces for allocation strategies: a MatchingAlgorithm decides
*which* organ/patient pairs to form, and a ScoringFunction decides *how
good* a given pairing is. A Strategy (see allocation.strategies) pairs one
of each together; the benchmark harness compares strategies by holding one
axis fixed while varying the other.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Tuple

from network_simulator.Network import Network
from network_simulator.Organ import Organ
from network_simulator.OrganList import OrganList
from network_simulator.Patient import Patient
from network_simulator.WaitList import WaitList

feasible_match = Tuple[Patient, float]  # (patient, transit_hours)


class ScoringFunction(Protocol):
    """Assigns a numeric value to a prospective organ/patient match; higher is better."""

    name: str

    def score(self, patient: Patient, organ: Organ, transit_hours: float) -> float:
        ...


@dataclass
class AllocationResult:
    """Outcome of running a MatchingAlgorithm over one allocation batch."""
    matches: List[Tuple[Organ, Patient]] = field(default_factory=list)
    unmatched_organs: List[Organ] = field(default_factory=list)

    def apply(self, wait_list: WaitList, organ_list: OrganList) -> None:
        """
        Removes matched patients from wait_list and empties organ_list (all
        harvested organs are consumed either way - matched, or expired
        before a feasible recipient was found). Matchers themselves are
        side-effect-free so they stay independently testable; callers
        (the CLI, the benchmark harness) apply the result explicitly.
        """
        for _, patient in self.matches:
            wait_list.remove_patient(patient)
        organ_list.empty_list()


class MatchingAlgorithm(Protocol):
    """Decides which feasible organ/patient pairs to form for one allocation batch."""

    name: str

    def allocate(self, organ_list: OrganList, wait_list: WaitList,
                network: Network, scorer: ScoringFunction,
                feasibility: Optional[Dict[Organ, List[feasible_match]]] = None
                ) -> AllocationResult:
        """
        :param feasibility: optional pre-computed {organ: [(patient, transit_hours), ...]}
            (see allocation.feasibility.feasible_matches_by_organ). When provided, used
            as-is instead of being recomputed - lets a caller (e.g. TieredMatcher) restrict
            candidates to a geographic tier without duplicating matching logic.
        """
        ...
