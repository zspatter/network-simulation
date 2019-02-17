from Node import Node
import random


# TODO #1 add support for functions to accept label (rather than just node_id)
# TODO #2 ensure generated network is ALWAYS connected initially
class Network:
    # a Network instance consists of:
    # graph_id (int)
    # label (string)
    # network_dict (node_id: Node)
    def __init__(self, graph_id, label, network_dict=None):
        self.graph_id = graph_id
        self.label = label
        if network_dict is None:
            network_dict = {}
        self.network_dict = network_dict

        # ensures adjacency lists mirror each other (undirected weighted edges)
        nodes = network_dict.keys()
        for node in nodes:
            adjacents = network_dict[node].get_adjacents()
            for adjacent in adjacents:
                if node in self.network_dict[adjacent].get_adjacents():
                    continue
                else:
                    self.network_dict[adjacent].adjacency_dict[node] = \
                        self.network_dict[node].adjacency_dict[adjacent]

    # determines if the network is connected (path between all nodes)
    def is_connected(self, nodes_encountered=None, start_node=None):
        if nodes_encountered is None:
            nodes_encountered = set()
        network_dict = self.network_dict
        nodes = list(network_dict.keys())
        if not start_node:
            # chose a vertex from network as start point
            start_node = nodes[0]
        nodes_encountered.add(start_node)
        if len(nodes_encountered) != len(nodes):
            for node in network_dict[start_node].get_adjacents():
                if node not in nodes_encountered:
                    if self.is_connected(nodes_encountered, node):
                        return True
        else:
            return True
        return False

    def nodes(self):
        return list(self.network_dict.keys())

    # this function generates a random network with n nodes
    @staticmethod
    def generate_network(n, graph_id=1, label='Generic Network'):
        network_dict = {}
        for x in range(1, n + 1):
            adjacency_dict = Network.generate_adjacency_dict(x, n)
            node = Node(x, 'Node #' + str(x), adjacency_dict)
            network_dict[x] = node
        network = Network(graph_id, label, network_dict)
        return network

    # this function generates an adjacency list consisting of 2-5 adjacencts
    @staticmethod
    def generate_adjacency_dict(node_id, total_nodes):
        adjacency_dict = {}
        for n in range(random.randint(2, 5)):
            random_node = random.randint(1, total_nodes)
            # ensures node doesn't add itself to adjacency_dict
            # or add a duplicate entry
            while node_id == random_node or \
                    any(random_node == x for x in adjacency_dict.keys()):
                random_node = random.randint(1, total_nodes)
            adjacency_dict[random_node] = random.randint(1, 20)
        return adjacency_dict

    def add_node(self, node_id, label, adjacency_dict):
        # if node_id is unique, add it to the network
        if node_id not in self.network_dict:
            # creates new node with pass parameters
            self.network_dict[node_id] = Node(node_id, label, adjacency_dict)
            # adds edges to the new node from the nodes in the adjacency list
            # (this ensures the edge is represented in both directions)
            for key in adjacency_dict:
                self.network_dict[key].adjacency_dict[node_id] = adjacency_dict[key]

    def remove_node(self, node_id):
        # gathers list of adjacent node id's
        adjacency_dict = self.network_dict[node_id].get_adjacents()

        # removes edges store on adjacent objects
        for key in adjacency_dict:
            del self.network_dict[key].adjacency_dict[node_id]

        # removes node object
        del self.network_dict[node_id]
        print(f'Node ID: #{node_id} and all of it\'s edges has been removed')

    # add edge to both adjacency lists
    def add_edge(self, node_id1, node_id2, weight):
        if node_id2 not in self.network_dict[node_id1].get_adjacents() \
                and node_id1 not in self.network_dict[node_id2].get_adjacents():
            self.network_dict[node_id1].adjacency_dict[node_id2] = weight
            self.network_dict[node_id2].adjacency_dict[node_id1] = weight

    def remove_edge(self, node_id1, node_id2):
        del self.network_dict[node_id1].adjacency_dict[node_id2]
        del self.network_dict[node_id2].adjacency_dict[node_id1]

    def __str__(self):
        string = 'Graph ID: ' + str(self.graph_id) + ': ' + self.label
        for key in self.network_dict.keys():
            string += f'{self.network_dict[key].__str__()}'
        return string


"""
The lines below behave as the main method in Java

Everything below is just to briefly demonstrate/test
the basic functions of our graph/network
"""

