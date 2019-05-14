from network_simulator.Network import Node, Network
from network_simulator.OrganGenerator import OrganGenerator
from network_simulator.OrganList import OrganList

test_net = Network()
test_net.add_node(Node(1))
n = 3


def test_generate_organs():
    organs = OrganGenerator.generate_organs(graph=test_net, n=n)

    assert len(organs) <= n * 6
    for organ in organs:
        assert organ.current_location in test_net.nodes()
        assert 0 <= organ.organ_type.value <= 5
        assert 0 <= organ.blood_type.blood_type_letter.value <= 3
        assert 0 <= organ.blood_type.blood_type_polarity.value <= 1


def test_generate_organs_to_list():
    organ_list = OrganList()
    OrganGenerator.generate_organs_to_list(graph=test_net, n=n, organ_list=organ_list)

    # assert len(organ_list.organ_list) <= n * 6
    for organ in organ_list.organ_list:
        assert organ.current_location in test_net.nodes()
        assert 0 <= organ.organ_type.value <= 5
        assert 0 <= organ.blood_type.blood_type_letter.value <= 3
        assert 0 <= organ.blood_type.blood_type_polarity.value <= 1
