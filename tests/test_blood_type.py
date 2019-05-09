from network_simulator.BloodType import BloodType
from network_simulator.CompatibilityMarkers import BloodTypeLetter, BloodTypePolarity

o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)
o_pos = BloodType(BloodTypeLetter.O, BloodTypePolarity.POS)
a_neg = BloodType(BloodTypeLetter.A, BloodTypePolarity.NEG)
a_pos = BloodType(BloodTypeLetter.A, BloodTypePolarity.POS)
b_neg = BloodType(BloodTypeLetter.B, BloodTypePolarity.NEG)
b_pos = BloodType(BloodTypeLetter.B, BloodTypePolarity.POS)
ab_neg = BloodType(BloodTypeLetter.AB, BloodTypePolarity.NEG)
ab_pos = BloodType(BloodTypeLetter.AB, BloodTypePolarity.POS)

valid_matches = [(o_neg, o_neg), (o_neg, o_pos), (o_neg, a_neg), (o_neg, a_pos),
                 (o_neg, b_neg), (o_neg, b_pos), (o_neg, ab_neg), (o_neg, ab_pos),
                 (o_pos, o_pos), (o_pos, a_pos), (o_pos, b_pos), (o_pos, ab_pos),
                 (a_neg, a_neg), (a_neg, a_pos), (a_neg, ab_neg), (a_neg, ab_neg),
                 (a_pos, a_pos), (a_pos, ab_pos), (b_neg, b_neg), (b_neg, b_pos),
                 (b_neg, ab_neg), (b_neg, ab_pos), (b_pos, b_pos), (b_pos, ab_pos),
                 (ab_neg, ab_neg), (ab_neg, ab_pos), (ab_pos, ab_pos)]

invalid_matches = [(o_pos, o_neg), (o_pos, a_neg), (o_pos, b_neg), (o_pos, ab_neg),
                   (a_neg, o_neg), (a_neg, o_pos), (a_neg, b_neg), (a_neg, b_pos),
                   (a_pos, o_neg), (a_pos, o_pos), (a_pos, a_neg), (a_pos, b_neg),
                   (a_pos, b_pos), (a_pos, ab_neg), (b_neg, o_neg), (b_neg, o_pos),
                   (b_neg, a_neg), (b_neg, a_pos), (b_pos, o_neg), (b_pos, o_pos),
                   (b_pos, a_neg), (b_pos, a_pos), (b_pos, b_neg), (b_pos, ab_neg),
                   (ab_neg, o_neg), (ab_neg, o_pos), (ab_neg, a_neg), (ab_neg, a_pos),
                   (ab_neg, b_neg), (ab_neg, b_pos), (ab_pos, o_neg), (ab_pos, o_pos),
                   (ab_pos, a_neg), (ab_pos, a_pos), (ab_pos, b_neg), (ab_pos, b_pos),
                   (ab_pos, ab_neg)]


def test_is_compatible_donor():
    for donor, recipient in valid_matches:
        assert donor.is_compatible_donor(recipient)
    
    for donor, recipient in invalid_matches:
        assert not donor.is_compatible_donor(recipient)


def test_is_compatible_recipient():
    for donor, recipient in valid_matches:
        assert recipient.is_compatible_recipient(donor)
    
    for donor, recipient in invalid_matches:
        assert not recipient.is_compatible_recipient(donor)
