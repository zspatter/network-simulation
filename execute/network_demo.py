import time

from network_simulator.ConnectivityChecker import ConnectivityChecker
from network_simulator.Dijkstra import Dijkstra
from network_simulator.GraphBuilder import GraphBuilder
from network_simulator.Network import Network
from network_simulator.Node import Node

# ansi codes to format console output
ANSI_CYAN = "\033[36m"
ANSI_YELLOW = '\033[33;1m'
ANSI_RESET = "\033[0m"

"""
The lines below behave as the main method in Java

Everything below is just to briefly demonstrate/test
the basic functions of our graph/network
"""

# creates 10 individual nodes (hard coded adjacency lists to match)
node_1 = Node(1, 'A',
              {2: {'weight': 3, 'status': True},
               3: {'weight': 1, 'status': True},
               5: {'weight': 4, 'status': True},
               9: {'weight': 2, 'status': True}})
node_2 = Node(2, 'B',
              {1: {'weight': 3, 'status': True},
               4: {'weight': 2, 'status': True},
               5: {'weight': 3, 'status': True},
               7: {'weight': 9, 'status': True},
               8: {'weight': 10, 'status': True},
               9: {'weight': 4, 'status': True}})
node_3 = Node(3, 'C',
              {1: {'weight': 1, 'status': True},
               4: {'weight': 2, 'status': True},
               6: {'weight': 4, 'status': True},
               7: {'weight': 3, 'status': True}})
node_4 = Node(4, 'D',
              {2:  {'weight': 2, 'status': True},
               3:  {'weight': 2, 'status': True},
               6:  {'weight': 8, 'status': True},
               10: {'weight': 4, 'status': True}})
node_5 = Node(5, 'E',
              {1: {'weight': 4, 'status': True},
               2: {'weight': 3, 'status': True},
               8: {'weight': 3, 'status': True},
               9: {'weight': 4, 'status': True}})
node_6 = Node(6, 'F',
              {3:  {'weight': 4, 'status': True},
               4:  {'weight': 8, 'status': True},
               9:  {'weight': 8, 'status': True},
               10: {'weight': 2, 'status': True}})
node_7 = Node(7, 'G',
              {2:  {'weight': 9, 'status': True},
               3:  {'weight': 3, 'status': True},
               8:  {'weight': 2, 'status': True},
               10: {'weight': 5, 'status': True}})
node_8 = Node(8, 'H',
              {2: {'weight': 10, 'status': True},
               5: {'weight': 3, 'status': True},
               7: {'weight': 2, 'status': True},
               9: {'weight': 4, 'status': True}})
node_9 = Node(9, 'I',
              {1: {'weight': 2, 'status': True},
               2: {'weight': 4, 'status': True},
               5: {'weight': 4, 'status': True},
               6: {'weight': 8, 'status': True},
               8: {'weight': 4, 'status': True}})
node_10 = Node(10, 'J',
               {4: {'weight': 4, 'status': True},
                6: {'weight': 2, 'status': True},
                7: {'weight': 5, 'status': True}})

# create a network consisting of the nodes above
network_1 = Network({node_1.node_id:  node_1,
                     node_2.node_id:  node_2,
                     node_3.node_id:  node_3,
                     node_4.node_id:  node_4,
                     node_5.node_id:  node_5,
                     node_6.node_id:  node_6,
                     node_7.node_id:  node_7,
                     node_8.node_id:  node_8,
                     node_9.node_id:  node_9,
                     node_10.node_id: node_10})

# demonstrates __str__() function works
print(network_1)

# demonstrates remove_edge function works
print('\t---REMOVE EDGE---')
network_1.remove_edge(1, 2)
print(network_1)

# demonstrates remove_node function works
print('\t---REMOVE NODE---')
network_1.remove_node(3)
print(network_1)

# demonstrates add edge function works
print('\t---ADD EDGE---')
network_1.add_edge(1, 2, 15)
print(network_1)

# demonstrates the add node function works
print('\t---ADD NODE---')
network_1.add_node(Node(11, 'K',
                        {1:  {'weight': 3, 'status': True},
                         2:  {'weight': 4, 'status': True},
                         10: {'weight': 8, 'status': True}}))
