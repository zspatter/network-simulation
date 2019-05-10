import heapq

from network_simulator.BloodType import BloodType
from network_simulator.compatibility_markers import OrganType, BloodTypeLetter, BloodTypePolarity
from network_simulator.Organ import Organ
from network_simulator.Patient import Patient
from network_simulator.WaitList import WaitList

o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)
ab_pos = BloodType(BloodTypeLetter.AB, BloodTypePolarity.POS)


def test__init__():
    wait_list = WaitList()
    assert len(wait_list.wait_list) is 0


def test_get_prioritized_patients():
    wait_list = WaitList()
    patient1 = Patient('name1', 'illness1', OrganType.Pancreas.value, o_neg, 500, 1,
                       wait_list)
    patient2 = Patient('name2', 'illness2', OrganType.Pancreas.value, ab_pos, 200, 1,
                       wait_list)
    patient3 = Patient('name3', 'illness3', OrganType.Pancreas.value, ab_pos, 300, 1,
                       wait_list)
    patient4 = Patient('name4', 'illness4', OrganType.Pancreas.value, ab_pos, 400, 1,
                       wait_list)
    organ = Organ(OrganType.Pancreas.value, ab_pos, 3)
    queue = wait_list.get_prioritized_patients(organ)
    
    assert len(queue) is 3
    assert heapq._heappop_max(queue) is patient4
    assert heapq._heappop_max(queue) is patient3
    assert heapq._heappop_max(queue) is patient2
    assert len(queue) is 0


def test_add_patient():
    wait_list = WaitList()
    patient = Patient('name1', 'illness1', OrganType.Pancreas.value, o_neg, 500, 1)
    wait_list.add_patient(patient)
    
    assert len(wait_list.wait_list) is 1
    wait_list.add_patient(patient)
    assert len(wait_list.wait_list) is 1
    patient = Patient('name1', 'illness1', OrganType.Pancreas.value, o_neg, 500, 1)
    wait_list.add_patient(patient)
    assert len(wait_list.wait_list) is 2


def test_remove_patient():
    wait_list = WaitList()
    patient = Patient('name1', 'illness1', OrganType.Pancreas.value, o_neg, 500, 1, wait_list)
    wait_list.remove_patient(patient)
    
    assert len(wait_list.wait_list) is 0
    patient2 = Patient('name1', 'illness1', OrganType.Pancreas.value, o_neg, 500, 1, wait_list)
    wait_list.remove_patient(patient)
    assert len(wait_list.wait_list) is 1
    wait_list.remove_patient(patient2)
    assert len(wait_list.wait_list) is 0