# creates 10 individual nodes (hard coded adjacency lists to match)
node_1 = Node(1, 'A', {2: 3, 3: 1, 5: 4, 9: 2})
node_2 = Node(2, 'B', {1: 3, 4: 2, 5: 3, 7: 9, 8: 10, 9: 4})
node_3 = Node(3, 'C', {1: 1, 4: 2, 6: 4, 7: 3})
node_4 = Node(4, 'D', {2: 2, 3: 2, 6: 8, 10: 4})
node_5 = Node(5, 'E', {1: 4, 2: 3, 8: 3, 9: 4})
node_6 = Node(6, 'F', {3: 4, 4: 8, 9: 8, 10: 2})
node_7 = Node(7, 'G', {2: 9, 3: 3, 8: 2, 10: 5})
node_8 = Node(8, 'H', {2: 10, 5: 3, 7: 2, 9: 4})
node_9 = Node(9, 'I', {1: 2, 2: 4, 5: 4, 6: 8, 8: 4})
node_10 = Node(10, 'J', {4: 4, 6: 2, 7: 5})

# create a network consisting of the nodes above
network_1 = Network(1, 'Sample Network',
                    {node_1.node_id: node_1,
                     node_2.node_id: node_2,
                     node_3.node_id: node_3,
                     node_4.node_id: node_4,
                     node_5.node_id: node_5,
                     node_6.node_id: node_6,
                     node_7.node_id: node_7,
                     node_8.node_id: node_8,
                     node_9.node_id: node_9,
                     node_10.node_id: node_10})

# demonstrates __str__() function works
print(network_1.__str__() + '\n\n===============================\n')

# demonstrates remove_edge function works
print('\t---REMOVE EDGE---\n')
network_1.remove_edge(1, 2)
print(network_1.__str__() + '\n\n===============================\n')

# demonstrates remove_node function works
print('\t---REMOVE NODE---\n')
network_1.remove_node(3)
print(network_1.__str__() + '\n\n===============================\n')

# demonstrates the add node function works
print('\t---ADD NODE---\n')
network_1.add_node(11, 'K', {1: 3, 2: 4, 10: 8})
print(network_1.__str__() + '\n\n===============================\n')


# demonstrates is_connected() function works
if network_1.is_connected():
    print("The network is connected!\n\n===============================\n")
else:
    print("The network is not connected!\n\n===============================\n")

# creates disconnected network to further test is_connected()
node_a = Node(1, 'A', {2: 1, 3: 2})
node_b = Node(2, 'B', {3: 1})
node_c = Node(3, 'C', {1: 2})
node_d = Node(4, 'D')
disconnected_network = Network(1, 'Disconnected Network',
                               {1: node_a,
                                2: node_b,
                                3: node_c,
                                4: node_d})

# prints Disconnected Network and checks if graph is connected
print('\t---DISCONNECTED GRAPH---\n')
print(disconnected_network.__str__())
print('The network is connected: ' + str(disconnected_network.is_connected()) +
      '\n\n===============================\n')

# tests the functionality in __init__ that ensures adjacency lists
# of separate nodes mirror each other (undirected, weighted edges)
init_tester_node1 = Node(1, "A", {2: 3, 3: 5})
init_tester_node2 = Node(2, "B", {1: 2, 4: 3})
init_tester_node3 = Node(3, "C", {2: 6, 4: 9})
init_tester_node4 = Node(4, "D", {3: 8, 2: 4})
init_tester_node5 = Node(5, "E", {1: 1, 4: 2})

init_tester = Network(1, "__init__ Test Network",
                      {init_tester_node1.node_id: init_tester_node1,
                       init_tester_node2.node_id: init_tester_node2,
                       init_tester_node3.node_id: init_tester_node3,
                       init_tester_node4.node_id: init_tester_node4,
                       init_tester_node5.node_id: init_tester_node5})

print('\t---ADJACENCY LISTS MIRROR TEST---\n')
print(init_tester.__str__() + '\n\n===============================\n')

# tests the generate_network and generate_adjacency_list functions
generated_network = Network.generate_network(50)
print('\t---GENERATED RANDOM NETWORK---\n')
print(generated_network.__str__() + '\n\n===============================\n')
if generated_network.is_connected():
    print('Generated Network is connected!\n')
else:
    print('Generated Network is not connected!\n')
