import network_simulator.Organ as o


def test__init__():
    test_organ1 = o.Organ(organ_type=o.Organ.HEART, blood_type='NA', viability=100, location=1)
    test_organ2 = o.Organ(organ_type=o.Organ.KIDNEY, blood_type='NA', viability=200, location=2)

    assert o.Organ.organ_count is 2

    assert test_organ1.organ_id is 1
    assert test_organ2.organ_id is 2


def test_move_organ():
    test_organ = o.Organ(organ_type=o.Organ.HEART, blood_type='NA', viability=100, location=1)

    # tests initial values
    assert test_organ.current_location is 1
    assert test_organ.origin_location is 1
    assert test_organ.viability is 100

    # tests altered values are as expected
    test_organ.move_organ(2, 50)
    assert test_organ.current_location is 2
    assert test_organ.origin_location is 1
    assert test_organ.viability is 50

    # tests whether moving cost can be greater than current viability
    test_organ.move_organ(3, 100)
    assert test_organ.current_location is 2
    assert test_organ.origin_location is 1
    assert test_organ.viability is 50


def test_organ_category_name():
    assert o.Organ.organ_category_name(-1) is None
    assert o.Organ.organ_category_name(0) is 'Heart'
    assert o.Organ.organ_category_name(1) is 'Kidney'
    assert o.Organ.organ_category_name(2) is 'Liver'
    assert o.Organ.organ_category_name(3) is 'Lung'
    assert o.Organ.organ_category_name(4) is 'Pancreas'
    assert o.Organ.organ_category_name(5) is 'Intestines'
    assert o.Organ.organ_category_name(6) is 'Thymus'
    assert o.Organ.organ_category_name(7) is None


