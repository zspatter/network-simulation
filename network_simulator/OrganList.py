import random
import network_simulator.Organ as O

class OrganList:
    """
    A class that represents all of the available organs waiting to be
    allocated to compatible recipients. This list accepts all organ types (generic)
    """

    def __init__(self, organ_list=None):
        if organ_list is None:
            organ_list = list()

        self.organ_list = organ_list

    def add_organ(self, organ):
        """
        Adds an organ to the existing organ list

        :param Organ organ: object to be added to the organ list
        """
        self.organ_list.append(organ)

    def remove_organ(self, organ):
        """
        Removes an organ from the existing organ list

        :param Organ organ: object to be removed from the organ list
        """
        self.organ_list.remove(organ)

    def generate_organs(self, graph, harvest_num):
        node_count = len(graph.network_dict)

        # number of patients to harvest from
        for _ in range(harvest_num):
            # number of possible organs to harvest
            for x in range(6):
                # determines if organ is suitable for harvest
                if random.choice([True, False]):
                    temp = O.Organ(organ_type=x, blood_type=random.randint(0, 7),
                                   location=random.randrange(node_count),
                                   organ_list=self)
