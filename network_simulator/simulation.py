import network_simulator.Network as net
import network_simulator.Organ as O
import network_simulator.Patient as P
import network_simulator.Dijkstra as D
import network_simulator.OrganList as OL
import network_simulator.WaitList as WL


# ansi codes to format console output
ANSI_CYAN = "\033[36m"
ANSI_YELLOW = '\033[33;1m'
ANSI_RESET = "\033[0m"

# builds hospitals (represented as nodes)
hospital_a = net.Node(1, 'A',
                      {2: {'weight': 3, 'status': True},
                       3: {'weight': 1, 'status': True},
                       5: {'weight': 4, 'status': True},
                       9: {'weight': 2, 'status': True}})
hospital_b = net.Node(2, 'B',
                      {1: {'weight': 3, 'status': True},
                       4: {'weight': 2, 'status': True},
                       5: {'weight': 3, 'status': True},
                       7: {'weight': 9, 'status': True},
                       8: {'weight': 10, 'status': True},
                       9: {'weight': 4, 'status': True}})
hospital_c = net.Node(3, 'C',
                      {1: {'weight': 1, 'status': True},
                       4: {'weight': 2, 'status': True},
                       6: {'weight': 4, 'status': True},
                       7: {'weight': 3, 'status': True}})
hospital_d = net.Node(4, 'D',
                      {2: {'weight': 2, 'status': True},
                       3: {'weight': 2, 'status': True},
                       6: {'weight': 8, 'status': True},
                       10: {'weight': 4, 'status': True}})
hospital_e = net.Node(5, 'E',
                      {1: {'weight': 4, 'status': True},
                       2: {'weight': 3, 'status': True},
                       8: {'weight': 3, 'status': True},
                       9: {'weight': 4, 'status': True}})
hospital_f = net.Node(6, 'F',
                      {3: {'weight': 4, 'status': True},
                       4: {'weight': 8, 'status': True},
                       9: {'weight': 8, 'status': True},
                       10: {'weight': 2, 'status': True}})
hospital_g = net.Node(7, 'G',
                      {2: {'weight': 9, 'status': True},
                       3: {'weight': 3, 'status': True},
                       8: {'weight': 2, 'status': True},
                       10: {'weight': 5, 'status': True}})
hospital_h = net.Node(8, 'H',
                      {2: {'weight': 10, 'status': True},
                       5: {'weight': 3, 'status': True},
                       7: {'weight': 2, 'status': True},
                       9: {'weight': 4, 'status': True}})
hospital_i = net.Node(9, 'I',
                      {1: {'weight': 2, 'status': True},
                       2: {'weight': 4, 'status': True},
                       5: {'weight': 4, 'status': True},
                       6: {'weight': 8, 'status': True},
                       8: {'weight': 4, 'status': True}})
hospital_j = net.Node(10, 'J',
                      {4: {'weight': 4, 'status': True},
                       6: {'weight': 2, 'status': True},
                       7: {'weight': 5, 'status': True}})

