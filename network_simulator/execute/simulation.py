from network_simulator.BloodType import BloodType
from network_simulator.compatibility_markers import OrganType, BloodTypeLetter, BloodTypePolarity
from network_simulator.Dijkstra import Dijkstra
from network_simulator.GraphBuilder import GraphBuilder
from network_simulator.Network import Network
from network_simulator.Node import Node
from network_simulator.Organ import Organ
from network_simulator.OrganAllocator import OrganAllocator
from network_simulator.OrganList import OrganList
from network_simulator.Patient import Patient
from network_simulator.WaitList import WaitList

# ansi codes to format console output
ANSI_CYAN = "\033[36m"
ANSI_YELLOW = '\033[33;1m'
ANSI_RED = '\033[31;1m'
ANSI_RESET = "\033[0m"

# builds hospitals (represented as nodes)
hospital_a = Node(1, 'A',
                  {2: {'weight': 3, 'status': True},
                   3: {'weight': 1, 'status': True},
                   5: {'weight': 4, 'status': True},
                   9: {'weight': 2, 'status': True}})
hospital_b = Node(2, 'B',
                  {1: {'weight': 3, 'status': True},
                   4: {'weight': 2, 'status': True},
                   5: {'weight': 3, 'status': True},
                   7: {'weight': 9, 'status': True},
                   8: {'weight': 10, 'status': True},
                   9: {'weight': 4, 'status': True}})
hospital_c = Node(3, 'C',
                  {1: {'weight': 1, 'status': True},
                   4: {'weight': 2, 'status': True},
                   6: {'weight': 4, 'status': True},
                   7: {'weight': 3, 'status': True}})
hospital_d = Node(4, 'D',
                  {2:  {'weight': 2, 'status': True},
                   3:  {'weight': 2, 'status': True},
                   6:  {'weight': 8, 'status': True},
                   10: {'weight': 4, 'status': True}})
hospital_e = Node(5, 'E',
                  {1: {'weight': 4, 'status': True},
                   2: {'weight': 3, 'status': True},
                   8: {'weight': 3, 'status': True},
                   9: {'weight': 4, 'status': True}})
hospital_f = Node(6, 'F',
                  {3:  {'weight': 4, 'status': True},
                   4:  {'weight': 8, 'status': True},
                   9:  {'weight': 8, 'status': True},
                   10: {'weight': 2, 'status': True}})
hospital_g = Node(7, 'G',
                  {2:  {'weight': 9, 'status': True},
                   3:  {'weight': 3, 'status': True},
                   8:  {'weight': 2, 'status': True},
                   10: {'weight': 5, 'status': True}})
hospital_h = Node(8, 'H',
                  {2: {'weight': 10, 'status': True},
                   5: {'weight': 3, 'status': True},
                   7: {'weight': 2, 'status': True},
                   9: {'weight': 4, 'status': True}})
hospital_i = Node(9, 'I',
                  {1: {'weight': 2, 'status': True},
                   2: {'weight': 4, 'status': True},
                   5: {'weight': 4, 'status': True},
                   6: {'weight': 8, 'status': True},
                   8: {'weight': 4, 'status': True}})
hospital_j = Node(10, 'J',
                  {4: {'weight': 4, 'status': True},
                   6: {'weight': 2, 'status': True},
                   7: {'weight': 5, 'status': True}})

# builds hospital network
hospital_network = Network({hospital_a.node_id: hospital_a,
                            hospital_b.node_id: hospital_b,
                            hospital_c.node_id: hospital_c,
                            hospital_d.node_id: hospital_d,
                            hospital_e.node_id: hospital_e,
                            hospital_f.node_id: hospital_f,
                            hospital_g.node_id: hospital_g,
                            hospital_h.node_id: hospital_h,
                            hospital_i.node_id: hospital_i,
                            hospital_j.node_id: hospital_j},
                           'Hospital Network')

# creates a handful of patients who need organ (across network)
patient_a = Patient(patient_name='patient a', illness='diabetes',
                    organ_needed=OrganType.Pancreas, blood_type=BloodType(BloodTypeLetter.AB,
                                                                          BloodTypePolarity.POS),
                    priority=1, location=hospital_j.node_id)
patient_b = Patient(patient_name='patient b', illness='heart trouble',
                    organ_needed=OrganType.Heart, blood_type=BloodType(BloodTypeLetter.AB,
                                                                       BloodTypePolarity.POS),
                    priority=2, location=hospital_i.node_id)
patient_c = Patient(patient_name='patient c', illness='alcoholism',
                    organ_needed=OrganType.Liver, blood_type=BloodType(BloodTypeLetter.AB,
                                                                       BloodTypePolarity.POS),
                    priority=3, location=hospital_h.node_id)
