import heapq

import network_simulator.BloodType as bT
import network_simulator.Organ as o
import network_simulator.Patient as p
import network_simulator.WaitList as wL
from network_simulator.CompatibilityMarkers import OrganType, BloodTypeLetter, BloodTypePolarity

o_neg = bT.BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)
ab_pos = bT.BloodType(BloodTypeLetter.AB, BloodTypePolarity.POS)


def test__init__():
    wait_list = wL.WaitList()
    assert len(wait_list.wait_list) is 0


def test_get_prioritized_patients():
    wait_list = wL.WaitList()
    patient1 = p.Patient('name1', 'illness1', OrganType.Pancreas.value, o_neg, 500, 1,
                         wait_list)
    patient2 = p.Patient('name2', 'illness2', OrganType.Pancreas.value, ab_pos, 200, 1,
                         wait_list)
    patient3 = p.Patient('name3', 'illness3', OrganType.Pancreas.value, ab_pos, 300, 1,
                         wait_list)
    patient4 = p.Patient('name4', 'illness4', OrganType.Pancreas.value, ab_pos, 400, 1,
                         wait_list)
    organ = o.Organ(OrganType.Pancreas.value, ab_pos, 3)
    queue = wait_list.get_prioritized_patients(organ)

    assert len(queue) is 3
    assert heapq._heappop_max(queue) is patient4
    assert heapq._heappop_max(queue) is patient3
    assert heapq._heappop_max(queue) is patient2
    assert len(queue) is 0


def test_add_patient():
    wait_list = wL.WaitList()
    patient = p.Patient('name1', 'illness1', OrganType.Pancreas.value, o_neg, 500, 1)
    wait_list.add_patient(patient)

    assert len(wait_list.wait_list) is 1
    wait_list.add_patient(patient)
    assert len(wait_list.wait_list) is 1
    patient = p.Patient('name1', 'illness1', OrganType.Pancreas.value, o_neg, 500, 1)
    wait_list.add_patient(patient)
    assert len(wait_list.wait_list) is 2


def test_remove_patient():
    wait_list = wL.WaitList()
    patient = p.Patient('name1', 'illness1', OrganType.Pancreas.value, o_neg, 500, 1, wait_list)
    wait_list.remove_patient(patient)

    assert len(wait_list.wait_list) is 0
    patient2 = p.Patient('name1', 'illness1', OrganType.Pancreas.value, o_neg, 500, 1, wait_list)
    wait_list.remove_patient(patient)
    assert len(wait_list.wait_list) is 1
    wait_list.remove_patient(patient2)
    assert len(wait_list.wait_list) is 0
