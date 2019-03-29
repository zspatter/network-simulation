from network_simulator.Node import Node
from network_simulator.exceptions import NodeAlreadyExistsError, \
    NodeDoesNotExistError, EdgeAlreadyExistsError, EdgeDoesNotExistError, \
    ElementActiveError, ElementInactiveError

"""
Add capability to represent subnetworks

A network will include nodes which will be represented by a complete
graph (mesh topology) of nodes objects (network within network)

These subnetworks will represent health systems (IU Health) while the
overall network will represent all hospitals
"""


class Network:
    """
    A class representing a network (graph). A network is defined through
    a collection of nodes (and their adjacency dicts). A network consists
    of a unique graph ID, label, and network dict that contains all of the
    nodes contained within the graph.
    """
    def __init__(self, network_dict=None):
        """
        Creates an instance of a Network. This function ensures that
        the adjacency dicts of nodes mirror each other (undirected graph).
        Furthermore, this function ensures nodes present in an adjacency
        list are present in the graph.

        :param dict network_dict: {int node_id: Node, ...} (None by default)
        """

        if network_dict is None:
            network_dict = {}

        to_remove = list()

        # ensures adjacency lists mirror each other (undirected weighted edges)
        nodes = network_dict.keys()
        # iterates through all nodes
        for node in nodes:
            adjacents = network_dict[node].adjacency_dict.keys()
            # iterates through all of the current node's adjacents
            for adjacent in adjacents:

                # if adjacent node id is present in network
                if adjacent in network_dict:
                    # if node is key in adjacent's adjacency dict
                    # AND the adjacencies mirror one another
                    if node in network_dict[adjacent].adjacency_dict.keys() \
                            and network_dict[adjacent].adjacency_dict[node] \
                            is network_dict[node].adjacency_dict[adjacent]:

                        continue

                    # if node isn't present in adjacent's adjacency dict
                    # OR adjacencies differ from one another
                    else:
                        # if edge is represented in both adjacency dicts
                        # (this prioritizes the latter status/weight values
                        # if the adjacencies differ)
                        if node in network_dict[adjacent].adjacency_dict:
                            network_dict[node].adjacency_dict[adjacent] = \
                                network_dict[adjacent].adjacency_dict[node]

                        # if edge is only present in node's adjacency dict
                        else:
                            network_dict[adjacent].adjacency_dict[node] = \
                                network_dict[node].adjacency_dict[adjacent]

                # if adjacent node id does not exist in graph
                else:
                    to_remove.append([node, adjacent])

        # remove edges to nodes that don't exist in graph
        for node, adjacent in to_remove:
            del network_dict[node].adjacency_dict[adjacent]

        self.network_dict = network_dict

    def nodes(self):
        """
        Returns list of active nodes within the graph.

        :return: active nodes in graph
        :rtype: list
        """
        nodes = list(self.network_dict.keys())
        active_nodes = list()
        for node in nodes:
            if self.network_dict[node].status:
                active_nodes.append(node)
        return active_nodes

    def add_node(self, node):
        """
        Adds a node with the passed parameters to the graph. If the
        node_id is already present in the graph, an error message
        is printed to the console.

        :param Node node: node that will be added to the graph
        """
        try:
            # if node_id is unique, add it to the network
            if node.node_id not in self.network_dict:
                self.network_dict[node.node_id] = node

                # adds edges to the new node from the nodes in the adjacency list
                # (this ensures the edge is represented in both directions)
                for key in node.adjacency_dict:
                    self.network_dict[key].adjacency_dict[node.node_id] = \
                        node.adjacency_dict[key]
                print(f'Node ID: #{node.node_id} has been added to this '
                      f'network!')

            # if node already exists
            else:
                raise NodeAlreadyExistsError(f'Node ID: #{node.node_id} '
                                             f'is already present in this network! '
                                             f'Node could not be added.')

        except NodeAlreadyExistsError as e:
            print(e)

    def remove_node(self, node_id):
        """
        Removes the node with the passed node_id from the graph. If node_id
        is not present in the graph, an error message is printed to the console.

        :param int node_id: unique identifier within a given graph
        """
        try:
            # if node is present in graph
            if node_id in self.network_dict:
                # gathers list of adjacent node id's
                adjacency_dict = self.network_dict[node_id].get_adjacents()

                # removes edges store on adjacent objects
                for key in adjacency_dict:
                    del self.network_dict[key].adjacency_dict[node_id]

                # removes node object
                del self.network_dict[node_id]
                print(f'Node ID: #{node_id} and all of it\'s edges has been removed!')

            # if node is not present in graph
            else:
                raise NodeDoesNotExistError(f'Node ID: #{node_id} is not present'
                                            f' in this network! Node could not be'
                                            f' removed.')

        except NodeDoesNotExistError as e:
            print(e)

    def add_edge(self, node_id1, node_id2, weight):
        """
        Adds an edge between two nodes with a specified weight. It is
        assumed that the added edge will be active. If there already
        exists an edge between the two nodes, an error message is printed
        to the console.

        :param int node_id1: unique identifier within a given graph
            (one of the vertices to be connected by the added edge)
        :param int node_id2: unique identifier within a given graph
            (one of the vertices to be connected by the added edge)
        :param int weight: cost associated with the edge
        """
        try:
            # if nodes are in graph
            if node_id1 in self.network_dict and node_id2 in self.network_dict:
                # if nodes are active
                if node_id1 in self.nodes() and node_id2 in self.nodes():
                    # if there is not an edge already connecting node 1 and node 2
                    if node_id2 not in self.network_dict[node_id1].get_adjacents() \
                            and node_id1 not in self.network_dict[node_id2].get_adjacents():

                        self.network_dict[node_id1].adjacency_dict[node_id2] = \
                            {'weight': weight, 'status': True}
                        self.network_dict[node_id2].adjacency_dict[node_id1] = \
                            {'weight': weight, 'status': True}

                        print(f'An edge has been added between Node ID: '
                              f'#{node_id1} and Node ID: #{node_id2} with'
                              f'a weight of {weight}!')

                    # if there is already an edge connecting the nodes
                    else:
                        raise EdgeAlreadyExistsError(f'There already exists an '
                                                     f'edge between Node ID: '
                                                     f'#{node_id1} and Node ID: '
                                                     f'#{node_id2}! This edge '
                                                     f'could not be added.')
                # if node(s) inactive
                else:
                    raise ElementInactiveError('One of the connecting nodes '
                                               'is inactive! As a result, this'
                                               ' edge cannot be added.')
            # if node(s) don't exist
            else:
                raise NodeDoesNotExistError(f'One of the passed nodes does '
                                            f'not exist! As a result, there '
                                            f'cannot be an edge, so it cannot '
                                            f'be added.')

        except EdgeAlreadyExistsError as e:
            print(e)
        except ElementInactiveError as e:
            print(e)
        except NodeDoesNotExistError as e:
            print(e)

    def remove_edge(self, node_id1, node_id2):
        """
        Removes an edge between two nodes from the graph. If the edge
        does not exist, an error message is printed to the console
        indicating that the edge cannot be removed.

        :param int node_id1: unique identifier within a given graph
            (one of the vertices connected by the edge to be removed)
        :param int node_id2: unique identifier within a given graph
            (one of the vertices connected by the edge to be removed)
        """

        # TODO what if edge is only in one adjacency dict?
        try:
            # if nodes are in graph
            if node_id1 in self.network_dict and node_id2 in self.network_dict:

                # if shared edge exists
                if node_id1 in self.network_dict[node_id2].adjacency_dict.keys() \
                        and node_id1 in self.network_dict[node_id2].adjacency_dict.keys():
                    del self.network_dict[node_id1].adjacency_dict[node_id2]
                    del self.network_dict[node_id2].adjacency_dict[node_id1]

                    print(f'The edge between Node ID: #{node_id1} '
                          f'and Node ID: #{node_id2} has been removed!')

                # if shared edge doesn't exist
                else:
                    raise EdgeDoesNotExistError(f'There is no edge connecting '
                                                f'Node ID: #{node_id1} and Node '
                                                f'ID: #{node_id2}, so there is '
                                                f'no edge to remove!')

            # if node(s) doesn't exist
            else:
                raise NodeDoesNotExistError(f'One of the passed nodes does '
                                            f'not exist! As a result, there '
                                            f'cannot be an edge, so it cannot '
                                            f'be marked as inactive.')

        except EdgeDoesNotExistError as e:
            print(e)
        except NodeDoesNotExistError as e:
            print(e)

    def mark_node_inactive(self, node_id):
        """
        Marks all edges in the adjacency list of the specified node as
        inactive, then mirrors that status in the other adjacency lists.
        Finally, the specified node's status is marked as inactive. If
        the node is already inactive, an error message indicating this
        prints to the console. If the node is not present in the graph,
        an error message prints to the console.

        :param int node_id: unique identifier within a given graph
        """
        try:
            # if node exists and is active
            if node_id in self.network_dict and self.network_dict[node_id].status:
                # gathers list of adjacent node id's
                adjacency_dict = self.network_dict[node_id].get_adjacents()

                # marks all edges of node as inactive, and mirrors
                # the status on all adjacents edges connected to the node
                for key in adjacency_dict:
                    self.network_dict[key].adjacency_dict[node_id]['status'] = False
                    self.network_dict[node_id].adjacency_dict[key]['status'] = False

                # marks node status as inactive
                self.network_dict[node_id].status = False
                print(f'Node ID: #{node_id} and all of it\'s edges has '
                      f'been marked inactive!')

            # if node exists and is inactive
            elif node_id in self.network_dict and not self.network_dict[node_id].status:
                raise ElementInactiveError(f'Node ID: #{node_id} is '
                                           f'already inactive!')

            # if node doesn't exist
            else:
                raise NodeDoesNotExistError(f'Node ID: #{node_id} is not present'
                                            f' in this network! Node could not '
                                            f'be marked inactive.')

        except ElementInactiveError as e:
            print(e)
        except NodeDoesNotExistError as e:
            print(e)

    """
    How should we handle status if an edge is explicitly made inactive,
    then a connected node is made inactive, then eventually active again
    
    currently, the edge that was explicitly toggled off would be made active
    when the connected node is made active
    
    should node status take priority over edge status?
    """
    def mark_node_active(self, node_id):
        """
        Marks all adjacent edges connected with another active node as
        active, then marks the specified node as active. If the node is
        already active, an error message prints to the console. If the
        node is not present in the graph, an error message prints to the
        console.

        :param int node_id: unique identifier within a given graph
        """
        try:
            # if node exists and is inactive
            if node_id in self.network_dict and not self.network_dict[node_id].status:
                # gathers list of adjacent node id's
                adjacency_dict = self.network_dict[node_id].adjacency_dict

                # marks all edges of node as active, and mirrors
                # the status on all adjacents edges connected to the node
                for key in adjacency_dict:
                    if self.network_dict[key].status:
                        self.network_dict[key].adjacency_dict[node_id]['status'] = True
                        self.network_dict[node_id].adjacency_dict[key]['status'] = True

                # marks node status as inactive
                self.network_dict[node_id].status = True
                print(f'Node ID: #{node_id} and all of it\'s edges has been '
                      f'marked active!')

            # if node exists and is active
            elif node_id in self.network_dict and self.network_dict[node_id].status:
                raise ElementActiveError(f'Node ID: #{node_id} is already active!')

            # if node doesn't exist
            else:
                raise NodeDoesNotExistError(f'Node ID: #{node_id} is not present '
                                            f'in this network! Node could not be '
                                            f'marked active.')

        except ElementActiveError as e:
            print(e)
        except NodeDoesNotExistError as e:
            print(e)

    def mark_edge_inactive(self, node_id1, node_id2):
        """
        Marks the specified edge as inactive in both adjacency lists iff
        a shared edge exists and both edges are active. If not, an error
        message is printed to the console indicating which conditions are
        not met.

        :param int node_id1: unique identifier within a given graph
        :param int node_id2: unique identifier within a given graph
        """
        try:
            # if node exists
            if node_id1 in self.network_dict and node_id2 in self.network_dict:
                # if shared edge exists
                if node_id1 in self.network_dict[node_id2].adjacency_dict.keys() \
                        and node_id1 in self.network_dict[node_id2].adjacency_dict.keys():

                    # if both edges are active
                    if self.network_dict[node_id1].adjacency_dict[node_id2]['status'] \
                            and self.network_dict[node_id2].adjacency_dict[node_id1]['status']:

                        self.network_dict[node_id1].adjacency_dict[node_id2]['status'] = False
                        self.network_dict[node_id2].adjacency_dict[node_id1]['status'] = False

                        print(f'The edge connecting Node ID: #{node_id1} and Node ID: '
                              f'#{node_id2} has been marked inactive!')

                    # if the edges are inactive
                    else:
                        raise ElementInactiveError(f'The edge connecting Node'
                                                   f' ID: #{node_id1} and Node'
                                                   f' ID: #{node_id2} is already'
                                                   f' inactive! As a result, the'
                                                   f' edge cannot be marked inactive.')

                # if a shared edge doesn't exist
                else:
                    raise EdgeDoesNotExistError(f'There is not a shared edge '
                                                f'between Node ID: #{node_id1} '
                                                f'and Node ID: #{node_id2}! As '
                                                f'a result, the edge cannot be '
                                                f'marked inactive.')

            # if node doesn't exist
            else:
                raise NodeDoesNotExistError(f'One of the passed nodes does '
                                            f'not exist! As a result, there '
                                            f'cannot be an edge, so it cannot '
                                            f'be marked as inactive.')

        except ElementInactiveError as e:
            print(e)
        except EdgeDoesNotExistError as e:
            print(e)
        except NodeDoesNotExistError as e:
            print(e)

    def mark_edge_active(self, node_id1, node_id2):
        """
        Marks the specified edge as active in both adjacency lists iff
        both connected nodes are active and the edge is inactive.

        :param int node_id1: unique identifier within a given graph
        :param int node_id2: unique identifier within a given graph
        """
        try:
            # if nodes exist
            if node_id1 in self.network_dict and node_id2 in self.network_dict:
                # if shared edge exists
                if node_id1 in self.network_dict[node_id2].adjacency_dict.keys() \
                        and node_id1 in self.network_dict[node_id2].adjacency_dict.keys():

                    # if both nodes are active
                    if self.network_dict[node_id1].status and self.network_dict[node_id2].status:
                        # if both edges are inactive
                        if not self.network_dict[node_id1].adjacency_dict[node_id2]['status'] \
                                and not self.network_dict[node_id2].adjacency_dict[node_id1]['status']:

                            self.network_dict[node_id1].adjacency_dict[node_id2]['status'] = True
                            self.network_dict[node_id2].adjacency_dict[node_id1]['status'] = True

                            print(f'The edge connecting Node ID: #{node_id1} and Node ID: '
                                  f'#{node_id2} has been marked active!')

                        # if the edges are active
                        else:
                            raise ElementActiveError(f'The edge connecting Node '
                                                     f'ID: #{node_id1} and Node '
                                                     f'ID: #{node_id2} is already '
                                                     f'active! As a result, the '
                                                     f'edge cannot be marked active.')
                    # if at least one node is inactive
                    else:
                        raise ElementInactiveError('One of the connecting nodes '
                                                   'is active! As a result, this'
                                                   ' edge must remain active.')
                # if shared edge does not exist
                else:
                    raise EdgeDoesNotExistError(f'There is not a shared edge '
                                                f'between Node ID: #{node_id1}'
                                                f' and Node ID: #{node_id2}! As'
                                                f' a result, the edge cannot be '
                                                f'marked active.')
            # if node doesn't exist
            else:
                raise NodeDoesNotExistError(f'One of the passed nodes does '
                                            f'not exist! As a result, there '
                                            f'cannot be an edge, so it cannot '
                                            f'be marked as inactive.')

        except ElementActiveError as e:
            print(e)
        except ElementInactiveError as e:
            print(e)
        except EdgeDoesNotExistError as e:
            print(e)
        except NodeDoesNotExistError as e:
            print(e)

    def __str__(self):
        """
        Returns an easily readable (formatted) string representation of
        the instance. Only active nodes and edges are represented. This
        calls the Node.__str__ function.

        :return: easily readable string representation of the graph
        :rtype: str
        """
        string = ''
        for key in self.network_dict:
            string += f'{self.network_dict[key].__str__()}'
        return string + '\n\n===============================\n'
