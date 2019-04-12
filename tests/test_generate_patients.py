import network_simulator.GeneratePatients as gp
import network_simulator.Network as net
import network_simulator.WaitList as wl


def test_generate_patients():
    test_net = net.Network()
    test_net.add_node(net.Node(1))
    wait_list = wl.WaitList()
    n = 3
    gp.GeneratePatients.generate_patients(graph=test_net, n=n, wait_list=wait_list)

    assert len(wait_list.wait_list) is n
    for patient in wait_list.wait_list:
        assert 0 <= patient.organ_needed <= 5
        assert 0 <= patient.blood_type <= 7
        assert 0 <= patient.priority < 100 + n
        assert patient.location in test_net.nodes()