# builds hospital network
hospital_network = net.Network({hospital_a.node_id: hospital_a,
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
patient_a = P.Patient(patient_name='patient a', illness='diabetes',
                      organ_needed=P.Patient.PANCREAS, blood_type=P.Patient.AB_POS,
                      priority=1, location=hospital_j.node_id)
patient_b = P.Patient(patient_name='patient b', illness='heart trouble',
                      organ_needed=P.Patient.HEART, blood_type=P.Patient.AB_POS,
                      priority=2, location=hospital_i.node_id)
patient_c = P.Patient(patient_name='patient c', illness='alcoholism',
                      organ_needed=P.Patient.LIVER, blood_type=P.Patient.AB_POS,
                      priority=3, location=hospital_h.node_id)
patient_d = P.Patient(patient_name='patient d', illness='lung cancer',
                      organ_needed=P.Patient.LUNG, blood_type=P.Patient.AB_POS,
                      priority=4, location=hospital_g.node_id)
patient_e = P.Patient(patient_name='patient e', illness='diabetes',
                      organ_needed=P.Patient.PANCREAS, blood_type=P.Patient.AB_POS,
                      priority=100, location=hospital_b.node_id)

# harvests a handful of organs (single donor, same source location)
harvest_organ_1 = O.Organ(organ_type=O.Organ.PANCREAS, blood_type='NA',
                          viability=50, location=hospital_a.node_id)
harvest_organ_2 = O.Organ(organ_type=O.Organ.HEART, blood_type='NA',
                          viability=50, location=hospital_a.node_id)
harvest_organ_3 = O.Organ(organ_type=O.Organ.LIVER, blood_type='NA',
                          viability=50, location=hospital_a.node_id)
harvest_organ_4 = O.Organ(organ_type=O.Organ.LUNG, blood_type='NA',
                          viability=50, location=hospital_a.node_id)

# constructs dijkstra instance (only need 1 as all organs share the same source)
dijkstra = D.Dijkstra(hospital_network, harvest_organ_1.origin_location)

path, weight = dijkstra.shortest_path(patient_a.location)
harvest_organ_1.move_organ(patient_a.location, weight)
print(f'Organ: {ANSI_CYAN}{O.Organ.organ_type_name(harvest_organ_1.organ_type)}{ANSI_RESET}'
      f' has been transported from hospital '
      f'{ANSI_CYAN}{harvest_organ_1.origin_location}{ANSI_RESET} '
      f'to hospital {ANSI_CYAN}{patient_a.location}{ANSI_RESET} '
      f'for patient: {ANSI_CYAN}{patient_a.patient_name}{ANSI_RESET}.'
      f'\n\tPath taken: {ANSI_YELLOW}{path}{ANSI_RESET}'
      f'\n\tThis came with a cost of: {ANSI_YELLOW}{weight}{ANSI_RESET}'
      f'\n\tRemaining organ viability is: {ANSI_YELLOW}{harvest_organ_1.viability}{ANSI_RESET}\n')

path, weight = dijkstra.shortest_path(patient_b.location)
harvest_organ_2.move_organ(patient_b.location, weight)
print(f'Organ: {ANSI_CYAN}{O.Organ.organ_type_name(harvest_organ_2.organ_type)}{ANSI_RESET}'
      f' has been transported from hospital '
      f'{ANSI_CYAN}{harvest_organ_2.origin_location}{ANSI_RESET} '
      f'to hospital {ANSI_CYAN}{patient_b.location}{ANSI_RESET} '
      f'for patient: {ANSI_CYAN}{patient_b.patient_name}{ANSI_RESET}.'
      f'\n\tPath taken: {ANSI_YELLOW}{path}{ANSI_RESET}'
      f'\n\tThis came with a cost of: {ANSI_YELLOW}{weight}{ANSI_RESET}'
      f'\n\tRemaining organ viability is: {ANSI_YELLOW}{harvest_organ_2.viability}{ANSI_RESET}\n')

path, weight = dijkstra.shortest_path(patient_c.location)
harvest_organ_3.move_organ(patient_c.location, weight)
print(f'Organ: {ANSI_CYAN}{O.Organ.organ_type_name(harvest_organ_3.organ_type)}{ANSI_RESET}'
      f' has been transported from hospital '
      f'{ANSI_CYAN}{harvest_organ_3.origin_location}{ANSI_RESET} '
      f'to hospital {ANSI_CYAN}{patient_c.location}{ANSI_RESET} '
      f'for patient: {ANSI_CYAN}{patient_c.patient_name}{ANSI_RESET}.'
      f'\n\tPath taken: {ANSI_YELLOW}{path}{ANSI_RESET}'
      f'\n\tThis came with a cost of: {ANSI_YELLOW}{weight}{ANSI_RESET}'
      f'\n\tRemaining organ viability is: {ANSI_YELLOW}{harvest_organ_3.viability}{ANSI_RESET}\n')

path, weight = dijkstra.shortest_path(patient_d.location)
harvest_organ_4.move_organ(patient_d.location, weight)
print(f'Organ: {ANSI_CYAN}{O.Organ.organ_type_name(harvest_organ_4.organ_type)}{ANSI_RESET}'
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
wait_list = WL.WaitList()
organ_list = OL.OrganList()

patient_a = P.Patient(patient_name='patient a', illness='diabetes',
                      organ_needed=P.Patient.PANCREAS, blood_type=P.Patient.AB_POS,
                      priority=1, location=hospital_j.node_id, wait_list=wait_list)
patient_b = P.Patient(patient_name='patient b', illness='heart trouble',
                      organ_needed=P.Patient.HEART, blood_type=P.Patient.AB_POS,
                      priority=2, location=hospital_i.node_id, wait_list=wait_list)
patient_c = P.Patient(patient_name='patient c', illness='alcoholism',
                      organ_needed=P.Patient.LIVER, blood_type=P.Patient.AB_POS,
                      priority=3, location=hospital_h.node_id, wait_list=wait_list)
patient_d = P.Patient(patient_name='patient d', illness='lung cancer',
                      organ_needed=P.Patient.LUNG, blood_type=P.Patient.AB_POS,
                      priority=4, location=hospital_g.node_id, wait_list=wait_list)
patient_e = P.Patient(patient_name='patient e', illness='diabetes',
                      organ_needed=P.Patient.PANCREAS, blood_type=P.Patient.AB_POS,
                      priority=100, location=hospital_b.node_id, wait_list=wait_list)

# harvests a handful of organs (single donor, same source location)
harvest_organ_1 = O.Organ(organ_type=O.Organ.PANCREAS, blood_type='NA',
                          viability=50, location=hospital_a.node_id, organ_list=organ_list)
harvest_organ_2 = O.Organ(organ_type=O.Organ.HEART, blood_type='NA',
                          viability=50, location=hospital_a.node_id, organ_list=organ_list)
harvest_organ_3 = O.Organ(organ_type=O.Organ.LIVER, blood_type='NA',
                          viability=50, location=hospital_a.node_id, organ_list=organ_list)
harvest_organ_4 = O.Organ(organ_type=O.Organ.LUNG, blood_type='NA',
                          viability=50, location=hospital_a.node_id, organ_list=organ_list)

priority_patients = wait_list.get_prioritized_patients(P.Patient.PANCREAS, P.Patient.AB_POS)
for x in priority_patients:
    print(x)
