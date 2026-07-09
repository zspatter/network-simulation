from organflow.BloodType import BloodType
from organflow.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from organflow.Organ import Organ
from organflow.OrganList import OrganList

o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)


def test__init__():
    organ_list = OrganList()
    assert len(organ_list.organ_list) == 0
    assert organ_list.label == 'Default list of organs'


def test_add_organ():
    organ_list = OrganList()
    organ = Organ(OrganType.Pancreas, o_neg, 1)
    organ_list.add_organ(organ)
    assert len(organ_list.organ_list) == 1
    assert organ in organ_list.organ_list
    organ_list.add_organ(organ)
    assert len(organ_list.organ_list) == 1
    assert organ in organ_list.organ_list
    organ_list.add_organ(1)
    assert len(organ_list.organ_list) == 1


def test_add_organs():
    organ_list = OrganList()
    assert len(organ_list.organ_list) == 0

    organs = list()
    organs.append(Organ(OrganType.random_organ_type(), o_neg, 1))
    organs.append(Organ(OrganType.random_organ_type(), o_neg, 1))
    organs.append(Organ(OrganType.random_organ_type(), o_neg, 1))
    organ_list.add_organs(organs)
    assert len(organ_list.organ_list) == 3

    for organ in organs:
        assert organ in organ_list.organ_list


def test_remove_organ():
    organ_list = OrganList()

    organ = Organ(OrganType.Pancreas, o_neg, 1)
    organ_list.remove_organ(organ)
    assert len(organ_list.organ_list) == 0
    assert organ not in organ_list.organ_list
    organ1 = Organ(OrganType.Pancreas, o_neg, 1, organ_list)
    organ_list.remove_organ(organ)
    assert len(organ_list.organ_list) == 1
    assert organ1 in organ_list.organ_list
    organ_list.remove_organ(organ1)
    assert len(organ_list.organ_list) == 0
    assert organ1 not in organ_list.organ_list


def test_empty_list():
    organ_list = OrganList()

    Organ(OrganType.Pancreas, o_neg, 1, organ_list)
    Organ(OrganType.Pancreas, o_neg, 1, organ_list)
    Organ(OrganType.Pancreas, o_neg, 1, organ_list)
    assert len(organ_list.organ_list) == 3
    organ_list.empty_list()
    assert len(organ_list.organ_list) == 0


def test__str__():
    organ_list = OrganList()
    assert str(organ_list) == '===============================\n'

    organ = Organ(OrganType.Pancreas, o_neg, 1, organ_list)
    text = str(organ_list)
    assert str(organ) in text
    assert text.endswith('===============================\n')
