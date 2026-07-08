"""
Single source of truth for what counts as a feasible organ/patient match:
blood-type + organ-type compatibility, and enough remaining viability after
transit to also complete the transplant procedure
(Organ.get_operation_buffer). Every MatchingAlgorithm builds its candidate
matches from here, so comparing strategies only ever measures differences
in matching/scoring - not differences in what counts as a valid match.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple

from network_simulator.BloodType import BloodType
from network_simulator.clinical.gates import GATES_BY_ORGAN
from network_simulator.compatibility_markers import (
    BloodTypeLetter,
    BloodTypePolarity,
    OrganType,
)
from network_simulator.Network import Network
from network_simulator.Organ import Organ
from network_simulator.OrganList import OrganList
from network_simulator.Patient import Patient
from network_simulator.WaitList import WaitList

feasible_match = Tuple[Patient, float]  # (patient, transit_hours)

# A patient is keyed by (organ needed, ABO letter value, Rh polarity value) so a given
# organ only ever scans candidates of the right organ type AND a blood-compatible type,
# instead of the whole wait list. Kidney is ~85% of the list, so blood-type bucketing -
# not just organ-type bucketing - is what keeps the dominant kidney path from rescanning
# every waiting patient for every kidney.
_PatientKey = Tuple[OrganType, int, int]

# Donor (letter, polarity) value pair -> every recipient (letter, polarity) value pair that
# can accept it, precomputed once from BloodType's own compatibility rule so the hot path is
# a dict lookup, never a per-pair ABO/Rh test. Cached lazily; there are only 8 donor types.
_compatible_recipient_keys_cache: Dict[Tuple[int, int], Tuple[Tuple[int, int], ...]] = {}


def _compatible_recipient_keys(donor: BloodType) -> Tuple[Tuple[int, int], ...]:
    """(letter, polarity) value pairs of every blood type that can receive from `donor`."""
    key = (donor.blood_type_letter.value, donor.blood_type_polarity.value)
    cached = _compatible_recipient_keys_cache.get(key)
    if cached is None:
        cached = tuple(
                (letter.value, polarity.value)
                for letter in BloodTypeLetter for polarity in BloodTypePolarity
                if BloodType(letter, polarity).is_compatible_recipient(donor))
        _compatible_recipient_keys_cache[key] = cached
    return cached


def feasible_matches_by_organ(organ_list: OrganList, wait_list: WaitList,
                              network: Network) -> Dict[Organ, List[feasible_match]]:
    """
    For every organ in organ_list, finds every patient on wait_list who is a
    compatible recipient and reachable in time to both arrive and complete the
    transplant procedure. A patient is feasible iff:
      - organ type matches the patient's need,
      - blood type is compatible,
      - organ.viability - transit_hours >= organ.get_operation_buffer(), and
      - every organ-specific gate passes (see clinical.gates.GATES_BY_ORGAN:
        size matching for heart/lung, HLA crossmatch for kidney).

    Transit times come from Network.transit_from (memoized per origin for the
    network's static topology), so the shortest-path/direct-distance work for a
    given origin is done at most once per network rather than once per round.

    :param OrganList organ_list: organs available for transplant
    :param WaitList wait_list: patients in need of a transplant
    :param Network network: hospital network organs/patients are present in
    :return: {organ: [(patient, transit_hours), ...]} - feasibility only,
        callers apply their own preference ranking (e.g. via a ScoringFunction)
    """
    # Index the wait list once per batch by (organ, blood type), tagging each patient with its
    # position so an organ's candidates can be restored to wait-list order (which greedy
    # tie-breaking depends on) after being gathered from several blood-type buckets.
    index: Dict[_PatientKey, List[Tuple[int, Patient]]] = defaultdict(list)
    for position, patient in enumerate(wait_list.wait_list):
        blood_type = patient.blood_type
        index[(patient.organ_needed, blood_type.blood_type_letter.value,
               blood_type.blood_type_polarity.value)].append((position, patient))

    matches: Dict[Organ, List[feasible_match]] = {}

    for organ in organ_list.organ_list:
        weights = network.transit_from(organ.origin_location)

        operation_buffer = Organ.get_operation_buffer(organ.organ_type)
        organ_gates = GATES_BY_ORGAN.get(organ.organ_type, ())

        # organ-type + blood-compatible candidates only, restored to wait-list order
        candidates: List[Tuple[int, Patient]] = []
        for letter_value, polarity_value in _compatible_recipient_keys(organ.blood_type):
            candidates.extend(index.get((organ.organ_type, letter_value, polarity_value), ()))
        candidates.sort(key=lambda item: item[0])

        organ_matches: List[feasible_match] = []
        for _, patient in candidates:
            transit_hours = weights[patient.location]
            if organ.viability - transit_hours < operation_buffer:
                continue

            if not all(gate(organ, patient) for gate in organ_gates):
                continue

            organ_matches.append((patient, transit_hours))

        matches[organ] = organ_matches

    return matches
