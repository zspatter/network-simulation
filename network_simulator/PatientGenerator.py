import random
from typing import List

from network_simulator.BloodType import BloodType
from network_simulator.Network import Network
from network_simulator.Patient import Patient
from network_simulator.WaitList import WaitList
from network_simulator.compatibility_markers import OrganType, BloodTypeLetter, BloodTypePolarity


class PatientGenerator:
    """
    Generates a variable number of patients in need of a transplant.
    The generated patients are distributed randomly across the network
    and are assigned a random blood type and priority value.
    """

    @staticmethod
    def generate_patients(graph: Network, n: int) -> List[Patient]:
        """
        Generates n patients to add to wait list with random combinations of
        organ needed, blood type, priority, and location

        :param Network graph: network for patients to be allocated to
        :param int n: number of patients to generate
        """
        # list of currently active nodes
        nodes = graph.node_ids()
        patients: List[Patient] = list()

        for x in range(n):
            patients.append(Patient(patient_name="generated patient #" + str(x + 1),
                                    illness="N/A",
                                    organ_needed=OrganType.random_organ_type(),
                                    blood_type=BloodType(BloodTypeLetter.random_blood_type(),
                                                         BloodTypePolarity.random_blood_polarity()),
                                    priority=random.randrange(100 + n),
                                    location=random.choice(nodes)))
        return patients

    @staticmethod
    def generate_patients_to_list(graph: Network, n: int, wait_list: WaitList) -> None:
        """
        Generates N patients and add all generated patients to a WaitList


        :param Network graph: network where patients can be generated
        :param int n: number of patients to generate
        :param WaitList wait_list: list of patients to add generated patients to
        """
        wait_list.add_patients(PatientGenerator.generate_patients(graph, n))
