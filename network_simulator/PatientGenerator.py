import random
from typing import List

from network_simulator.BloodType import BloodType
from network_simulator.CompatibilityMarkers import OrganType, BloodTypeLetter, BloodTypePolarity
from network_simulator.Network import Network
from network_simulator.Patient import Patient


class PatientGenerator:
    """
    Generates a variable number of patients in need of a transplant.
    The generated patients are distributed randomly across the network
    and are assigned a random blood type and priority value.
    """

    @staticmethod
    def generate_patients(graph: Network, n: int, wait_list: List[Patient]):
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
            temp = Patient(patient_name="generated patient #" + str(x + 1),
                           illness="N/A",
                           organ_needed=OrganType.get_organ_type().value,
                           blood_type=BloodType(BloodTypeLetter.get_blood_type(),
                                                BloodTypePolarity.get_blood_polarity()),
                           priority=random.randrange(100 + n),
                           location=random.choice(nodes),
                           wait_list=wait_list)
