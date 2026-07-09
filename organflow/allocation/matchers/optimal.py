"""
OptimalMatcher: solves one allocation batch as a maximum-weight bipartite matching (organs vs.
patients) rather than assigning organs one at a time, so a lower-scoring match made early in the
batch can't crowd out a higher-scoring match that would have been available for a later organ.

Solves one scipy.optimize.linear_sum_assignment (the Hungarian/Jonker-Volgenant algorithm, built
for exactly this rectangular bipartite assignment problem) per organ type, rather than one
global nx.max_weight_matching over every organ:
  1. Organ types never share candidates (a patient only needs one organ type - see
     feasibility.feasible_matches_by_organ), so the global bipartite graph always decomposes
     into independent per-organ-type components anyway; solving them separately is equivalent,
     not an approximation.
  2. At national scale this project was originally built to avoid a scipy dependency by using
     networkx's general-graph max_weight_matching instead - but once a real wait-list backlog
     (e.g. kidney) reaches tens of thousands of candidates, that general-graph algorithm both
     takes minutes and can crash outright (verified directly). scipy's LAP solver handles a
     several-hundred x tens-of-thousands rectangular matrix in well under a second, because it's
     specialized for bipartite assignment rather than general graphs.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
from scipy.optimize import linear_sum_assignment  # type: ignore

from organflow.allocation.base import AllocationResult, ScoringFunction, feasible_match
from organflow.allocation.feasibility import feasible_matches_by_organ
from organflow.compatibility_markers import OrganType
from organflow.Network import Network
from organflow.Organ import Organ
from organflow.OrganList import OrganList
from organflow.Patient import Patient
from organflow.WaitList import WaitList

# Stand-in "no real edge" cost for a (organ, patient) pair with no feasible/positive-weight
# score. linear_sum_assignment always returns exactly min(rows, cols) assignments even over a
# fully-dense matrix, so pairs with no real edge get this deliberately-terrible cost and are
# filtered back out afterward if the rectangular shape forced one to be "assigned" anyway.
_NO_EDGE_COST = -1e9


class OptimalMatcher:
    name = 'optimal'

    def allocate(self, organ_list: OrganList, wait_list: WaitList,
                network: Network, scorer: ScoringFunction,
                feasibility: Optional[Dict[Organ, List[feasible_match]]] = None
                ) -> AllocationResult:
        if feasibility is None:
            feasibility = feasible_matches_by_organ(organ_list, wait_list, network)

        result = AllocationResult()
        matched_organ_ids: Set[int] = set()

        organs_by_type: Dict[OrganType, List[Organ]] = defaultdict(list)
        for organ in organ_list.organ_list:
            organs_by_type[organ.organ_type].append(organ)

        for organs in organs_by_type.values():
            for organ, patient in self._solve_one_organ_type(organs, feasibility, scorer):
                result.matches.append((organ, patient))
                matched_organ_ids.add(organ.organ_id)

        result.unmatched_organs = [organ for organ in organ_list.organ_list
                                   if organ.organ_id not in matched_organ_ids]
        return result

    @staticmethod
    def _solve_one_organ_type(organs: List[Organ],
                              feasibility: Dict[Organ, List[feasible_match]],
                              scorer: ScoringFunction) -> List[Tuple[Organ, Patient]]:
        """
        Solves the assignment problem for one organ type's organs against their combined
        candidate pool. Weights are tracked by (organ_id, patient_id) rather than matrix
        position so a forced rectangular assignment (see _NO_EDGE_COST) can be filtered back
        down to genuinely feasible, positive-weight pairs afterward.
        """
        weight_by_ids: Dict[Tuple[int, int], float] = {}
        candidates: List[Patient] = []
        seen_patient_ids: Set[int] = set()

        for organ in organs:
            for patient, transit_hours in feasibility[organ]:
                weight = scorer.score(patient, organ, transit_hours)
                if weight <= 0:
                    continue
                weight_by_ids[(organ.organ_id, patient.patient_id)] = weight
                if patient.patient_id not in seen_patient_ids:
                    seen_patient_ids.add(patient.patient_id)
                    candidates.append(patient)

        if not candidates:
            return []

        cost_matrix = np.full((len(organs), len(candidates)), _NO_EDGE_COST)
        for i, organ in enumerate(organs):
            for j, patient in enumerate(candidates):
                matrix_weight = weight_by_ids.get((organ.organ_id, patient.patient_id))
                if matrix_weight is not None:
                    cost_matrix[i, j] = matrix_weight

        row_indices, col_indices = linear_sum_assignment(cost_matrix, maximize=True)

        matches = []
        for i, j in zip(row_indices, col_indices):
            organ, patient = organs[i], candidates[j]
            if (organ.organ_id, patient.patient_id) in weight_by_ids:
                matches.append((organ, patient))
        return matches
