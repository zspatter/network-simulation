import network_simulator.GenerateOrgans as gO
import network_simulator.Network as net
import network_simulator.OrganList as oL


def test_generate_organs():
    test_net = net.Network()
    test_net.add_node(net.Node(1))
    organ_list = oL.OrganList()
    n = 3
    gO.GenerateOrgans.generate_organs(graph=test_net, n=n, organ_list=organ_list)

    assert len(organ_list.organ_list) <= n * 6

    for organ in organ_list.organ_list:
        assert organ.current_location in test_net.nodes()
        assert 0 <= organ.organ_type <= 5
        assert 0 <= organ.blood_type <= 7