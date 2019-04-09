import heapq
import random
import network_simulator.Patient as P
import network_simulator.MatchIdentifier as MI


class WaitList:
    """
    A class that represents the wait list for all patients waiting on
    a donation. This list accepts all patients in need of organs (generic)
    """

    def __init__(self, wait_list=None):
        """
        Creates a WaitList object. If no wait_list parameter is provided,
        an empty list is created

        :param list wait_list: optional wait_list parameter (if preexisting list exists)
        """
        if wait_list is None:
            wait_list = list()

        self.wait_list = wait_list

    def get_prioritized_patients(self, organ):
        """
        Takes an organ as a parameter and searches the
        wait list for matches. All matches are added to a priority queue
        with the patient's priority attribute determining priority.

        The heapq is returned after the entire list has been iterated through

        :param Organ organ: object representing a prospective transplant
        :return: heapq (priority queue) with only patients whose needs match that of the parameters
        """
        queue = []

        for patient in self.wait_list:
            if patient.organ_needed is organ.organ_type and \
                    MI.MatchIdentifier.is_match(patient, organ):
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

    def generate_patients(self, graph, n):
        """
        Generates n patients to add to wait list with random combinations of
        organ needed, blood type, priority, and location

        :param Network graph: network for patients to be allocated to
        :param int n: number of patients to generate
        """
        # list of currently active nodes
        nodes = graph.nodes()

        for x in range(n):
            temp = P.Patient(patient_name="generated patient #" + str(x + 1),
                             illness="N/A",
                             organ_needed=random.randrange(7),
                             blood_type=random.randrange(8),
                             priority=random.randrange(251),
                             location=random.choice(nodes),
                             wait_list=self)
