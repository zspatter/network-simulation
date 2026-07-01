"""
Shared test scenario for the greedy/optimal matcher tests: organ A (O-,
universal donor) is compatible with both patients; organ B (AB+) is only
compatible with the AB+ patient. Processing A first lets a greedy matcher
grab the higher-priority AB+ patient for A, stranding B (its only candidate
is already claimed) - a worse outcome than reserving the AB+ patient for B
and using A for the O- patient instead.
"""
from network_simulator.BloodType import BloodType
from network_simulator.compatibility_markers import BloodTypeLetter, BloodTypePolarity, OrganType
from network_simulator.Network import Network
from network_simulator.Node import Node
from network_simulator.Organ import Organ
from network_simulator.OrganList import OrganList
from network_simulator.Patient import Patient
from network_simulator.WaitList import WaitList

O_NEG = BloodType(BloodTypeLetter.O, BloodTypePolarity.NEG)
AB_POS = BloodType(BloodTypeLetter.AB, BloodTypePolarity.POS)


def build_scenario():
    network = Network({1: Node(1)})

    organ_list = OrganList()
    organ_a = Organ(OrganType.Kidney, O_NEG, location=1, organ_list=organ_list)
    organ_b = Organ(OrganType.Kidney, AB_POS, location=1, organ_list=organ_list)

    wait_list = WaitList()
    patient_x = Patient('x (AB+, high priority)', 'n/a', OrganType.Kidney,
                        AB_POS, 100, 1, wait_list)
    patient_y = Patient('y (O-, low priority)', 'n/a', OrganType.Kidney,
                        O_NEG, 10, 1, wait_list)

    return organ_list, wait_list, network, organ_a, organ_b, patient_x, patient_y
