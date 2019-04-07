from network_simulator.Patient import Patient as p
import heapq


class WaitList:
    """
    A class that represents the wait list for all patients waiting on
    a donation. This list accepts all patients in need of organs (generic)
    """

    def __init__(self, wait_list=None):
        if wait_list is None:
            wait_list = list()

        self.wait_list = wait_list

    def get_prioritized_patients(self, organ_type, blood_type):
        queue = []
        heapq.heapify(queue)

        for patient in self.wait_list:
            if patient.organ_needed is organ_type and \
                    patient.blood_type_compatibility(blood_type):
                heapq.heappush(queue, patient)

        return queue

    def add_patient(self, patient):
        self.wait_list.append(patient)

    def remove_patient(self, patient):
        self.wait_list.remove(patient)
