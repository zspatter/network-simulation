from network_simulator.Network import Node, Network
from network_simulator.PatientGenerator import PatientGenerator
from network_simulator.WaitList import WaitList

test_net = Network()
test_net.add_node(Node(1))
n = 3


def test_generate_patients():
    patients = PatientGenerator.generate_patients(graph=test_net, n=n)
    assert len(patients) == n

    for patient in patients:
        assert 0 <= patient.organ_needed.value <= 5
        assert 0 <= patient.blood_type.blood_type_letter.value <= 3
        assert 0 <= patient.blood_type.blood_type_polarity.value <= 1
        assert 0 <= patient.priority < 100 + n
        assert patient.location in test_net.nodes()


def test_generate_patients_to_list():
    wait_list = WaitList()
    PatientGenerator.generate_patients_to_list(graph=test_net, n=n, wait_list=wait_list)

    assert len(wait_list.wait_list) is n
    for patient in wait_list.wait_list:
        assert patient.location in test_net.nodes()
        assert 0 <= patient.organ_needed.value <= 5
        assert 0 <= patient.blood_type.blood_type_letter.value <= 3
        assert 0 <= patient.blood_type.blood_type_polarity.value <= 1
        assert 0 <= patient.priority < 100 + n
        assert patient.location in test_net.nodes()
