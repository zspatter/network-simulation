from organflow.Network import Network, Node
from organflow.OrganGenerator import OrganGenerator
from organflow.OrganList import OrganList

test_net = Network()
test_net.add_node(Node(1))
n = 3


def test_generate_organs():
    organs = OrganGenerator.generate_organs(graph=test_net, n=n)

    # at most 7 organs per donor: one of each of the 6 types, but kidney yields 2
    assert len(organs) <= n * 7
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


def test_generate_organs_restricts_location_to_eligible_nodes():
    multi_node_net = Network()
    multi_node_net.add_node(Node(1))
    multi_node_net.add_node(Node(2))
    multi_node_net.add_node(Node(3))

    organs = OrganGenerator.generate_organs(graph=multi_node_net, n=10, eligible_nodes=[2])

    assert organs  # n=10 donors virtually guarantees at least one recovered organ
    assert all(organ.current_location == 2 for organ in organs)


def test_generate_organs_to_list_restricts_location_to_eligible_nodes():
    multi_node_net = Network()
    multi_node_net.add_node(Node(1))
    multi_node_net.add_node(Node(2))
    multi_node_net.add_node(Node(3))
    organ_list = OrganList()

    OrganGenerator.generate_organs_to_list(graph=multi_node_net, n=10, organ_list=organ_list,
                                           eligible_nodes=[2])

    assert all(organ.current_location == 2 for organ in organ_list.organ_list)
