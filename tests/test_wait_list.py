import heapq

from organflow.BloodType import BloodType
from organflow.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from organflow.Organ import Organ
from organflow.Patient import Patient
from organflow.WaitList import WaitList

o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)
ab_pos = BloodType(BloodTypeLetter.AB, BloodTypePolarity.POS)


def test__init__():
    wait_list = WaitList()
    assert len(wait_list.wait_list) == 0


def test__init__seeds_from_a_preexisting_list_preserving_order():
    p1 = Patient('a', 'n/a', OrganType.Kidney, o_neg, 100, 1)
    p2 = Patient('b', 'n/a', OrganType.Liver, o_neg, 200, 1)
    wait_list = WaitList([p1, p2])

    assert wait_list.wait_list == [p1, p2]  # arrival order preserved
    wait_list.remove_patient(p1)
    assert wait_list.wait_list == [p2]


def test_get_prioritized_patients():
    wait_list = WaitList()
    # O- patient can't receive an AB+ organ - constructed only to prove the queue
    # excludes blood-incompatible patients (highest priority yet absent below)
    Patient('name1', 'illness1', OrganType.Pancreas, o_neg, 500, 1, wait_list)
    patient2 = Patient('name2', 'illness2', OrganType.Pancreas, ab_pos, 200, 1,
                       wait_list)
    patient3 = Patient('name3', 'illness3', OrganType.Pancreas, ab_pos, 300, 1,
                       wait_list)
    patient4 = Patient('name4', 'illness4', OrganType.Pancreas, ab_pos, 400, 1,
                       wait_list)
    organ = Organ(OrganType.Pancreas, ab_pos, 3)
    queue = wait_list.get_prioritized_patients(organ)

    assert len(queue) == 3
    assert heapq.heappop(queue)[2] is patient4
    assert heapq.heappop(queue)[2] is patient3
    assert heapq.heappop(queue)[2] is patient2
    assert len(queue) == 0


def test_add_patient():
    wait_list = WaitList()
    patient = Patient('name1', 'illness1', OrganType.Pancreas, o_neg, 500, 1)
    wait_list.add_patient(patient)

    assert len(wait_list.wait_list) == 1
    wait_list.add_patient(patient)
    assert len(wait_list.wait_list) == 1
    patient = Patient('name1', 'illness1', OrganType.Pancreas, o_neg, 500, 1)
    wait_list.add_patient(patient)
    assert len(wait_list.wait_list) == 2
    wait_list.add_patient(1)
    assert len(wait_list.wait_list) == 2


def test_add_patients():
    wait_list = WaitList()
    assert len(wait_list.wait_list) == 0

    patients = list()
    patients.append(Patient('name', 'N/A', OrganType.random_organ_type(), o_neg, 150, 1))
    patients.append(Patient('name', 'N/A', OrganType.random_organ_type(), o_neg, 150, 1))
    patients.append(Patient('name', 'N/A', OrganType.random_organ_type(), o_neg, 150, 1))
    wait_list.add_patients(patients)
    assert len(wait_list.wait_list) == 3

    for patient in patients:
        assert patient in wait_list.wait_list


def test_remove_patient():
    wait_list = WaitList()
    patient = Patient('name1', 'illness1', OrganType.Pancreas, o_neg, 500, 1, wait_list)
    wait_list.remove_patient(patient)

    assert len(wait_list.wait_list) == 0
    patient2 = Patient('name1', 'illness1', OrganType.Pancreas, o_neg, 500, 1, wait_list)
    wait_list.remove_patient(patient)
    assert len(wait_list.wait_list) == 1
    wait_list.remove_patient(patient2)
    assert len(wait_list.wait_list) == 0


def test_increment_wait_times():
    wait_list = WaitList()
    patient1 = Patient('name1', 'illness1', OrganType.Pancreas, o_neg, 500, 1, wait_list)
    patient2 = Patient('name2', 'illness2', OrganType.Pancreas, o_neg, 500, 1, wait_list)

    assert patient1.rounds_waited == 0
    assert patient2.rounds_waited == 0

    wait_list.increment_wait_times()
    assert patient1.rounds_waited == 1
    assert patient2.rounds_waited == 1

    wait_list.remove_patient(patient1)
    wait_list.increment_wait_times()
    assert patient1.rounds_waited == 1  # no longer on the list, unaffected
    assert patient2.rounds_waited == 2


def test__str__():
    wait_list = WaitList()
    assert str(wait_list) == '===============================\n'

    patient = Patient('name1', 'illness1', OrganType.Pancreas, o_neg, 500, 1, wait_list)
    text = str(wait_list)
    assert str(patient) in text
    assert text.endswith('===============================\n')
