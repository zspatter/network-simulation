import heapq
import random


class WaitList:
    """
    A class that represents the wait list for all patients waiting on
    a donation. This list accepts all patients in need of organs (generic)
    """

    def __init__(self, wait_list=None):
        if wait_list is None:
            wait_list = list()

        self.wait_list = wait_list

    def get_prioritized_patients(self, organ):
        """
        Takes an organ type and blood type as parameters and searches the
        wait list for matches. All matches are added to a priority queue
        with the patient's priority attribute determining priority.

        The heapq is returned after the entire list has been iterated through

        :param Organ organ: object representing a prospective transplant
        :return: heapq (priority queue) with only patients whose needs match that of the parameters
        """
        queue = []

        for patient in self.wait_list:
            if patient.organ_needed is organ.organ_type and \
                    patient.blood_type_compatibility(organ.blood_type):
                heapq.heappush(queue, patient)

        heapq._heapify_max(queue)
        return queue

    def add_patient(self, patient):
        """
        Adds a patient to the existing wait list

        :param Patient patient: object to be added
        """
        self.wait_list.append(patient)

    def remove_patient(self, patient):
        """
        Removes a patient from the existing wait list

        :param Patient patient: object to be removed
        """
        self.wait_list.remove(patient)
