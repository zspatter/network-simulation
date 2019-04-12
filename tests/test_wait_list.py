import network_simulator.WaitList as wl
import network_simulator.Organ as o
import network_simulator.Patient as p
import network_simulator.Network as net
import heapq


def test__init__():
    wait_list = wl.WaitList()
    assert len(wait_list.wait_list) is 0


def test_get_prioritized_patients():
    wait_list = wl.WaitList()
    patient1 = p.Patient('name1', 'illness1', p.Patient.PANCREAS, p.Patient.O_NEG, 500, 1, wait_list)
    patient2 = p.Patient('name2', 'illness2', p.Patient.PANCREAS, p.Patient.AB_POS, 200, 1, wait_list)
    patient3 = p.Patient('name3', 'illness3', p.Patient.PANCREAS, p.Patient.AB_POS, 300, 1, wait_list)
    patient4 = p.Patient('name4', 'illness4', p.Patient.PANCREAS, p.Patient.AB_POS, 400, 1, wait_list)
    organ = o.Organ(o.Organ.PANCREAS, o.Organ.A_POS, 3)
    queue = wait_list.get_prioritized_patients(organ)

    assert len(queue) is 3
    assert heapq._heappop_max(queue) is patient4
    assert heapq._heappop_max(queue) is patient3
    assert heapq._heappop_max(queue) is patient2
    assert len(queue) is 0


def test_add_patient():
    wait_list = wl.WaitList()
    patient = p.Patient('name1', 'illness1', p.Patient.PANCREAS, p.Patient.O_NEG, 500, 1)
    wait_list.add_patient(patient)
    assert len(wait_list.wait_list) is 1
    wait_list.add_patient(patient)
    assert len(wait_list.wait_list) is 1
    patient = p.Patient('name1', 'illness1', p.Patient.PANCREAS, p.Patient.O_NEG, 500, 1)
    wait_list.add_patient(patient)
    assert len(wait_list.wait_list) is 2


def test_remove_patient():
    wait_list = wl.WaitList()
    patient = p.Patient('name1', 'illness1', p.Patient.PANCREAS, p.Patient.O_NEG, 500, 1, wait_list)
    wait_list.remove_patient(patient)
    assert len(wait_list.wait_list) is 0
    patient2 = p.Patient('name1', 'illness1', p.Patient.PANCREAS, p.Patient.O_NEG, 500, 1, wait_list)
    wait_list.remove_patient(patient)
    assert len(wait_list.wait_list) is 1
    wait_list.remove_patient(patient2)
    assert len(wait_list.wait_list) is 0