print(network_1)

# demonstrates is_connected() function works
if ConnectivityChecker.is_connected(network_1):
    print("The network is connected!\n")
else:
    print("The network is not connected!\n")

start = time.time_ns()
print('Recursive depth_first_search: ' + str(ConnectivityChecker.is_connected(network_1)))
end = time.time_ns()
print('\telapsed time: ' + str(end - start))

start = time.time_ns()
print('\nIterative depth_first_search: ' + str(ConnectivityChecker.depth_first_search(network_1)))
end = time.time_ns()
print('\telapsed time: ' + str(end - start))

start = time.time_ns()
print(
        '\nIterative breadth_first_search: ' + str(
                ConnectivityChecker.breadth_first_search(network_1)))
end = time.time_ns()
print('\telapsed time: ' + str(end - start) + '\n\n===============================\n')

# creates disconnected network to further test is_connected()
node_a = Node(1, 'A',
              {2: {'weight': 1, 'status': True},
               3: {'weight': 2, 'status': True}})
node_b = Node(2, 'B',
              {3: {'weight': 1, 'status': True}})
node_c = Node(3, 'C',
              {1: {'weight': 2, 'status': True}})
node_d = Node(4, 'D')
disconnected_network = Network({1: node_a,
                                2: node_b,
                                3: node_c,
                                4: node_d})

# prints Disconnected Network and checks if graph is connected
print('\t---DISCONNECTED GRAPH---')
print(disconnected_network)

start = time.time_ns()
print(
        'Recursive depth_first_search: ' + str(
                ConnectivityChecker.is_connected(disconnected_network)))
end = time.time_ns()
print('\telapsed time: ' + str(end - start))

start = time.time_ns()
print('\nIterative depth_first_search: ' + str(
        ConnectivityChecker.depth_first_search(disconnected_network)))
end = time.time_ns()
print('\telapsed time: ' + str(end - start))

start = time.time_ns()
print('\nIterative breadth_first_search: ' + str(
        ConnectivityChecker.breadth_first_search(disconnected_network)))
end = time.time_ns()
print('\telapsed time: ' + str(end - start) + '\n\n===============================\n')

# tests the functionality in __init__ that ensures adjacency lists
# of separate nodes mirror each other (undirected, weighted edges)
init_tester_node1 = Node(1, "A",
                         {2: {'weight': 3, 'status': True},
                          3: {'weight': 5, 'status': True}})
init_tester_node2 = Node(2, "B",
                         {1: {'weight': 2, 'status': True},
                          4: {'weight': 3, 'status': True}})
init_tester_node3 = Node(3, "C",
                         {2: {'weight': 6, 'status': True},
                          4: {'weight': 9, 'status': True}})
init_tester_node4 = Node(4, "D",
                         {3: {'weight': 8, 'status': True},
                          2: {'weight': 4, 'status': True}})
init_tester_node5 = Node(5, "E",
                         {1: {'weight': 1, 'status': True},
                          4: {'weight': 2, 'status': True}})

init_tester = Network({init_tester_node1.node_id: init_tester_node1,
                       init_tester_node2.node_id: init_tester_node2,
                       init_tester_node3.node_id: init_tester_node3,
                       init_tester_node4.node_id: init_tester_node4,
                       init_tester_node5.node_id: init_tester_node5})

print('\t---ADJACENCY LISTS MIRROR TEST---')
print(init_tester)

"""
The following section briefly tests the functions that toggle status
of nodes/edges. These tests show that each condition can be reached from
each of the 4 function. These conditions all behave as desired.
"""

print('\t---MARK NODE INACTIVE TESTS---')
init_tester.mark_node_inactive(1)
init_tester.mark_node_inactive(1)
init_tester.mark_node_inactive(6)

init_tester.mark_node_inactive(6)

print(init_tester)

print('\t---MARK NODE ACTIVE TESTS---')
init_tester.mark_node_active(1)
init_tester.mark_node_active(1)
init_tester.mark_node_active(6)
print(init_tester)

