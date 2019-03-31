class Organ:
    """
    A class representing a given organ which is available for transplant.

    Each organ has a name, a unique ID, lifetime (a maximum out of body duration),
    type matching, and a location.
    """
    # heart, kidneys, liver, lungs, pancreas, intestine, and thymus.
    HEART = 1
    KIDNEY = 2
    LIVER = 3
    LUNG = 4
    PANCREAS = 5
    INTESTINE = 6
    THYMUS = 7
    organ_count = 0

    def __init__(self, organ_category, organ_type, viability, location):
        Organ.organ_count = Organ.organ_count + 1
        self.organ_id = Organ.organ_count
        self.organ_category = organ_category
        self.organ_type = organ_type
        self.viability = viability
        self.origin_location = location
        self.current_location = location

    def move_organ(self, new_location, cost):
        if self.viability < cost:
            print('ERROR: organ no longer viable!')
            return

        self.current_location = new_location
        self.viability -= cost

    @staticmethod
    def organ_category_name(n):
        organs = {Organ.HEART: 'Heart',
                  Organ.KIDNEY: 'Kidney',
                  Organ.LIVER: 'Liver',
                  Organ.LUNG: 'Lung',
                  Organ.PANCREAS: 'Pancreas',
                  Organ.INTESTINE: 'Intestines',
                  Organ.THYMUS: 'Thymus'}

        return organs[n]
