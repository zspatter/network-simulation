from enum import Enum


class OrganType(Enum):
    HEART = 0
    KIDNEY = 1
    LIVER = 2
    LUNGS = 3
    PANCREAS = 4
    INTESTINES = 5


class BloodTypeLetter(Enum):
    O = 0
    A = 1
    B = 2
    AB = 3


class BloodTypePolarity(Enum):
    NEG = 0
    POS = 1
