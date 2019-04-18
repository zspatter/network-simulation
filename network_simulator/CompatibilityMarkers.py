from enum import Enum
import random


class OrganType(Enum):
    Heart = 0
    Kidney = 1
    Liver = 2
    Lungs = 3
    Pancreas = 4
    Intestines = 5

    @classmethod
    def get_organ_type(cls):
        return random.choice(list(cls.__members__.values()))


class BloodTypeLetter(Enum):
    O = 0
    A = 1
    B = 2
    AB = 3

    @classmethod
    def get_blood_type(cls):
        return random.choice(list(cls.__members__.values()))


class BloodTypePolarity(Enum):
    NEG = 0
    POS = 1

    @classmethod
    def get_blood_polarity(cls):
        return random.choice(list(cls.__members__.values()))

