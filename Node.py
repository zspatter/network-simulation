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
        self.status = True

    # return bool indicating whether this instance shares an edge with passed node_id
    def is_adjacent(self, node_id):
        if node_id in self.adjacency_dict and self.adjacency_dict[node_id]['status'] and self.status:
            return True
        else:
            return False

    def get_adjacents(self):
        # return list(self.adjacency_dict.keys())
        adjacents = list()
        if self.status:
            for key in self.adjacency_dict:
                if self.adjacency_dict[key]['status']:
                    adjacents.append(key)
        return adjacents

    # if node is active, returns string displaying all of the active edges
    def __str__(self):
        if self.status:
            string = '\n\nLabel: ' + self.label + '\t(Node ID: ' \
                     + str(self.node_id) + ')\nNeighbors:'
            for key in self.adjacency_dict:
                if self.adjacency_dict[key]['status']:
                    string += '\n\tNode {:>4}:\t{:>2} (weight)'.format('#' + str(key),
                                                                       str(self.adjacency_dict[key]['weight']))
            return string
