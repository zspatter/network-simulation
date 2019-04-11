import random
import network_simulator.Patient as P


class GeneratePatients:

    @staticmethod
    def generate_patients(graph, n, wait_list):
        """
        Generates n patients to add to wait list with random combinations of
        organ needed, blood type, priority, and location

        :param Network graph: network for patients to be allocated to
        :param int n: number of patients to generate
        :param WaitList wait_list:
        """
        # list of currently active nodes
        nodes = graph.nodes()

        for x in range(n):
            temp = P.Patient(patient_name="generated patient #" + str(x + 1),
                             illness="N/A",
                             organ_needed=random.randrange(6),
                             blood_type=random.randrange(8),
                             priority=random.randrange(100 + n),
                             location=random.choice(nodes),
                             wait_list=wait_list)
