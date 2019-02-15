from Node import Node

class Network:
    def __init__(self, graph_id, label, network_dict = None):
        self.graph_id = graph_id
        self.label = label
        if network_dict is None:
            network_dict = {}
        self.network_dict = network_dict


    def is_connected(self, nodes_encountered = None, start_node = None):
        if nodes_encountered is None:
            nodes_encountered = set()
        network_dict = self.network_dict
        nodes = list(network_dict.keys())
        if not start_node:
            # chose a vertex from network as start point
            start_node = nodes[0]
        nodes_encountered.add(start_node)
        if len(nodes_encountered) != len(nodes):
            for node in network_dict[start_node].adjacency_list.keys():
                if node not in nodes_encountered:
                    if self.is_connected(nodes_encountered, node):
                        return True
        else:
            return True
        return False


    def nodes(self):
        return list(self.network_dict.keys())


    def add_node(self, node_id, adjacency_list, label):
        # if node_id is unique, add it to the network
        if node_id not in self.network_dict:
            # creates new node with pass parameters
            self.network_dict[node_id] = Node(node_id, adjacency_list, label)
            # adds edges to the new node from the nodes in the adjaceny list
            # (this ensures the edge is represented in both directions)
            for key in adjacency_list:
                self.network_dict[key].adjacency_list[node_id] = adjacency_list[key]


    def remove_node(self, node_id):
        # gathers list of adjacent node id's
        adjacency_list = self.network_dict[node_id].adjacency_list.keys()

        # removes edges store on adjacent objects
        for key in adjacency_list:
            del self.network_dict[key].adjacency_list[node_id]

        # removes node object
        del self.network_dict[node_id]
        print(f'Node ID: #{node_id} and all of it\'s edges has been removed')


    # add edge to both adjacency lists
    def add_edge(self, node_id1, node_id2, weight):
        if node2 not in self.network_dict[node1].adjacency_list.keys() \
                and node1 not in self.network_dict[node2].adjacency_list.keys():
            self.network_dict[node1].adjacency_list[node2] = weight
            self.network_dict[node2].adjacency_list[node1] = weight


    def remove_edge(self, node_id1, node_id2):
        del self.network_dict[node_id1].adjacency_list[node_id2]
        del self.network_dict[node_id2].adjacency_list[node_id1]



    def __str__(self):
        string = str(self.graph_id) + " " + self.label
        for key in self.network_dict.keys():
            string += f'{self.network_dict[key].__str__()}'
        return string


# creates 10 individual nodes (hard coded adjacency lists to match)
node1 = Node(1, {2: 3, 3: 1, 5: 4, 9: 2}, "A")
node2 = Node(2, {1: 3, 4: 2, 5: 3, 7: 9, 8: 10, 9: 4}, "B")
node3 = Node(3, {1: 1, 4: 2, 6: 4, 7: 3}, "C")
node4 = Node(4, {2: 2, 3: 2, 6: 8, 10: 4}, "D")
node5 = Node(5, {1: 4, 2: 3, 8: 3, 9: 4}, "E")
node6 = Node(6, {3: 4, 4: 8, 9: 8, 10: 2}, "F")
node7 = Node(7, {2: 9, 3: 3, 8: 2, 10: 5}, "G")
node8 = Node(8, {2: 10, 5: 3, 7: 2, 9: 4}, "H")
node9 = Node(9, {1: 2, 2: 4, 5: 4, 6: 8, 8: 4}, "I")
node10 = Node(10, {4: 4, 6: 2, 7: 5}, "J")

# create a newtwork consisting of the nodes above
network = Network(1, 'Sample Network', {node1.node_id: node1,
                                        node2.node_id: node2,
                                        node3.node_id: node3,
                                        node4.node_id: node4,
                                        node5.node_id: node5,
                                        node6.node_id: node6,
                                        node7.node_id: node7,
                                        node8.node_id: node8,
                                        node9.node_id: node9,
                                        node10.node_id: node10})
# demonstrates __str__() function works
print(network.__str__())
# demonstrates is_connected() function works
if network.is_connected():
    print("\nThe network is connected!\n")
else:
    print("\nThe network is not connected!\n")

# demonstrates remove edges function works
network.remove_edge(1, 2)
print(network.__str__())
network.remove_node(3)
print(network.__str__())

print('\n\n\n')
# demonstrates the add node function works
network.add_node(11, {1: 3, 2: 4, 10: 8}, 'K')
print(network.__str__())
