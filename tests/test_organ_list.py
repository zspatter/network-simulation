from network_simulator.BloodType import BloodType
from network_simulator.Compatibility_markers import OrganType, BloodTypeLetter, BloodTypePolarity
from network_simulator.Organ import Organ
from network_simulator.OrganList import OrganList

o_neg = BloodType(BloodTypeLetter.O.value, BloodTypePolarity.NEG.value)


def test__init__():
    organ_list = OrganList()
    assert len(organ_list.organ_list) is 0


def test_add_organ():
    organ_list = OrganList()
    organ = Organ(OrganType.Pancreas.value, o_neg, 1)
    organ_list.add_organ(organ)
    assert len(organ_list.organ_list) is 1
    assert organ in organ_list.organ_list
    organ_list.add_organ(organ)
    assert len(organ_list.organ_list) is 1
    assert organ in organ_list.organ_list


def test_remove_organ():
    organ_list = OrganList()
    
    organ = Organ(OrganType.Pancreas.value, o_neg, 1, organ_list)
    organ_list.remove_organ(organ)
    assert len(organ_list.organ_list) is 0
    assert organ not in organ_list.organ_list
    organ1 = Organ(OrganType.Pancreas.value, o_neg, 1, organ_list)
    organ_list.remove_organ(organ)
    assert len(organ_list.organ_list) is 1
    assert organ1 in organ_list.organ_list
    organ_list.remove_organ(organ1)
    assert len(organ_list.organ_list) is 0
    assert organ1 not in organ_list.organ_list


def test_empty_list():
    organ_list = OrganList()
    
    organ = Organ(OrganType.Pancreas.value, o_neg, 1, organ_list)
    organ = Organ(OrganType.Pancreas.value, o_neg, 1, organ_list)
    organ = Organ(OrganType.Pancreas.value, o_neg, 1, organ_list)
    assert len(organ_list.organ_list) is 3
    organ_list.empty_list()
    assert len(organ_list.organ_list) is 0
