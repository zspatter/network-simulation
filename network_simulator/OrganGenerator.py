import random
from typing import List, Optional

from network_simulator.BloodType import BloodType
from network_simulator.Network import Network
from network_simulator.Organ import Organ
from network_simulator.OrganList import OrganList
from network_simulator.compatibility_markers import OrganType, BloodTypeLetter, BloodTypePolarity


class OrganGenerator:
    """
    Generates organs from a variable number of patients. Each organ has
    a 75% chance of being successfully harvested.

    The harvested organs are distributed randomly across the network
    (from one harvest to another; all organs harvested from a single
    patient share the same location/blood type)
    """

    @staticmethod
    def generate_organs(graph: Network, n: int,
                        rng: Optional[random.Random] = None) -> List[Organ]:
        """
        Harvests a random number of organs from n patients. Not all organs are harvested
        to represent organs that are not suitable for donation (health condition, etc

        Generates n patients to add to wait list with random combinations of
        organ needed, blood type, priority, and location

        :param Network graph: network where organs can be generated
        :param int n: number of of bodies to harvest organs from
        :param random.Random rng: optional random source (defaults to the
            shared global random module); pass a seeded instance for
            reproducible generation, e.g. in the benchmark harness
        """

        # list of currently active nodes
        nodes = graph.nodes()
        organs: List[Organ] = list()
        source = rng or random

        # number of patients to harvest from
        for _ in range(n):
            # number of possible organs to harvest
            location_id = source.choice(nodes)
            blood_type = BloodType(BloodTypeLetter.random_blood_type(rng),
                                   BloodTypePolarity.random_blood_polarity(rng))

            for organ_type in OrganType:
                # determines if organ is suitable for harvest
                if source.randrange(4) != 0:
                    organs.append(Organ(organ_type=organ_type,
                                        blood_type=blood_type,
                                        location=location_id))
        return organs

    @staticmethod
    def generate_organs_to_list(graph: Network, n: int, organ_list: OrganList,
                                rng: Optional[random.Random] = None) -> None:
        """
        Generates N organs and adds all generated organs to an OrganList

        :param Network graph: network where organs can be generated
        :param int n: number of bodies to harvest organs from
        :param OrganList organ_list: list of organs to add harvested organs to
        :param random.Random rng: optional random source (defaults to the
            shared global random module); pass a seeded instance for
            reproducible generation, e.g. in the benchmark harness
        """
        organ_list.add_organs(OrganGenerator.generate_organs(graph, n, rng))
