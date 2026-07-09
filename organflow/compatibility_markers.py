from __future__ import annotations

import random
from enum import Enum
from typing import Optional


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
    def random_organ_type(cls, rng: Optional[random.Random] = None) -> OrganType:
        """
        Returns a random OrganType

        :param random.Random rng: optional random source (defaults to the
            shared global random module); pass a seeded instance for
            reproducible generation, e.g. in the benchmark harness
        :return: OrganType
        """
        return (rng or random).choice(list(OrganType.__iter__()))


class BloodTypeLetter(Enum):
    """
    This enum contains flags that indicate blood type letter
    """
    O = 0  # noqa: E741 - real blood type letter, not an ambiguous variable name
    A = 1
    B = 2
    AB = 3

    @classmethod
    def random_blood_type(cls, rng: Optional[random.Random] = None) -> BloodTypeLetter:
        """
        Returns a random BloodTypeLetter

        :param random.Random rng: optional random source (defaults to the
            shared global random module); pass a seeded instance for
            reproducible generation, e.g. in the benchmark harness
        :return: BloodTypeLetter
        """
        return (rng or random).choice(list(BloodTypeLetter.__iter__()))


class BloodTypePolarity(Enum):
    """
    This enum contains flags that indicate blood polarity
    """
    NEG = 0
    POS = 1

    @classmethod
    def random_blood_polarity(cls, rng: Optional[random.Random] = None) -> BloodTypePolarity:
        """
        Returns a random BloodTypePolarity

        :param random.Random rng: optional random source (defaults to the
            shared global random module); pass a seeded instance for
            reproducible generation, e.g. in the benchmark harness
        :return: BloodTypePolarity
        """
        return (rng or random).choice(list(BloodTypePolarity.__iter__()))
