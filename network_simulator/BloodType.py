from __future__ import annotations

from network_simulator.CompatibilityMarkers import BloodTypeLetter, BloodTypePolarity


class BloodType:
    """
    A class representing a given blood type.

    Possible blood types: O-, O+, A-, A+, B-, B+, AB-, AB+
    """

    def __init__(self, blood_type_letter: BloodTypeLetter, blood_type_polarity: BloodTypePolarity):
        self.blood_type_letter: BloodTypeLetter = blood_type_letter
        self.blood_type_polarity: BloodTypePolarity = blood_type_polarity

    def is_compatible_donor(self, blood_type: BloodType):
        """
        Determines if this blood type can donate to the parameter's blood type.
        This simply calls the is_compatible_recipient function on the parameter
        and passes itself as an argument.

        :param BloodType blood_type: blood type of potential recipient
        :return: bool
        """
        return blood_type.is_compatible_recipient(self)

    def is_compatible_recipient(self, blood_type: BloodType):
        """
        Determines if this blood type can receive a donation from the parameter's
        blood type using bitwise operations

        :param BloodTyp blood_type: blood type of potential donor
        :return: bool
        """
        return ((self.blood_type_letter.value | blood_type.blood_type_letter.value)
                == self.blood_type_letter.value) \
               and self.blood_type_polarity.value >= blood_type.blood_type_polarity.value

    def __str__(self):
        """
        Builds a string representing blood type (ex: 'AB+')

        :return: str representing blood type
        """
        polarity = ''

        if self.blood_type_polarity.value is 0:
            polarity = '-'
        elif self.blood_type_polarity.value is 1:
            polarity = '+'

        return f'{self.blood_type_letter.name}{polarity}'

    def __eq__(self, other):
        """
        Rich comparison returns true iff all attributes are equal

        :param BloodType other: other object to compare
        :return: bool
        """
        if isinstance(other, BloodType):
            return self.blood_type_letter.value is other.blood_type_letter.value \
                   and self.blood_type_polarity.value is other.blood_type_letter.value

        return NotImplemented

    def __ne__(self, other):
        """
        Rich comparison returns true if any of the attributes differ

        :param BloodType other: other object to compare
        :return: bool
        """
        if isinstance(other, BloodType):
            return not (self.blood_type_letter.value is other.blood_type_letter.value
                        and self.blood_type_polarity.value is other.blood_type_letter.value)

        return NotImplemented
