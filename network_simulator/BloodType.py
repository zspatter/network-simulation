from network_simulator.CompatibilityMarkers import BloodTypeLetter
from network_simulator.CompatibilityMarkers import BloodTypePolarity


class BloodType:
    def __init__(self, blood_type_letter, blood_type_polarity):
        self.blood_type_letter = blood_type_letter
        self.blood_type_polarity = blood_type_polarity

    def is_compatible_recipient(self, blood_type):
        if self.blood_type_letter.value >= blood_type.blood_type_letter.value \
                and self.blood_type_polarity.value >= blood_type.blood_type_polarity.value:
            return True

        return False

    def is_compatible_donor(self, blood_type):
        if self.blood_type_letter.value <= blood_type.blood_type_letter.value \
                and self.blood_type_polarity.value <= blood_type.blood_type_polarity.value:
            return True

        return False

    def __str__(self):
        polarity = ''

        if self.blood_type_polarity.value is 0:
            polarity = '-'
        elif self.blood_type_polarity.value is 1:
            polarity = '+'

        return f"Blood type: {self.blood_type_letter.name}{polarity}"


# patient_blood_type = BloodType(BloodTypeLetter.A, BloodTypePolarity.NEG)
# print(patient_blood_type)
#
# organ_blood_type = BloodType(BloodTypeLetter.AB, BloodTypePolarity.POS)
# print(organ_blood_type)
#
# print(patient_blood_type.is_compatible_recipient(organ_blood_type))
# print(patient_blood_type.is_compatible_donor(organ_blood_type))
# print(organ_blood_type.is_compatible_donor(patient_blood_type))
# print(organ_blood_type.is_compatible_recipient(patient_blood_type))
