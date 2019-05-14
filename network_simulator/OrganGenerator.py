import random
from typing import List

from network_simulator.BloodType import BloodType
from network_simulator.Network import Network
from network_simulator.Organ import Organ
from network_simulator.compatibility_markers import OrganType, BloodTypeLetter, BloodTypePolarity
from network_simulator.OrganList import OrganList


class OrganGenerator:
    """
    Generates organs from a variable number of patients. Each organ has
    a 75% chance of being successfully harvested.

    The harvested organs are distributed randomly across the network 
    (from one harvest to another; all organs harvested from a single
    patient share the same location/blood type)
    """
    
    @staticmethod
    def generate_organs(graph: Network, n: int) -> List[Organ]:
        """
        Harvests a random number of organs from n patients. Not all organs are harvested
        to represent organs that are not suitable for donation (health condition, etc

        Generates n patients to add to wait list with random combinations of
        organ needed, blood type, priority, and location

        :param Network graph:
        :param int n:
        :return:
        """
        
        # list of currently active nodes
        nodes = graph.nodes()
        organs: List[Organ] = list()
        
        # number of patients to harvest from
        for _ in range(n):
            # number of possible organs to harvest
            location_id = random.choice(nodes)
            blood_type = BloodType(BloodTypeLetter.random_blood_type(),
                                   BloodTypePolarity.random_blood_polarity())
            
            for organ_type in OrganType:
                # determines if organ is suitable for harvest
                if random.randrange(4) is not 0:
                    organs.append(Organ(organ_type=organ_type,
                                        blood_type=blood_type,
                                        location=location_id))
        return organs
    
    @staticmethod
    def generate_organs_to_list(graph: Network, n: int, organ_list: OrganList) -> None:
        organ_list.add_organs(OrganGenerator.generate_organs(graph, n))
