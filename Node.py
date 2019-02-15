class Node:
    def __init__(self, node_id, adjacency_list, label):
        self.node_id = node_id
        self.adjacency_list = adjacency_list
        self.label = label


    # if 'key' in dict:
    def is_neighbor(self, node_id):
        if node_id in self.adjacency_list:
            return True
        else:
            return False


    def edges(self):
        return list(self.adjacency_list.keys())


    def __del__(self):
        print(f'Destructor called, Node #{self.node_id}: {self.label} removed.')

    def __str__(self):
        string = '\n\nLabel: ' + self.label +  '\t(node id: ' + str(self.node_id) + ')\nNeighbors:'
        for key in self.adjacency_list:
            string += '\n\tNode #' + str(key) + ': weight - ' + str(self.adjacency_list[key])
        return string

