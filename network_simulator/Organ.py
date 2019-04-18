from network_simulator.CompatibilityMarkers import OrganType


class Organ:
    """
    A class representing a given organ which is available for transplant.

    Each organ has a name, a unique ID, lifetime (a maximum out of body duration),
    type matching, and a location.
    """
    HEART, KIDNEY, LIVER, LUNG, PANCREAS, INTESTINE = 0, 1, 2, 3, 4, 5
    # organ_types = enum()
    O_NEG, O_POS, A_NEG, A_POS, B_NEG, B_POS, AB_NEG, AB_POS = 0, 1, 2, 3, 4, 5, 6, 7
    organ_count = 0

    def __init__(self, organ_type, blood_type, location, organ_list=None):
        Organ.organ_count = Organ.organ_count + 1
        self.organ_id = Organ.organ_count
        self.organ_type = organ_type
        self.blood_type = blood_type
        self.viability = Organ.get_viability(self.organ_type)
        self.origin_location = location
        self.current_location = location
        self.path = [location]
        if organ_list:
            organ_list.add_organ(self)

    def move_organ(self, new_location, cost, shortest_path):
        """
        This function allows an organ's attributes to be altered to represent it's
        transportation across the network. This is intended to be used with
        Dijkstra.shortest_path (this will be the source of the cost parameter)

        :param int new_location: node id representing the destination location
        :param cost: weight/cost associated with then most efficient path
        :param list shortest_path: transit path taken when moving organ
        """
        if self.viability < cost:
            print('ERROR: organ no longer viable!')
            return
        path, weight = shortest_path
        self.path = path
        self.current_location = new_location
        self.viability -= cost

    @staticmethod
    def get_viability(organ_type):
        """
        Gets viability rating for each organ individually
        
        Viability is represented by hours an organ can be out of body * 10

        :param int organ_type: constant corresponding to an organ type
        :return: int viability rating (used in __init__())
        """
        viability = {Organ.HEART: 60,
                     Organ.KIDNEY: 300,
                     Organ.LIVER: 120,
                     Organ.LUNG: 60,
                     Organ.PANCREAS: 120,
                     Organ.INTESTINE: 80}

        return viability[organ_type]

    def __str__(self):
        """
        Builds an easily readable string representing an organ

        :return: str
        """
        return f'Organ:\n' \
            f'\tOrgan ID: {"{:05d}".format(self.organ_id)}\n' \
            f'\tOrgan type: {OrganType(self.organ_type).name}\n' \
            f'\tBlood type: {self.blood_type}\n' \
            f'\tViability: {self.viability}\n' \
            f'\tOrigin location: {self.origin_location}\n' \
            f'\tCurrent location: {self.current_location}\n' \
            f'\tTransit path: {self.path}\n'
