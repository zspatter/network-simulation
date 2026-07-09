"""
GreedyMatcher: processes organs one at a time (the project's original
allocation behavior), assigning each to its highest-scoring still-available
feasible patient. Parameterized by a ScoringFunction so it can rank
candidates by raw priority or by a composite of urgency/wait-time/geography.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Set

from organflow.allocation.base import AllocationResult, ScoringFunction, feasible_match
from organflow.allocation.feasibility import feasible_matches_by_organ
from organflow.Network import Network
from organflow.Organ import Organ
from organflow.OrganList import OrganList
from organflow.Patient import Patient
from organflow.WaitList import WaitList


class GreedyMatcher:
    name = 'greedy'

    def allocate(self, organ_list: OrganList, wait_list: WaitList,
                network: Network, scorer: ScoringFunction,
                feasibility: Optional[Dict[Organ, List[feasible_match]]] = None
                ) -> AllocationResult:
        result = AllocationResult()
        if feasibility is None:
            feasibility = feasible_matches_by_organ(organ_list, wait_list, network)
        claimed_patients: Set[Patient] = set()

        for organ in organ_list.organ_list:
            candidates = [pair for pair in feasibility[organ]
                         if pair[0] not in claimed_patients]
            if not candidates:
                result.unmatched_organs.append(organ)
                continue

            patient, transit_hours = max(
                    candidates, key=lambda pair: scorer.score(pair[0], organ, pair[1]))
            result.matches.append((organ, patient))
            claimed_patients.add(patient)

        return result
