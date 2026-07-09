"""
TieredMatcher: wraps a base MatchingAlgorithm (Greedy or Optimal) with a geographic
TierClassifier (see organflow.allocation.geography), running it in ascending-tier
passes so an organ is only offered outside its current tier once no candidate remains
inside it. This mirrors the real "match run" waterfall (offer locally, expand regionally,
then nationally) rather than a single global optimization that treats geography as just
another scoring input - the hard-constraint counterpart to a scorer's soft geography term.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Set

from organflow.allocation.base import (
    AllocationResult,
    MatchingAlgorithm,
    ScoringFunction,
    feasible_match,
)
from organflow.allocation.feasibility import feasible_matches_by_organ
from organflow.allocation.geography import TierClassifier
from organflow.Network import Network
from organflow.Organ import Organ
from organflow.OrganList import OrganList
from organflow.Patient import Patient
from organflow.WaitList import WaitList


class TieredMatcher:
    def __init__(self, base_matcher: MatchingAlgorithm, tier_classifier: TierClassifier) -> None:
        self.base_matcher = base_matcher
        self.tier_classifier = tier_classifier
        self.name = f'{tier_classifier.name}-tiered-{base_matcher.name}'

    def allocate(self, organ_list: OrganList, wait_list: WaitList,
                network: Network, scorer: ScoringFunction,
                feasibility: Optional[Dict[Organ, List[feasible_match]]] = None
                ) -> AllocationResult:
        if feasibility is None:
            feasibility = feasible_matches_by_organ(organ_list, wait_list, network)

        result = AllocationResult()
        remaining_organs: List[Organ] = list(organ_list.organ_list)
        matched_patients: Set[Patient] = set()

        for tier in range(self.tier_classifier.max_tier + 1):
            if not remaining_organs:
                break

            tier_feasibility: Dict[Organ, List[feasible_match]] = {
                organ: [(patient, transit_hours)
                       for patient, transit_hours in feasibility[organ]
                       if patient not in matched_patients
                       and self.tier_classifier.classify(
                               organ, patient, transit_hours, network) <= tier]
                for organ in remaining_organs
            }

            tier_result = self.base_matcher.allocate(
                    OrganList(list(remaining_organs)), wait_list, network, scorer,
                    feasibility=tier_feasibility)

            result.matches.extend(tier_result.matches)
            matched_patients.update(patient for _, patient in tier_result.matches)
            matched_organ_ids = {organ.organ_id for organ, _ in tier_result.matches}
            remaining_organs = [organ for organ in remaining_organs
                               if organ.organ_id not in matched_organ_ids]

        result.unmatched_organs = remaining_organs
        return result
