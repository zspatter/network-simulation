class BloodType:
    def __init__(self, blood_type_letter, blood_type_polarity):
        self.blood_type_letter = blood_type_letter
        self.blood_type_polarity = blood_type_polarity

    def is_compatible_donor(self, blood_type):
        """
        Determines if this blood type can donate to the parameter's blood type.
        This simply calls the is_compatible_recipient function on the parameter
        and passes itself as an argument.

        :param BloodType blood_type: blood type of potential recipient
        :return: bool
        """
        return blood_type.is_compatible_recipient(self)

    def is_compatible_recipient(self, blood_type):
        """
        Determines if this blood type can receive a donation from the parameter's
        blood type using bitwise operations

        :param BloodTyp blood_type: blood type of potential donor
        :return: bool
        """
        return ((self.blood_type_letter.value | blood_type.blood_type_letter.value)
                == self.blood_type_letter.value)\
            and self.blood_type_polarity.value >= blood_type.blood_type_polarity.value

    def __str__(self):
        polarity = ''

        if self.blood_type_polarity.value is 0:
            polarity = '-'
        elif self.blood_type_polarity.value is 1:
            polarity = '+'

        return f'{self.blood_type_letter.name}{polarity}'
