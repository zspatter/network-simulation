import network_simulator.Network as net
import network_simulator.Organ as O
import network_simulator.Patient as P
import network_simulator.Dijkstra as D


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
patient_a = P.Patient(patient_id=1, patient_name='patient a', illness='diabetes',
                      organ_needed=O.Organ.PANCREAS, wait_time=1, location=hospital_j.node_id)
patient_b = P.Patient(patient_id=2, patient_name='patient b', illness='heart trouble',
                      organ_needed=O.Organ.HEART, wait_time=2, location=hospital_i.node_id)
patient_c = P.Patient(patient_id=3, patient_name='patient c', illness='alcoholism',
                      organ_needed=O.Organ.LIVER, wait_time=3, location=hospital_h.node_id)
patient_d = P.Patient(patient_id=4, patient_name='patient d', illness='lung cancer',
                      organ_needed=O.Organ.LUNG, wait_time=4, location=hospital_g.node_id)
patient_e = P.Patient(patient_id=5, patient_name='patient e', illness='diabetes',
                      organ_needed=O.Organ.PANCREAS, wait_time=100, location=hospital_b.node_id)

# harvests a handful of organs (single donor, same source location)
harvest_organ_1 = O.Organ(organ_category=O.Organ.PANCREAS, organ_type='NA',
                          viability=50, location=hospital_a.node_id)
harvest_organ_2 = O.Organ(organ_category=O.Organ.HEART, organ_type='NA',
                          viability=50, location=hospital_a.node_id)
harvest_organ_3 = O.Organ(organ_category=O.Organ.LIVER, organ_type='NA',
                          viability=50, location=hospital_a.node_id)
harvest_organ_4 = O.Organ(organ_category=O.Organ.LUNG, organ_type='NA',
                          viability=50, location=hospital_a.node_id)

# constructs dijkstra instance (only need 1 as all organs share the same source)
dijkstra = D.Dijkstra(hospital_network, harvest_organ_1.origin_location)

path, weight = dijkstra.shortest_path(patient_a.location)
harvest_organ_1.move_organ(patient_a.location, weight)
print(f'Organ: {O.Organ.organ_category_name(harvest_organ_1.organ_category)}'
      f' has been transported from hospital '
      f'{harvest_organ_1.origin_location} to hospital {patient_a.location}.'
      f'\n\tPath taken: {path}'
      f'\n\tThis came with a cost of: {weight}'
      f'\n\tRemaining organ viability is: {harvest_organ_1.viability}\n')

path, weight = dijkstra.shortest_path(patient_b.location)
harvest_organ_2.move_organ(patient_b.location, weight)
print(f'Organ: {O.Organ.organ_category_name(harvest_organ_2.organ_category)}'
      f' has been transported from hospital '
      f'{harvest_organ_2.origin_location} to hospital {patient_b.location}.'
      f'\n\tPath taken: {path}'
      f'\n\tThis came with a cost of: {weight}'
      f'\n\tRemaining organ viability is: {harvest_organ_2.viability}\n')

path, weight = dijkstra.shortest_path(patient_c.location)
harvest_organ_3.move_organ(patient_c.location, weight)
print(f'Organ: {O.Organ.organ_category_name(harvest_organ_3.organ_category)}'
      f' has been transported from hospital '
      f'{harvest_organ_3.origin_location} to hospital {patient_c.location}.'
      f'\n\tPath taken: {path}'
      f'\n\tThis came with a cost of: {weight}'
      f'\n\tRemaining organ viability is: {harvest_organ_3.viability}\n')

path, weight = dijkstra.shortest_path(patient_d.location)
harvest_organ_4.move_organ(patient_d.location, weight)
print(f'Organ: {O.Organ.organ_category_name(harvest_organ_4.organ_category)}'
      f' has been transported from hospital '
      f'{harvest_organ_4.origin_location} to hospital {patient_d.location}.'
      f'\n\tPath taken: {path}'
      f'\n\tThis came with a cost of: {weight}'
      f'\n\tRemaining organ viability is: {harvest_organ_4.viability}\n')