patient_d = Patient(patient_name='patient d', illness='lung cancer',
                    organ_needed=OrganType.Lungs, blood_type=BloodType(BloodTypeLetter.AB,
                                                                       BloodTypePolarity.POS),
                    priority=4, location=hospital_g.node_id)
patient_e = Patient(patient_name='patient e', illness='diabetes',
                    organ_needed=OrganType.Pancreas, blood_type=BloodType(BloodTypeLetter.AB,
                                                                          BloodTypePolarity.POS),
                    priority=100, location=hospital_b.node_id)

# harvests a handful of organs (single donor, same source location)
harvest_organ_1 = Organ(organ_type=OrganType.Pancreas.value,
                        blood_type=BloodType(BloodTypeLetter.A,
                                             BloodTypePolarity.NEG),
                        location=hospital_a.node_id)
harvest_organ_2 = Organ(organ_type=OrganType.Heart.value,
                        blood_type=BloodType(BloodTypeLetter.A,
                                             BloodTypePolarity.NEG),
                        location=hospital_a.node_id)
harvest_organ_3 = Organ(organ_type=OrganType.Liver.value,
                        blood_type=BloodType(BloodTypeLetter.A,
                                             BloodTypePolarity.NEG),
                        location=hospital_a.node_id)
harvest_organ_4 = Organ(organ_type=OrganType.Lungs.value,
                        blood_type=BloodType(BloodTypeLetter.A,
                                             BloodTypePolarity.NEG),
                        location=hospital_a.node_id)

# constructs dijkstra instance (only need 1 as all organs share the same source)
dijkstra = Dijkstra(hospital_network, harvest_organ_1.origin_location)

path, weight = dijkstra.shortest_path(patient_a.location)
harvest_organ_1.move_organ(patient_a.location, weight, dijkstra.shortest_path(patient_a.location))
print(f'Organ: {ANSI_CYAN}{harvest_organ_1.organ_type}{ANSI_RESET}'
      f' has been transported from hospital '
      f'{ANSI_CYAN}{harvest_organ_1.origin_location}{ANSI_RESET} '
      f'to hospital {ANSI_CYAN}{patient_a.location}{ANSI_RESET} '
      f'for patient: {ANSI_CYAN}{patient_a.patient_name}{ANSI_RESET}.'
      f'\n\tPath taken: {ANSI_YELLOW}{path}{ANSI_RESET}'
      f'\n\tThis came with a cost of: {ANSI_YELLOW}{weight}{ANSI_RESET}'
      f'\n\tRemaining organ viability is: {ANSI_YELLOW}{harvest_organ_1.viability}{ANSI_RESET}\n')

path, weight = dijkstra.shortest_path(patient_b.location)
harvest_organ_2.move_organ(patient_b.location, weight, dijkstra.shortest_path(patient_b.location))
print(f'Organ: {ANSI_CYAN}{harvest_organ_2.organ_type}{ANSI_RESET}'
      f' has been transported from hospital '
      f'{ANSI_CYAN}{harvest_organ_2.origin_location}{ANSI_RESET} '
      f'to hospital {ANSI_CYAN}{patient_b.location}{ANSI_RESET} '
      f'for patient: {ANSI_CYAN}{patient_b.patient_name}{ANSI_RESET}.'
      f'\n\tPath taken: {ANSI_YELLOW}{path}{ANSI_RESET}'
      f'\n\tThis came with a cost of: {ANSI_YELLOW}{weight}{ANSI_RESET}'
      f'\n\tRemaining organ viability is: {ANSI_YELLOW}{harvest_organ_2.viability}{ANSI_RESET}\n')

path, weight = dijkstra.shortest_path(patient_c.location)
harvest_organ_3.move_organ(patient_c.location, weight, dijkstra.shortest_path(patient_c.location))
print(f'Organ: {ANSI_CYAN}{harvest_organ_3.organ_type}{ANSI_RESET}'
      f' has been transported from hospital '
      f'{ANSI_CYAN}{harvest_organ_3.origin_location}{ANSI_RESET} '
      f'to hospital {ANSI_CYAN}{patient_c.location}{ANSI_RESET} '
      f'for patient: {ANSI_CYAN}{patient_c.patient_name}{ANSI_RESET}.'
      f'\n\tPath taken: {ANSI_YELLOW}{path}{ANSI_RESET}'
      f'\n\tThis came with a cost of: {ANSI_YELLOW}{weight}{ANSI_RESET}'
      f'\n\tRemaining organ viability is: {ANSI_YELLOW}{harvest_organ_3.viability}{ANSI_RESET}\n')

