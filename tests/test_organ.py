import network_simulator.Organ as o


def test_move_organ():
    test_organ = o.Organ(organ_type=o.Organ.HEART, blood_type='NA', location=1)

    # tests initial values
    assert test_organ.current_location is 1
    assert test_organ.origin_location is 1
    assert test_organ.viability is 60

    # tests altered values are as expected
    test_organ.move_organ(2, 20)
    assert test_organ.current_location is 2
    assert test_organ.origin_location is 1
    assert test_organ.viability is 40

    # tests whether moving cost can be greater than current viability
    test_organ.move_organ(3, 100)
    assert test_organ.current_location is 2
    assert test_organ.origin_location is 1
    assert test_organ.viability is 40


def test_organ_type_name():
    assert o.Organ.organ_type_name(-1) is None
    assert o.Organ.organ_type_name(0) == 'Heart'
    assert o.Organ.organ_type_name(1) == 'Kidney'
    assert o.Organ.organ_type_name(2) == 'Liver'
    assert o.Organ.organ_type_name(3) == 'Lung'
    assert o.Organ.organ_type_name(4) == 'Pancreas'
    assert o.Organ.organ_type_name(5) == 'Intestines'
    assert o.Organ.organ_type_name(6) is None


def test_blood_type_name():
    assert o.Organ.blood_type_name(-1) is None
    assert o.Organ.blood_type_name(0) == 'O-'
    assert o.Organ.blood_type_name(1) == 'O+'
    assert o.Organ.blood_type_name(2) == 'A-'
    assert o.Organ.blood_type_name(3) == 'A+'
    assert o.Organ.blood_type_name(4) == 'B-'
    assert o.Organ.blood_type_name(5) == 'B+'
    assert o.Organ.blood_type_name(6) == 'AB-'
    assert o.Organ.blood_type_name(7) == 'AB+'
    assert o.Organ.blood_type_name(8) is None


def test_get_viability():
    assert o.Organ.get_viability(o.Organ.HEART) == 60
    assert o.Organ.get_viability(o.Organ.KIDNEY) == 300
    assert o.Organ.get_viability(o.Organ.LIVER) == 120
    assert o.Organ.get_viability(o.Organ.LUNG) == 60
    assert o.Organ.get_viability(o.Organ.PANCREAS) == 120
    assert o.Organ.get_viability(o.Organ.INTESTINE) == 80
