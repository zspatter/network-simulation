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
    Heart: int = 0
    Kidney: int = 1
    Liver: int = 2
    Lungs: int = 3
    Pancreas: int = 4
    Intestines: int = 5
    
    @classmethod
    def random_organ_type(cls) -> OrganType:
        """
        Returns a random OrganType
        
        :return: OrganType
        """
        return random.choice(list(OrganType.__iter__()))


class BloodTypeLetter(Enum):
    """
    This enum contains flags that indicate blood type letter
    """
    O: int = 0
    A: int = 1
    B: int = 2
    AB: int = 3
    
    @classmethod
    def random_blood_type(cls) -> BloodTypeLetter:
        """
        Returns a random BloodTypeLetter
        
        :return: BloodTypeLetter
        """
        return random.choice(list(BloodTypeLetter.__iter__()))


class BloodTypePolarity(Enum):
    """
    This enum contains flags that indicate blood polarity
    """
    NEG: int = 0
    POS: int = 1
    
    @classmethod
    def random_blood_polarity(cls) -> BloodTypePolarity:
        """
        Returns a random BloodTypePolarity

        :return: BloodTypePolarity
        """
        return random.choice(list(BloodTypePolarity.__iter__()))
