"""
GreedyMatcher: processes organs one at a time (the project's original
allocation behavior), assigning each to its highest-scoring still-available
feasible patient. Parameterized by a ScoringFunction so it can rank
candidates by raw priority or by a composite of urgency/wait-time/geography.
"""
from __future__ import annotations

from typing import Set

from network_simulator.allocation.base import AllocationResult, ScoringFunction
from network_simulator.allocation.feasibility import feasible_matches_by_organ
from network_simulator.Network import Network
from network_simulator.OrganList import OrganList
from network_simulator.Patient import Patient
from network_simulator.WaitList import WaitList


class GreedyMatcher:
    name = 'greedy'

    def allocate(self, organ_list: OrganList, wait_list: WaitList,
                network: Network, scorer: ScoringFunction) -> AllocationResult:
        result = AllocationResult()
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
