import network_simulator.BloodType as bT
import network_simulator.Organ as o
import network_simulator.OrganList as oL
from network_simulator.CompatibilityMarkers import OrganType, BloodTypeLetter, BloodTypePolarity

o_neg = bT.BloodType(BloodTypeLetter.O.value, BloodTypePolarity.NEG.value)


def test__init__():
    organ_list = oL.OrganList()
    assert len(organ_list.organ_list) is 0


def test_add_organ():
    organ_list = oL.OrganList()
    organ = o.Organ(OrganType.Pancreas.value, o_neg, 1)
    organ_list.add_organ(organ)
    assert len(organ_list.organ_list) is 1
    assert organ in organ_list.organ_list
    organ_list.add_organ(organ)
    assert len(organ_list.organ_list) is 1
    assert organ in organ_list.organ_list


def test_remove_organ():
    organ_list = oL.OrganList()

    organ = o.Organ(OrganType.Pancreas.value, o_neg, 1, organ_list)
    organ_list.remove_organ(organ)
    assert len(organ_list.organ_list) is 0
    assert organ not in organ_list.organ_list
    organ1 = o.Organ(OrganType.Pancreas.value, o_neg, 1, organ_list)
    organ_list.remove_organ(organ)
    assert len(organ_list.organ_list) is 1
    assert organ1 in organ_list.organ_list
    organ_list.remove_organ(organ1)
    assert len(organ_list.organ_list) is 0
    assert organ1 not in organ_list.organ_list


def test_empty_list():
    organ_list = oL.OrganList()

    organ = o.Organ(OrganType.Pancreas.value, o_neg, 1, organ_list)
    organ = o.Organ(OrganType.Pancreas.value, o_neg, 1, organ_list)
    organ = o.Organ(OrganType.Pancreas.value, o_neg, 1, organ_list)
    assert len(organ_list.organ_list) is 3
    organ_list.empty_list()
    assert len(organ_list.organ_list) is 0
