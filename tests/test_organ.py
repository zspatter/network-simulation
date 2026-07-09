from organflow.BloodType import BloodType
from organflow.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from organflow.Organ import Organ

o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)


def test_move_organ():
    test_organ = Organ(organ_type=OrganType.Heart, blood_type=o_neg, location=1)

    # tests initial values
    assert test_organ.current_location == 1
    assert test_organ.origin_location == 1
    assert test_organ.viability == 6.0
    assert test_organ.path == [test_organ.origin_location]

    # tests altered values are as expected
    test_organ.move_organ(2, 2.0, ([1, 2, 3], 200))
    assert test_organ.current_location == 2
    assert test_organ.origin_location == 1
    assert test_organ.viability == 4.0
    assert test_organ.path == [1, 2, 3]

    # tests whether moving cost can be greater than current viability
    test_organ.move_organ(3, 10.0, ([3, 2, 1], 500))
    assert test_organ.current_location == 2
    assert test_organ.origin_location == 1
    assert test_organ.viability == 4.0
    assert test_organ.path == [1, 2, 3]


def test_get_viability():
    assert Organ.get_viability(OrganType.Heart) == 6.0
    assert Organ.get_viability(OrganType.Kidney) == 30.0
    assert Organ.get_viability(OrganType.Liver) == 12.0
    assert Organ.get_viability(OrganType.Lungs) == 6.0
    assert Organ.get_viability(OrganType.Pancreas) == 12.0
    assert Organ.get_viability(OrganType.Intestines) == 8.0


def test_get_operation_buffer():
    # implant-to-reperfusion portion that consumes cold-ischemia time (not full OR time)
    assert Organ.get_operation_buffer(OrganType.Heart) == 1.5
    assert Organ.get_operation_buffer(OrganType.Kidney) == 1.0
    assert Organ.get_operation_buffer(OrganType.Liver) == 2.0
    assert Organ.get_operation_buffer(OrganType.Lungs) == 1.5
    assert Organ.get_operation_buffer(OrganType.Pancreas) == 1.5
    assert Organ.get_operation_buffer(OrganType.Intestines) == 2.0


def test_operation_buffer_leaves_transit_room_within_viability():
    # every organ must leave at least an hour of transit budget, or nothing could
    # ever be transplanted under a realistic transit model
    for organ_type in OrganType:
        budget = Organ.get_viability(organ_type) - Organ.get_operation_buffer(organ_type)
        assert budget >= 1.0


def test__str__():
    test_organ = Organ(organ_type=OrganType.Liver, blood_type=o_neg, location=3)
    text = str(test_organ)

    assert 'Organ' in text
    assert 'Liver' in text
    assert str(o_neg) in text
    assert str(test_organ.viability) in text
    assert 'Origin location: 3' in text
