from Network_Simulator.Node import Node
import random


# TODO: add support for functions to accept label (rather than just node_id)
class Network:
    """
    A class representing a network (graph). A network is defined through
    a collection of nodes (and their adjacency dicts). A network consists
    of a unique graph ID, label, and network dict that contains all of the
    nodes contained within the graph.
    """

    def __init__(self, network_dict=None):
        """
        Creates an instance of a Network

        :param dict network_dict: {int node_id: Node, ...} (None by default)
        """

        if network_dict is None:
            network_dict = {}
        self.network_dict = network_dict

        # ensures adjacency lists mirror each other (undirected weighted edges)
        nodes = network_dict.keys()
        for node in nodes:
            adjacents = network_dict[node].get_adjacents()
            for adjacent in adjacents:
                if node in self.network_dict[adjacent].get_adjacents() \
                        and self.network_dict[adjacent].adjacency_dict[node] \
                        is self.network_dict[node].adjacency_dict[adjacent]:
                    continue
                else:
                    self.network_dict[adjacent].adjacency_dict[node] = self.network_dict[node].adjacency_dict[adjacent]

    def is_connected(self, nodes_encountered=None, start_node=None):
        """
        Returns bool indicating graph connectivity (path between all nodes).
        This is a recursive DFS.

        :param set nodes_encountered: set of node_id's encountered (None by default)
        :param int start_node: node_id of start of search (None by default)

        :return: bool indicating graph connectivity
        :rtype: bool
        """
        if nodes_encountered is None:
            nodes_encountered = set()
        nodes = self.nodes()
        if not start_node:
            # chose a vertex from network as start point
            start_node = nodes[0]
        nodes_encountered.add(start_node)
        if len(nodes_encountered) != len(nodes):
            for node in self.network_dict[start_node].get_adjacents():
                if node not in nodes_encountered:
                    if self.is_connected(nodes_encountered, node):
                        return True
        else:
            return True
        return False

    # todo feed graph, is it connected
    def DFS(self, node_id=None):
        """
        Returns bool indicating graph connectivity (path between all nodes).
        This is an iterative DFS.

        :param int node_id: identifies node where search will start (None by default)

        :return: bool indicating graph connectivity
        :rtype: bool
        """
        nodes_encountered = set()
        if not node_id:
            node_id = self.nodes()[0]
        stack = [node_id]
        while stack:
            node = stack.pop()
            if node not in nodes_encountered:
                nodes_encountered.add(node)
                # TODO: this adds all adjacents - this will cause repeat visits
                stack.extend(self.network_dict[node].get_adjacents())

        if len(nodes_encountered) != len(self.nodes()):
            return False
        else:
            return True

    def BFS(self, node_id=None):
        """
        Returns bool indicating graph connectivity (path between all nodes).
        This is an iterative BFS.

        :param int node_id: identifies node where search will start (None by default)

        :return: bool indicating graph connectivity
        :rtype: bool
        """
        # mark all the nodes as not visited (value is None)
        visited = dict.fromkeys(self.nodes())
        nodes_encountered = set()
        queue = []

        if not node_id:
            node_id = self.nodes()[0]

        # mark the source node as visited and enqueue it
        queue.append(node_id)
        visited[node_id] = True
        nodes_encountered.add(node_id)

        while queue:
            # dequeue a node from queue and add to nodes_encountered
            node_id = queue.pop(0)
            nodes_encountered.add(node_id)

            # all adjacents of current node are checked, if the node hasn't been
            # enqueued previously, node is enqueued and added to nodes_encountered
            for node in self.network_dict[node_id].get_adjacents():
                if visited[node] is None:
                    queue.append(node)
                    visited[node] = True
                    nodes_encountered.add(node)

        # if size of nodes_encountered equals size of nodes(), return True
        if len(nodes_encountered) == len(self.nodes()):
            return True
        else:
            return False

    # dijkstra's saves all shortest paths from source to struture
    # gets path and/or weight
    def dijkstra(self, initial_node_id, end_node_id):
        """
        Returns the shortest path between the initial node and the end
        node as well as the total cost of the path. If there is no
        path that exists which connects the given nodes, an error message
        is printed to the console.

        :param int initial_node_id: identifies the source node
        :param int end_node_id: identifies the destination node

        :return: collection of node ID's that indicate the shortest path
            and the total cost of the given path
        :rtype: dict {'path': list, 'weight': int}
        """
        # shortest paths is a dict of nodes
        # whose value is a tuple of (previous node, weight)
        shortest_paths = {initial_node_id: (None, 0)}
        current_node = initial_node_id
        visited = set()

        while current_node != end_node_id:
            visited.add(current_node)
            destinations = self.network_dict[current_node].get_adjacents()
            weight_to_current_node = shortest_paths[current_node][1]

            # for node in active adjacents
            for next_node in destinations:
                weight = self.network_dict[current_node].adjacency_dict[next_node]['weight'] + weight_to_current_node

                # if next node hasn't been stored
                if next_node not in shortest_paths:
                    shortest_paths[next_node] = (current_node, weight)

                # if next node has been stored
                else:
                    current_shortest_weight = shortest_paths[next_node][1]

                    # if currently stored weight is greater than this path's weight
                    if current_shortest_weight > weight:
                        shortest_paths[next_node] = (current_node, weight)

            # next destinations are nodes in shortest paths that haven't been visited
            next_destinations = {node: shortest_paths[node] for node in shortest_paths if node not in visited}
            # if next destinations are empty
            if not next_destinations:
                return f'There is no path connecting Node ID: #{initial_node_id} ' \
                    f'and Node ID: #{end_node_id}.'

            # next node is the destination with the lowest weight
            current_node = min(next_destinations, key=lambda k: next_destinations[k][1])

        # Work back through destinations in shortest path
        path = []
        cumulative_weight = 0

        while current_node:
            path.append(current_node)
            next_node = shortest_paths[current_node][0]
            cumulative_weight += shortest_paths[current_node][1]
            current_node = next_node
        # Reverse path
        path = path[::-1]
        shortest_path = {'path': path, 'weight': cumulative_weight}
        return shortest_path

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

    @staticmethod
    def generate_network(n):
        """
        Returns randomly generated network with n nodes.

        :param int n: number of nodes generated graph will contain

        :return: randomly generated network with N nodes
        :rtype: Network
        """
        network_dict = {}
        for x in range(1, n + 1):
            adjacency_dict = Network.generate_adjacency_dict(x, n)
            node = Node(x, 'Node #' + str(x), adjacency_dict)
            network_dict[x] = node
        network = Network(network_dict)
        return network

    # TODO random parameter (seed)
    @staticmethod
    def generate_adjacency_dict(node_id, total_nodes):
        """
        Returns randomly generated adjacency dict for an instance of a node.
        The generated adjacency list can contain a connection to any node
        in the graph (except itself). This will prevent parallel edges from
        being generated. A random number of edges between 5 and 25 (inclusive)
        will be generated and a random weight between 1 and 50 (inclusive)
        will be assigned to each edge.
        This is called by the generate_network function.

        :param int node_id: unique identifier for the node that the
            adjacency dict is being generated for
        :param int total_nodes: total number of nodes present in the generated graph

        :return: randomly generated adjacency_dict
        :rtype: dict
        """
        adjacency_dict = {}
        for n in range(random.randint(5, 25)):
            random_node = random.randint(1, total_nodes)
            # ensures node doesn't add itself to adjacency_dict
            # or add a duplicate entry
            while node_id == random_node or any(random_node == x for x in adjacency_dict.keys()):
                random_node = random.randint(1, total_nodes)
            # updates adjacency dict to new format
            adjacency_dict[random_node] = {'weight': random.randint(1, 50), 'status': True}
        return adjacency_dict

    def add_node(self, node):
        """
        Adds a node with the passed parameters to the graph. If the
        node_id is already present in the graph, an error message
        is printed to the console.

        :param Node node: node that will be added to the graph
        """
        # if node_id is unique, add it to the network
        if node.node_id not in self.network_dict:
            self.network_dict[node.node_id] = node

            # adds edges to the new node from the nodes in the adjacency list
            # (this ensures the edge is represented in both directions)
            for key in node.adjacency_dict:
                self.network_dict[key].adjacency_dict[node.node_id] = node.adjacency_dict[key]

        # if node already exists
        else:
            print(f'Node ID: #{node.node_id} is already present in this network. '
                  f'Node could not be added.')

    def remove_node(self, node_id):
        """
        Removes the node with the passed node_id from the graph. If node_id
        is not present in the graph, an error message is printed to the console.

        :param int node_id: unique identifier within a given graph
        """
        # if node is present in graph
        if node_id in self.network_dict:
            # gathers list of adjacent node id's
            adjacency_dict = self.network_dict[node_id].get_adjacents()

            # removes edges store on adjacent objects
            for key in adjacency_dict:
                del self.network_dict[key].adjacency_dict[node_id]

            # removes node object
            del self.network_dict[node_id]
            print(f'Node ID: #{node_id} and all of it\'s edges has been removed')

        # if node is not present in graph
        else:
            print(f'Node ID: #{node_id} is not present in this network. '
                  f'Node could not be removed.')

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
        # if there is not an edge already connecting node 1 and node 2
        if node_id2 not in self.network_dict[node_id1].get_adjacents() \
                and node_id1 not in self.network_dict[node_id2].get_adjacents():
            self.network_dict[node_id1].adjacency_dict[node_id2] = {'weight': weight, 'status': True}
            self.network_dict[node_id2].adjacency_dict[node_id1] = {'weight': weight, 'status': True}

        # if there is already an edge connecting the nodes
        else:
            print(f'There already exists an edge between Node ID: #{node_id1} '
                  f'and Node ID: #{node_id2}. This edge could not be added.')

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
        # if shared edge exists
        if node_id1 in self.network_dict[node_id2].adjacency_dict.keys() \
                and node_id1 in self.network_dict[node_id2].adjacency_dict.keys():
            del self.network_dict[node_id1].adjacency_dict[node_id2]
            del self.network_dict[node_id2].adjacency_dict[node_id1]

        # if shared edge doesn't exist
        else:
            print(f'There is no edge connecting Node ID: #{node_id1} and Node ID: #{node_id2}, so there is no edge to remove.')

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
            print(f'Node ID: #{node_id} and all of it\'s edges has been marked inactive.')

        # if node exists and is inactive
        elif node_id in self.network_dict and not self.network_dict[node_id].status:
            print(f'Node ID: #{node_id} is already inactive!')

        # if node doesn't exist
        else:
            print(f'Node ID: #{node_id} is not present in this network. '
                  f'Node could not be marked inactive.')

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
            print(f'Node ID: #{node_id} and all of it\'s edges has been marked active.')

        # if node exists and is active
        elif node_id in self.network_dict and self.network_dict[node_id].status:
            print(f'Node ID: #{node_id} is already active!')

        # if node doesn't exist
        else:
            print(f'Node ID: #{node_id} is not present in this network. '
                  f'Node could not be marked active.')

    def mark_edge_inactive(self, node_id1, node_id2):
        """
        Marks the specified edge as inactive in both adjacency lists iff
        a shared edge exists and both edges are active. If not, an error
        message is printed to the console indicating which conditions are
        not met.

        :param int node_id1: unique identifier within a given graph
        :param int node_id2: unique identifier within a given graph
        """
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
                          f'#{node_id2} has been marked inactive.')

                # if the edges are inactive
                else:
                    print(f'The edge connecting Node ID: #{node_id1} '
                          f'and Node ID: #{node_id2} is already inactive. '
                          f'As a result, the edge cannot be marked inactive.')

            # if a shared edge doesn't exist
            else:
                print(f'There is not a shared edge between Node ID: #{node_id1} '
                      f'and Node ID: #{node_id2}. As a result, the edge cannot '
                      f'be marked inactive.')

        # if node doesn't exist
        else:
            print(f'One of the passed nodes does not exist. As a result, '
                  f'there cannot be an edge, so it cannot be marked as inactive.')

    def mark_edge_active(self, node_id1, node_id2):
        """
        Marks the specified edge as active in both adjacency lists iff
        both connected nodes are active and the edge is inactive.

        :param int node_id1: unique identifier within a given graph
        :param int node_id2: unique identifier within a given graph
        """
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
                          f'#{node_id2} has been marked active.')

                # if the edges are active
                else:
                    print(f'The edge connecting Node ID: #{node_id1} '
                          f'and Node ID: #{node_id2} is already active. '
                          f'As a result, the edge cannot be marked active.')

            # if at least one node is inactive
            else:
                print('One of the connecting nodes is inactive. '
                      'As a result, this edge must remain inactive.')

        # if shared edge does not exist
        else:
            print(f'There is not a shared edge between Node ID: #{node_id1} '
                  f'and Node ID: #{node_id2}. As a result, the edge cannot '
                  f'be marked active.')

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
