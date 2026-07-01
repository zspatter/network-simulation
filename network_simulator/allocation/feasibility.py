"""
Single source of truth for what counts as a feasible organ/patient match:
blood-type + organ-type compatibility, and enough remaining viability after
transit to also complete the transplant procedure
(Organ.get_operation_buffer). Every MatchingAlgorithm builds its candidate
matches from here, so comparing strategies only ever measures differences
in matching/scoring - not differences in what counts as a valid match.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from network_simulator.Dijkstra import Dijkstra
from network_simulator.Network import Network
from network_simulator.Organ import Organ
from network_simulator.OrganList import OrganList
from network_simulator.Patient import Patient
from network_simulator.WaitList import WaitList

feasible_match = Tuple[Patient, float]  # (patient, transit_hours)


def feasible_matches_by_organ(organ_list: OrganList, wait_list: WaitList,
                              network: Network) -> Dict[Organ, List[feasible_match]]:
    """
    For every organ in organ_list, finds every patient on wait_list who is a
    compatible recipient (blood type + organ type) and reachable in time to
    both arrive and complete the transplant procedure:
    organ.viability - transit_hours >= organ.get_operation_buffer().

    Runs one Dijkstra per distinct organ origin location in the batch
    (rather than per organ), since harvested organs frequently share an
    origin.

    :param OrganList organ_list: organs available for transplant
    :param WaitList wait_list: patients in need of a transplant
    :param Network network: hospital network organs/patients are present in
    :return: {organ: [(patient, transit_hours), ...]} - feasibility only,
        callers apply their own preference ranking (e.g. via a ScoringFunction)
    """
    dijkstra_by_origin: Dict[int, Dijkstra] = {}
    matches: Dict[Organ, List[feasible_match]] = {}

    for organ in organ_list.organ_list:
        origin = organ.origin_location
        if origin not in dijkstra_by_origin:
            dijkstra_by_origin[origin] = Dijkstra(network, origin)
        weights = dijkstra_by_origin[origin].weight

        operation_buffer = Organ.get_operation_buffer(organ.organ_type)
        organ_matches: List[feasible_match] = []

        for patient in wait_list.wait_list:
            if patient.organ_needed != organ.organ_type:
                continue
            if not patient.blood_type.is_compatible_recipient(organ.blood_type):
                continue

            transit_hours = weights[patient.location]
            if organ.viability - transit_hours >= operation_buffer:
                organ_matches.append((patient, transit_hours))

        matches[organ] = organ_matches

    return matches
