from __future__ import annotations

import random
from enum import Enum

"""
These are a collection of enums used to represent organ type and blood type.

These are used to initialize values for various objects throughout the system
"""


class OrganType(Enum):
    """
    This enum contains flags that indicate organ type
    """
    Heart = 0
    Kidney = 1
    Liver = 2
    Lungs = 3
    Pancreas = 4
    Intestines = 5
    
    @classmethod
    def random_organ_type(cls) -> OrganType:
        return random.choice(list(OrganType.__iter__()))


class BloodTypeLetter(Enum):
    """
    This enum contains flags that indicate blood type letter
    """
    O = 0
    A = 1
    B = 2
    AB = 3
    
    @classmethod
    def random_blood_type(cls) -> BloodTypeLetter:
        return random.choice(list(BloodTypeLetter.__iter__()))


class BloodTypePolarity(Enum):
    """
    This enum contains flags that indicate blood polarity
    """
    NEG = 0
    POS = 1
    
    @classmethod
    def random_blood_polarity(cls) -> BloodTypePolarity:
        return random.choice(list(BloodTypePolarity.__iter__()))
