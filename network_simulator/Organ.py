

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
        if organ_list:
            organ_list.add_organ(self)

    def move_organ(self, new_location, cost):
        """
        This function allows an organ's attributes to be altered to represent it's
        transportation across the network. This is intended to be used with
        Dijkstra.shortest_path (this will be the source of the cost parameter)

        :param int new_location: node id representing the destination location
        :param cost: weight/cost associated with then most efficient path
        """
        if self.viability < cost:
            print('ERROR: organ no longer viable!')
            return

        self.current_location = new_location
        self.viability -= cost

    @staticmethod
    def organ_type_name(n):
        """
        Returns the string associated with an organ category int
        This is designed to improve readability with console output

        :param int n: a number between 1-7 (inclusive) as defined with organ constants
        :return: string representing organ (or None if no match found)
        """
        if 0 <= n < 6:
            organs = {Organ.HEART: 'Heart',
                      Organ.KIDNEY: 'Kidney',
                      Organ.LIVER: 'Liver',
                      Organ.LUNG: 'Lung',
                      Organ.PANCREAS: 'Pancreas',
                      Organ.INTESTINE: 'Intestines'}

            return organs[n]

        return None

    @staticmethod
    def blood_type_name(n):
        """
        Returns the string associated with a blood type int
        This is designed to improve readability with console output

        :param int n: a number between 0-7 (inclusive) as defined with organ and patient constants
        :return: string representing blood type (or None if no match found)
        """
        if 0 <= n < 8:
            blood_types = {Organ.O_NEG: 'O-',
                           Organ.O_POS: 'O+',
                           Organ.A_NEG: 'A-',
                           Organ.A_POS: 'A+',
                           Organ.B_NEG: 'B-',
                           Organ.B_POS: 'B+',
                           Organ.AB_NEG: 'AB-',
                           Organ.AB_POS: 'AB+'}
            return blood_types[n]
        return None

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
            f'\tOrgan type: {Organ.organ_type_name(self.organ_type)}\n' \
            f'\tBlood type: {Organ.blood_type_name(self.blood_type)}\n' \
            f'\tViability: {self.viability}\n' \
            f'\tOrigin location: {self.origin_location}\n' \
            f'\tCurrent location: {self.current_location}\n'
