from network_simulator.CompatibilityMarkers import BloodTypeLetter


class BloodType:
    def __init__(self, blood_type_letter, blood_type_polarity):
        self.blood_type_letter = blood_type_letter
        self.blood_type_polarity = blood_type_polarity

    def is_compatible_recipient(self, blood_type):
        if self.blood_type_letter.value is not BloodTypeLetter.B.value:
            return self.blood_type_letter.value >= blood_type.blood_type_letter.value \
                   and self.blood_type_polarity.value >= blood_type.blood_type_polarity.value
        else:
            if blood_type.blood_type_letter.value in \
                    (BloodTypeLetter.O.value, BloodTypeLetter.B.value):
                return self.blood_type_polarity.value >= blood_type.blood_type_polarity.value

        return False

    def is_compatible_donor(self, blood_type):
        if self.blood_type_letter.value is not BloodTypeLetter.B.value:
            return self.blood_type_letter.value <= blood_type.blood_type_letter.value \
                   and self.blood_type_polarity.value <= blood_type.blood_type_polarity.value
        else:
            if blood_type.blood_type_letter.value in \
                    (BloodTypeLetter.B.value, BloodTypeLetter.AB.value):
                return self.blood_type_polarity <= blood_type.blood_type_polarity.value

        return False

    def __str__(self):
        polarity = ''

        if self.blood_type_polarity.value is 0:
            polarity = '-'
        elif self.blood_type_polarity.value is 1:
            polarity = '+'

        return f'{self.blood_type_letter.name}{polarity}'
