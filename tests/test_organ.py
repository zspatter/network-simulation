from network_simulator.BloodType import BloodType
from network_simulator.Organ import Organ
from network_simulator.compatibility_markers import OrganType, BloodTypeLetter, BloodTypePolarity

o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)


def test_move_organ():
    test_organ = Organ(organ_type=OrganType.Heart, blood_type=o_neg, location=1)

    # tests initial values
    assert test_organ.current_location is 1
    assert test_organ.origin_location is 1
    assert test_organ.viability is 60
    assert test_organ.path == [test_organ.origin_location]

    # tests altered values are as expected
    test_organ.move_organ(2, 20, ([1, 2, 3], 200))
    assert test_organ.current_location is 2
    assert test_organ.origin_location is 1
    assert test_organ.viability is 40
    assert test_organ.path == [1, 2, 3]

    # tests whether moving cost can be greater than current viability
    test_organ.move_organ(3, 100, ([3, 2, 1], 500))
    assert test_organ.current_location is 2
    assert test_organ.origin_location is 1
    assert test_organ.viability is 40
    assert test_organ.path == [1, 2, 3]


def test_get_viability():
    assert Organ.get_viability(OrganType.Heart) == 60
    assert Organ.get_viability(OrganType.Kidney) == 300
    assert Organ.get_viability(OrganType.Liver) == 120
    assert Organ.get_viability(OrganType.Lungs) == 60
    assert Organ.get_viability(OrganType.Pancreas) == 120
    assert Organ.get_viability(OrganType.Intestines) == 80
