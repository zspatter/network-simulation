from network_simulator.Network import Node, Network
from network_simulator.PatientGenerator import PatientGenerator
from network_simulator.WaitList import WaitList


def test_generate_patients():
    test_net = Network()
    test_net.add_node(Node(1))
    wait_list = WaitList()
    n = 3
    PatientGenerator.generate_patients(graph=test_net, n=n, wait_list=wait_list)
    
    assert len(wait_list.wait_list) is n
    for patient in wait_list.wait_list:
        assert 0 <= patient.organ_needed <= 5
        assert 0 <= patient.blood_type.blood_type_letter.value <= 3
        assert 0 <= patient.blood_type.blood_type_polarity.value <= 1
        assert 0 <= patient.priority < 100 + n
        assert patient.location in test_net.nodes()
