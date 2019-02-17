class Node:
    # a Node instance consists of:
    # node_id (int)
    # label (string)
    # adjacency_dict (node_id: weight)
    def __init__(self, node_id, label='Default Node', adjacency_dict=None):
        self.node_id = node_id
        self.label = label
        if adjacency_dict is None:
            adjacency_dict = {}
        self.adjacency_dict = adjacency_dict

    # return bool indicating whether this instance shares an edge with passed node_id
    def is_adjacent(self, node_id):
        if node_id in self.adjacency_dict:
            return True
        else:
            return False

    def get_adjacents(self):
        return list(self.adjacency_dict.keys())

    def __del__(self):
        print(f'Destructor called, Node #{self.node_id}: {self.label} removed.')

    def __str__(self):
        string = '\n\nLabel: ' + self.label + '\t(Node ID: ' + str(self.node_id) + ')\nNeighbors:'
        for key in self.adjacency_dict:
            string += '\n\tNode {:>4}:\t{:>2} (weight)'.format('#' + str(key), str(self.adjacency_dict[key]))
        return string