path, weight = dijkstra.shortest_path(patient_d.location)
harvest_organ_4.move_organ(patient_d.location, weight, dijkstra.shortest_path(patient_d.location))
print(f'Organ: {ANSI_CYAN}{harvest_organ_4.organ_type}{ANSI_RESET}'
      f' has been transported from hospital '
      f'{ANSI_CYAN}{harvest_organ_4.origin_location}{ANSI_RESET} '
      f'to hospital {ANSI_CYAN}{patient_d.location}{ANSI_RESET} '
      f'for patient: {ANSI_CYAN}{patient_d.patient_name}{ANSI_RESET}.'
      f'\n\tPath taken: {ANSI_YELLOW}{path}{ANSI_RESET}'
      f'\n\tThis came with a cost of: {ANSI_YELLOW}{weight}{ANSI_RESET}'
      f'\n\tRemaining organ viability is: {ANSI_YELLOW}{harvest_organ_4.viability}{ANSI_RESET}\n')

"""
This section declares the above patients and organs with the optional
list parameters passed (WaitList and OrganList)

This was done to test whether or not the initializers function as desired
with the optional parameters.

Furthermore, this briefly tests the data structures holding patient/organ
information. This also demonstrates how the priority queue functions.
"""
wait_list = WaitList()
organ_list = OrganList()

patient_a = Patient(patient_name='patient a', illness='diabetes',
                    organ_needed=OrganType.Pancreas, blood_type=BloodType(BloodTypeLetter.AB,
                                                                          BloodTypePolarity.POS),
                    priority=1, location=hospital_j.node_id, wait_list=wait_list)
patient_b = Patient(patient_name='patient b', illness='heart trouble',
                    organ_needed=OrganType.Heart, blood_type=BloodType(BloodTypeLetter.AB,
                                                                       BloodTypePolarity.POS),
                    priority=2, location=hospital_i.node_id, wait_list=wait_list)
patient_c = Patient(patient_name='patient c', illness='alcoholism',
                    organ_needed=OrganType.Liver, blood_type=BloodType(BloodTypeLetter.AB,
                                                                       BloodTypePolarity.POS),
                    priority=3, location=hospital_h.node_id, wait_list=wait_list)
patient_d = Patient(patient_name='patient d', illness='lung cancer',
                    organ_needed=OrganType.Lungs, blood_type=BloodType(BloodTypeLetter.AB,
                                                                       BloodTypePolarity.POS),
                    priority=4, location=hospital_g.node_id, wait_list=wait_list)
patient_e = Patient(patient_name='patient e', illness='diabetes',
                    organ_needed=OrganType.Pancreas, blood_type=BloodType(BloodTypeLetter.AB,
                                                                          BloodTypePolarity.POS),
                    priority=100, location=hospital_b.node_id, wait_list=wait_list)

# harvests a handful of organs (single donor, same source location)
harvest_organ_1 = Organ(organ_type=OrganType.Pancreas.value,
                        blood_type=BloodType(BloodTypeLetter.O,
                                             BloodTypePolarity.NEG),
                        location=hospital_a.node_id, organ_list=organ_list)
harvest_organ_2 = Organ(organ_type=OrganType.Heart.value,
                        blood_type=BloodType(BloodTypeLetter.O,
                                             BloodTypePolarity.NEG),
                        location=hospital_a.node_id, organ_list=organ_list)
harvest_organ_3 = Organ(organ_type=OrganType.Liver.value,
                        blood_type=BloodType(BloodTypeLetter.O,
                                             BloodTypePolarity.NEG),
                        location=hospital_a.node_id, organ_list=organ_list)
harvest_organ_4 = Organ(organ_type=OrganType.Lungs.value,
                        blood_type=BloodType(BloodTypeLetter.O,
                                             BloodTypePolarity.NEG),
                        location=hospital_a.node_id, organ_list=organ_list)

# priority_patients = wait_list.get_prioritized_patients(harvest_organ_1)
# for x in priority_patients:
#     print(x)
#
# organ_list.generate_organs(hospital_network, 3)
# for x in organ_list.organ_list:
#     print(x)
#
# wait_list.generate_patients(hospital_network, 5)
# for x in wait_list.wait_list:
#     print(x)

network = GraphBuilder.graph_builder(10)
organ_list.generate_organs(network, 5)
wait_list.generate_patients(network, 50)

print(ANSI_CYAN + 'Organs to be allocated: ' + str(len(organ_list.organ_list)) + ANSI_RESET)
print(ANSI_CYAN + 'Patients on wait list: ' + str(len(wait_list.wait_list)) + ANSI_RESET + '\n')
OrganAllocator.allocate_organs(organ_list, wait_list, network)
print(ANSI_CYAN + '\n\nOrgans to be allocated: ' + str(len(organ_list.organ_list)) + ANSI_RESET)
print(ANSI_CYAN + 'Patients on wait list: ' + str(len(wait_list.wait_list)) + ANSI_RESET)

# graph = GraphBuilder.graph_builder(15)
# organ_list = OrganList()
# oG.OrganGenerator.generate_organs(graph, 10, organ_list)
# print(organ_list)
#
# wait_list = WaitList()
# pG.PatientGenerator.generate_patients(graph, 15, wait_list)
# print(wait_list)
