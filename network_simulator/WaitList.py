from __future__ import annotations

import heapq
from itertools import count
from typing import Dict, List, Optional, Tuple

from network_simulator.Organ import Organ
from network_simulator.Patient import Patient

prioritized_patient = Tuple[int, int, Patient]


class WaitList:
    """
    A class that represents the wait list for all patients waiting on
    a donation. This list accepts all patients in need of organs (generic).

    Backed by an insertion-ordered {patient_id: patient} dict, so add, remove, and
    membership are all O(1) while iteration stays in arrival order (which greedy
    tie-breaking depends on). A plain list made remove_patient an O(n) scan - the
    dominant per-round cost once a national-scale wait list grows into the thousands.
    """

    def __init__(self, wait_list: Optional[List[Patient]] = None,
                label: Optional[str] = None) -> None:
        """
        Creates a WaitList object. If no wait_list parameter is provided,
        an empty wait list is created.

        :param list wait_list: optional preexisting patients to seed the list with
        :param str label: label for the list/collection of patients
        """
        self.label: str = label or 'Default list of patients'
        self._patients: Dict[int, Patient] = {}
        if wait_list:
            for patient in wait_list:
                self._patients[patient.patient_id] = patient

    @property
    def wait_list(self) -> List[Patient]:
        """
        Patients on the list, in arrival order. Returns a fresh list each call (the
        backing store is a dict) - callers only ever read it; mutations go through
        add_patient/remove_patient.
        """
        return list(self._patients.values())

    def get_prioritized_patients(self, organ: Organ) -> List[prioritized_patient]:
        """
        Takes an organ as a parameter and searches the
        wait list for matches. All matches are added to a priority queue
        with the patient's priority attribute determining priority (highest
        priority first).

        Patients are stored as (-priority, insertion_order, patient) tuples so the
        queue can be built and drained with the standard library's min-heap
        `heapq` API (public API only - no private `_heapify_max`/`_heappop_max`
        internals). `insertion_order` breaks ties between equal-priority patients
        without relying on `Patient` supporting comparison.

        :param Organ organ: object representing a prospective transplant
        :return: heapq (priority queue) of (-priority, insertion_order, patient)
            tuples with only patients whose needs match that of the parameters;
            pop with heapq.heappop() to get the highest-priority match next
        """
        queue: List[prioritized_patient] = []
        counter = count()

        for patient in self._patients.values():
            if patient.organ_needed == organ.organ_type and \
                    patient.blood_type.is_compatible_recipient(organ.blood_type):
                heapq.heappush(queue, (-patient.priority, next(counter), patient))

        return queue

    def add_patient(self, patient: Patient) -> None:
        """
        Adds a patient to the existing wait list

        :param Patient patient: object to be added
        """
        if isinstance(patient, Patient) and patient.patient_id not in self._patients:
            self._patients[patient.patient_id] = patient
            return
        print('This patient is already in the wait list!')

    def add_patients(self, patients: List[Patient]) -> None:
        for patient in patients:
            self.add_patient(patient)

    def remove_patient(self, patient: Patient) -> None:
        """
        Removes a patient from the existing wait list

        :param Patient patient: object to be removed
        """
        if isinstance(patient, Patient) and patient.patient_id in self._patients:
            del self._patients[patient.patient_id]
            return
        print('This patient isn\'t in the wait list!')

    def increment_wait_times(self) -> None:
        """
        Increments rounds_waited for every patient still on the wait list.
        Intended to be called once per simulation round (see
        execute/benchmark_strategies.py) so time-aware scoring functions
        (e.g. allocation.scoring.CompositeScore) have a real time axis to
        react to.
        """
        for patient in self._patients.values():
            patient.rounds_waited += 1

    def __str__(self) -> str:
        string = ''
        for patient in self._patients.values():
            string += patient.__str__() + '\n'

        return string + '===============================\n'
