from __future__ import annotations

import heapq
from typing import List

from network_simulator.Organ import Organ
from network_simulator.Patient import Patient


class WaitList:
    """
    A class that represents the wait list for all patients waiting on
    a donation. This list accepts all patients in need of organs (generic)
    """
    
    def __init__(self, wait_list: List[Patient] = None, label: str = None) -> None:
        """
        Creates a WaitList object. If no wait_list parameter is provided,
        an empty list is created

        :param list wait_list: optional wait_list parameter (if preexisting list exists)
        :param str label: label for the list/collection of patients
        """
        self.wait_list: List[Patient]
        self.label: str
        
        if not wait_list:
            wait_list = list()
        
        if not label:
            label = 'Default list of patients'
        
        self.label = label
        self.wait_list = wait_list
    
    def get_prioritized_patients(self, organ: Organ) -> List[Patient]:
        """
        Takes an organ as a parameter and searches the
        wait list for matches. All matches are added to a priority queue
        with the patient's priority attribute determining priority.

        The heapq is returned after the entire list has been iterated through

        :param Organ organ: object representing a prospective transplant
        :return: heapq (priority queue) with only patients whose needs match that of the parameters
        """
        queue: List[Patient] = []
        
        for patient in self.wait_list:
            if patient.organ_needed is organ.organ_type and \
                    patient.blood_type.is_compatible_recipient(organ.blood_type):
                heapq.heappush(queue, patient)
        
        heapq._heapify_max(queue)
        return queue
    
    def add_patient(self, patient: Patient) -> None:
        """
        Adds a patient to the existing wait list

        :param Patient patient: object to be added
        """
        if isinstance(patient, Patient) and patient not in self.wait_list:
            self.wait_list.append(patient)
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
        if patient in self.wait_list:
            self.wait_list.remove(patient)
            return
        print('This patient is already in the wait list!')
    
    def __str__(self) -> str:
        string = ''
        for patient in self.wait_list:
            string += patient.__str__() + '\n'
        
        return string + '===============================\n'