print('\t---MARK EDGE INACTIVE TESTS---')
init_tester.mark_edge_inactive(1, 5)
init_tester.mark_edge_inactive(1, 5)
init_tester.mark_edge_inactive(3, 5)
init_tester.mark_edge_inactive(1, 6)
print(init_tester)

print('\t---MARK EDGE ACTIVE TESTS---')
init_tester.mark_edge_active(1, 5)
init_tester.mark_edge_active(1, 5)
init_tester.mark_node_inactive(3)
init_tester.mark_edge_active(1, 3)
init_tester.mark_edge_active(3, 5)
print(init_tester)

print('\t---BREAK CONNECTIVITY VIA STATUS---')
init_tester.mark_edge_inactive(1, 2)
init_tester.mark_edge_inactive(1, 5)

print('\nDisconnected through inactive edges:')
print('\tRecursive depth_first_search: ' + str(ConnectivityChecker.is_connected(init_tester)))
print('\tIterative depth_first_search: ' + str(ConnectivityChecker.depth_first_search(init_tester)))
print('\tIterative breadth_first_search: ' + str(
        ConnectivityChecker.breadth_first_search(init_tester)) + '\n')

init_tester.mark_node_inactive(1)

print('\nDisconnected node made inactive (reconnecting graph):')
print('\tRecursive depth_first_search: ' + str(ConnectivityChecker.is_connected(init_tester)))
print('\tIterative depth_first_search: ' + str(ConnectivityChecker.depth_first_search(init_tester)))
print('\tIterative breadth_first_search: ' + str(
        ConnectivityChecker.breadth_first_search(init_tester)) + '\n')

# tests the generate_network and generate_adjacency_list functions
generated_network = GraphBuilder.graph_builder(15)
print('\t---GENERATED RANDOM NETWORK---\n')
print(generated_network)

start = time.time_ns()
print('\n\tIterative breadth_first_search: ' + str(
        ConnectivityChecker.breadth_first_search(generated_network)))
end = time.time_ns()
print('\t\telapsed time: ' + str(end - start))

dijkstra = Dijkstra(network_1, 1)

weights, previous = dijkstra.dijkstra(network_1, 1)
print("weights:\n" + str(weights))
print("\nprevious:\n" + str(previous))

node1 = Node(1, "A",
             {2: {'weight': 3, 'status': True},
              3: {'weight': 5, 'status': True},
              6: {'weight': 6, 'status': False}})
node2 = Node(2, "B",
             {1: {'weight': 20, 'status': True},
              4: {'weight': 3, 'status': True}})
node3 = Node(3, "C",
             {2: {'weight': 6, 'status': True},
              4: {'weight': 9, 'status': True}})
node4 = Node(4, "D",
             {3: {'weight': 8, 'status': True},
              2: {'weight': 4, 'status': True}})
node5 = Node(5, "E",
             {1: {'weight': 1, 'status': True},
              4: {'weight': 2, 'status': True}})

net = Network({node1.node_id: node1,
               node2.node_id: node2,
               node3.node_id: node3,
               node4.node_id: node4,
               node5.node_id: node5})
print(net)

# iterates through all nodes in network_1, finds and prints shortest path and weight
# manually calls each destination individually
for node in network_1.nodes():
    path, weight = dijkstra.shortest_path(node)
    print('The shortest path between Node %s#%d%s and Node %s#%d%s is:'
          '\n\t%-8s%s%s%s'
          '\n\t%-8s%s%d%s\n'
          % (ANSI_CYAN, dijkstra.source, ANSI_RESET, ANSI_CYAN, node, ANSI_RESET,
             'Path: ', ANSI_YELLOW, path, ANSI_RESET,
             'Weight: ', ANSI_YELLOW, weight, ANSI_RESET))

# shortest_paths contains all shortest paths from the source node
# all paths stored in a single structure
shortest_paths = dijkstra.all_shortest_paths()
path, weight = shortest_paths[7]
print(f'Shortest path from #{dijkstra.source} to #7:'
      f'\n\tPath: {path}'
      f'\n\tWeight: {weight}')

print(node2.get_adjacents())
