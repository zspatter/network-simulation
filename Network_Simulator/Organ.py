class Organ:
    """
    A class representing a given organ which is available for transplant.

    Each organ has a name, a unique ID, lifetime (a maximum out of body duration),
    type matching, and a location.
    """
    def __init__(self, organ_name, id, lifetime, organ_type, location):
        self.organ_name = organ_name
        self.id = id
        self.lifetime = lifetime
        self.organ_type = organ_type
        self.location = location
