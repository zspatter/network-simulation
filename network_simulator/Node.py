class Node:
    """
    A class representing a given node/vertex. A node is defined through
    a unique node ID, label, and adjacency dict that contains all of the
    neighboring nodes along with the weight associated with the shared
    edge, and a status that marks active/inactive nodes.
    """
    def __init__(self, node_id, label='Default node label', adjacency_dict=None, status=None):
        """
        Creates an instance of a Node

        :param int node_id: unique identifier within a given graph
        :param int/str label: name associated with a node
        :param dict adjacency_dict: {int node_id: {'weight': int, 'status': bool}, ...}
            (None by default)
        :param bool status: flag indicating whether a node is active or inactive
            (None by default)
        """
        self.node_id = node_id
        self.label = label
        if adjacency_dict is None:
            adjacency_dict = {}
        self.adjacency_dict = adjacency_dict

        if status is False:
            for key in adjacency_dict:
                adjacency_dict[key]['status'] = False

        if status is None:
            status = True
        self.status = status

    def is_adjacent(self, node_id):
        """
        Returns bool indicating if this instance is connected to the passed
        node_id with an active edge

        :param int node_id: unique identifier within a given graph

        :return: bool indicating if the passed node is adjacent to the current node
        :rtype: bool
        """
        if node_id in self.adjacency_dict and self.adjacency_dict[node_id]['status'] \
                and self.status:
            return True
        else:
            return False

    def get_adjacents(self):
        """
        Returns list of adjacent nodes. Nodes are only added to the list
        if they are currently active, and the edge connecting the nodes
        is currently active

        :return: active adjacent nodes
        :rtype: list
        """
        adjacents = list()
        if self.status:
            for key in self.adjacency_dict:
                if self.adjacency_dict[key]['status']:
                    adjacents.append(key)
        return adjacents

    def __str__(self):
        """
        Returns an easily readable (formatted) string representation of the instance.
        Only active edges are represented. If the node is inactive,
        nothing is returned.

        :return: easily readable string representation of the node
        :rtype: str
        """
        if self.status:
            string = '\n\nLabel: ' + self.label + '\t(Node ID: ' + \
                     str(self.node_id) + ')\nNeighbors:'

            for key in self.adjacency_dict:
                if self.adjacency_dict[key]['status']:
                    string += '\n\tNode {:>6}:\t{:>2} (weight)'.format(
                        '#' + str(key), str(self.adjacency_dict[key]['weight']))
            return string
        else:
            return f'Node ID: #{self.node_id} is inactive and cannot be converted to a string.'
