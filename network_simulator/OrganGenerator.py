import network_simulator.Organ as O
import network_simulator.BloodType as bT
from network_simulator.CompatibilityMarkers import OrganType, BloodTypeLetter, BloodTypePolarity
import random


class OrganGenerator:

    @staticmethod
    def generate_organs(graph, n, organ_list):
        """
        Harvests a random number of organs from n patients. Not all organs are harvested
        to represent organs that are not suitable for donation (health condition, etc

        Generates n patients to add to wait list with random combinations of
        organ needed, blood type, priority, and location

        :param Network graph:
        :param int n:
        :param OrganList organ_list:
        :return:
        """
        # list of currently active nodes
        nodes = graph.nodes()

        # number of patients to harvest from
        for _ in range(n):
            # number of possible organs to harvest
            location_id = random.choice(nodes)
            blood_type = bT.BloodType(BloodTypeLetter.get_blood_type(),
                                      BloodTypePolarity.get_blood_polarity())

            for organ_type in OrganType:
                # determines if organ is suitable for harvest
                if random.randrange(4) is not 0:
                    temp = O.Organ(organ_type=organ_type.value,
                                   blood_type=blood_type,
                                   location=location_id,
                                   organ_list=organ_list)
