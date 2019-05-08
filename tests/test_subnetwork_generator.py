from network_simulator.BloodType import BloodType
from network_simulator.CompatibilityMarkers import BloodTypeLetter, BloodTypePolarity, OrganType
from network_simulator.Network import Node, Network
from network_simulator.Organ import Organ
from network_simulator.OrganList import OrganList
from network_simulator.Patient import Patient
from network_simulator.SubnetworkGenerator import SubnetworkGenerator
from network_simulator.WaitList import WaitList

node_a = Node(1, 'A',
              {2: {'weight': 1, 'status': True},
               3: {'weight': 2, 'status': True}})
node_b = Node(2, 'B',
              {3: {'weight': 1, 'status': True}})
node_c = Node(3, 'C',
              {1: {'weight': 2, 'status': True}})
node_d = Node(4, 'D')

network = Network({node_a.node_id: node_a,
                   node_b.node_id: node_b,
                   node_c.node_id: node_c,
                   node_d.node_id: node_d})

o_neg = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)
wait_list = WaitList()
organ_list = OrganList()

patient_a = Patient('name1', 'N/A', OrganType.Lungs.value, o_neg, 1, node_a.node_id, wait_list)
patient_b = Patient('name2', 'N/A', OrganType.Kidney.value, o_neg, 1, node_b.node_id, wait_list)

organ_c = Organ(OrganType.Liver.value, o_neg, node_c.node_id, organ_list)
organ_d = Organ(OrganType.Heart.value, o_neg, node_d.node_id, organ_list)


def test_generate_subnetwork():
    patient_network = SubnetworkGenerator.generate_subnetwork(network, wait_list)
    organ_network = SubnetworkGenerator.generate_subnetwork(network, organ_list)

    patient_nodes = patient_network.nodes()
    organ_nodes = organ_network.nodes()

    assert len(network.nodes()) == 4
    assert len(patient_network.nodes()) == 2
    assert len(organ_network.nodes()) == 2
    assert node_a.node_id in patient_nodes
    assert node_b.node_id in patient_nodes
    assert node_c.node_id in organ_nodes
    assert node_d.node_id in organ_nodes

    for node in patient_nodes:
        assert node in network.nodes()

    for node in organ_nodes:
        assert node in network.nodes()
