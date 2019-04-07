class Organ:
    """
    A class representing a given organ which is available for transplant.

    Each organ has a name, a unique ID, lifetime (a maximum out of body duration),
    type matching, and a location.
    """
    # heart, kidneys, liver, lungs, pancreas, intestine, and thymus.
    HEART = 0
    KIDNEY = 1
    LIVER = 2
    LUNG = 3
    PANCREAS = 4
    INTESTINE = 5
    THYMUS = 6
    O_NEG = 0
    O_POS = 1
    A_NEG = 2
    A_POS = 3
    B_NEG = 4
    B_POS = 5
    AB_NEG = 6
    AB_POS = 7
    organ_count = 0

    def __init__(self, organ_type, blood_type, viability, location):
        Organ.organ_count = Organ.organ_count + 1
        self.organ_id = Organ.organ_count
        self.organ_type = organ_type
        self.blood_type = blood_type
        self.viability = viability
        self.origin_location = location
        self.current_location = location

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
    def organ_category_name(n):
        """
        Returns the string associated with an organ category int
        This is designed to improve readability with console output

        :param int n: a number between 1-7 (inclusive) as defined with organ constants
        :return: string representing organ (or None if no match found)
        """
        if 0 < n < 8:
            organs = {Organ.HEART: 'Heart',
                      Organ.KIDNEY: 'Kidney',
                      Organ.LIVER: 'Liver',
                      Organ.LUNG: 'Lung',
                      Organ.PANCREAS: 'Pancreas',
                      Organ.INTESTINE: 'Intestines',
                      Organ.THYMUS: 'Thymus'}

            return organs[n]

        return None
