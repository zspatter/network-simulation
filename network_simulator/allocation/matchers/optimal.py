"""
OptimalMatcher: solves one allocation batch as a maximum-weight bipartite
matching (organs vs. patients) rather than assigning organs one at a time,
so a lower-scoring match made early in the batch can't crowd out a
higher-scoring match that would have been available for a later organ.

Uses networkx.algorithms.matching.max_weight_matching (networkx is already
a project dependency, avoiding scipy). maxcardinality=False is required:
feasibility here is sparse (most organ/patient pairs are infeasible), and
this lets an organ or patient with no good match go legitimately unmatched
rather than being forced into a pairing, which is what
scipy.optimize.linear_sum_assignment would require padding tricks to express.
"""
from __future__ import annotations

from typing import Dict, Set, Tuple

import networkx as nx  # type: ignore

from network_simulator.allocation.base import AllocationResult, ScoringFunction
from network_simulator.allocation.feasibility import feasible_matches_by_organ
from network_simulator.Network import Network
from network_simulator.Organ import Organ
from network_simulator.OrganList import OrganList
from network_simulator.Patient import Patient
from network_simulator.WaitList import WaitList

# node identifiers are tagged by kind to keep organ_id/patient_id (each its
# own auto-incrementing counter starting at 1) from colliding in the graph
graph_node = Tuple[str, int]


class OptimalMatcher:
    name = 'optimal'

    def allocate(self, organ_list: OrganList, wait_list: WaitList,
                network: Network, scorer: ScoringFunction) -> AllocationResult:
        result = AllocationResult()
        feasibility = feasible_matches_by_organ(organ_list, wait_list, network)

        graph: nx.Graph = nx.Graph()
        for organ, candidates in feasibility.items():
            organ_node: graph_node = ('organ', organ.organ_id)
            for patient, transit_hours in candidates:
                weight = scorer.score(patient, organ, transit_hours)
                if weight > 0:
                    patient_node: graph_node = ('patient', patient.patient_id)
                    graph.add_edge(organ_node, patient_node, weight=weight)

        matching = nx.max_weight_matching(graph, maxcardinality=False, weight='weight')

        organ_by_id: Dict[int, Organ] = {organ.organ_id: organ for organ in organ_list.organ_list}
        patient_by_id: Dict[int, Patient] = {patient.patient_id: patient
                                             for patient in wait_list.wait_list}
        matched_organ_ids: Set[int] = set()

        for a, b in matching:
            organ_node, patient_node = (a, b) if a[0] == 'organ' else (b, a)
            organ = organ_by_id[organ_node[1]]
            patient = patient_by_id[patient_node[1]]
            result.matches.append((organ, patient))
            matched_organ_ids.add(organ.organ_id)

        result.unmatched_organs = [organ for organ in organ_list.organ_list
                                   if organ.organ_id not in matched_organ_ids]
        return result
