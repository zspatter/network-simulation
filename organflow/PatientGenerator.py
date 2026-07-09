import random
from typing import List, Optional

from organflow.clinical.frequencies import (
    is_pediatric_arrival,
    random_arrival_organ,
    random_us_blood_type,
)
from organflow.clinical.hla import cpra, patient_unacceptable_antigens
from organflow.clinical.progression import initialize_urgency
from organflow.clinical.size import body_size
from organflow.Network import Network
from organflow.Patient import Patient
from organflow.WaitList import WaitList


class PatientGenerator:
    """
    Generates a variable number of patients in need of a transplant.
    The generated patients are distributed randomly across the network
    and are assigned a random blood type and priority value.

    Organ need and blood type are drawn from real US frequency distributions
    (see organflow.clinical.frequencies) rather than uniformly. Organ
    need follows the wait-list *additions* mix (a flow), not the prevalence
    snapshot (a stock), so arrivals aren't over-weighted toward the long-waiting
    kidney candidates that dominate the standing list - see random_arrival_organ.
    """

    @staticmethod
    def generate_patients(graph: Network, n: int, rng: Optional[random.Random] = None,
                         eligible_nodes: Optional[List[int]] = None) -> List[Patient]:
        """
        Generates n patients to add to wait list with random combinations of
        organ needed, blood type, priority, and location

        :param Network graph: network for patients to be allocated to
        :param int n: number of patients to generate
        :param random.Random rng: optional random source (defaults to the
            shared global random module); pass a seeded instance for
            reproducible generation, e.g. in the benchmark harness
        :param eligible_nodes: optional subset of node ids patients may be located at (defaults
            to every node in `graph`); e.g. on a real hospital network, only nodes that are
            actual transplant hospitals - not Organ Procurement Organizations - should carry
            wait-list patients (see execute.import_hospitals)
        """
        # list of currently active nodes
        nodes = eligible_nodes if eligible_nodes is not None else graph.nodes()
        patients: List[Patient] = list()
        source = rng or random

        for x in range(n):
            unacceptable = patient_unacceptable_antigens(rng)
            organ_needed = random_arrival_organ(rng)
            patient = Patient(patient_name="generated patient #" + str(x + 1),
                              illness="N/A",
                              organ_needed=organ_needed,
                              blood_type=random_us_blood_type(rng),
                              priority=source.randrange(100 + n),
                              location=source.choice(nodes),
                              body_size=body_size(rng),
                              unacceptable_antigens=unacceptable,
                              cpra=cpra(unacceptable),
                              is_pediatric=is_pediatric_arrival(organ_needed, rng))
            initialize_urgency(patient, rng)
            patients.append(patient)
        return patients

    @staticmethod
    def generate_patients_to_list(graph: Network, n: int, wait_list: WaitList,
                                  rng: Optional[random.Random] = None,
                                  eligible_nodes: Optional[List[int]] = None) -> None:
        """
        Generates N patients and add all generated patients to a WaitList


        :param Network graph: network where patients can be generated
        :param int n: number of patients to generate
        :param WaitList wait_list: list of patients to add generated patients to
        :param random.Random rng: optional random source (defaults to the
            shared global random module); pass a seeded instance for
            reproducible generation, e.g. in the benchmark harness
        :param eligible_nodes: optional subset of node ids patients may be located at - see
            generate_patients()
        """
        wait_list.add_patients(
                PatientGenerator.generate_patients(graph, n, rng, eligible_nodes))
