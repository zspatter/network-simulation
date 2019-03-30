class Dijkstra:
    """
    A class which will be used to analyze graphs to determine shortest
    paths between given nodes.

    Eventually this class will determine the shortest path between
    a source node and ALL other nodes.
    """

    def __init__(self, graph, source):
        weight, previous = Dijkstra.dijkstra(graph, source)
        self.source = source
        self.weight = weight
        self.previous = previous

    @staticmethod
    def dijkstra(graph, source):
        unvisited = graph.nodes()
        weight = dict.fromkeys(graph.nodes(), float('inf'))
        previous = dict.fromkeys(graph.nodes(), None)
        weight[source] = 0

        # while there are nodes which haven't been visited
        while unvisited:
            # picks the unvisited node with the shortest weight to visit next
            current_node = Dijkstra.minimum_unvisited_distance(unvisited, weight)
            unvisited.remove(current_node)

            # looks at all of the current node's adjacents
            for adjacent in graph.network_dict[current_node].get_adjacents():
                alt_weight = weight[current_node] + \
                             graph.network_dict[current_node].adjacency_dict[adjacent]['weight']
                # if this adjacent has a lower weight than currently recorded weight, replace it
                if alt_weight < weight[adjacent]:
                    weight[adjacent] = alt_weight
                    previous[adjacent] = current_node

        return weight, previous

    @staticmethod
    def minimum_unvisited_distance(unvisited, weight):
        min_weight = float('inf')
        min_node = unvisited[0]

        for node in unvisited:
            if weight[node] < min_weight:
                min_weight = weight[node]
                min_node = node

        return min_node

    def shortest_path(self, destination):
        if self.weight[destination] is float('inf'):
            print('No paths (check connectivity to source)')
            return

        # set current node to destination and add to path (where reverse path starts)
        current = destination
        path = [current]

        # while there is a previous node, append previous to path
        while current:
            current = self.previous[current]
            if current:
                path.append(current)

        # reverse path and return
        path = path[::-1]
        return path, self.weight[destination]

    def all_shortest_paths(self):
        shortest_paths = {}
        for key in self.weight:
            shortest_paths[key] = (self.shortest_path(key))

        return shortest_paths

    @staticmethod
    def is_connected(network, nodes_encountered=None, source=None):
        """
        Returns bool indicating graph connectivity (path between all nodes).
        This is a recursive DFS.

        :param network: object representing a graph (network)
        :param set nodes_encountered: set of node_id's encountered (None by default)
        :param int source: node_id of start of search (None by default)

        :return: bool indicating graph connectivity
        :rtype: bool
        """
        if nodes_encountered is None:
            nodes_encountered = set()
        nodes = network.nodes()
        if not source:
            # chose a vertex from network as start point
            source = nodes[0]
        nodes_encountered.add(source)
        if len(nodes_encountered) != len(nodes):
            for node in network.network_dict[source].get_adjacents():
                if node not in nodes_encountered:
                    if Dijkstra.is_connected(network, nodes_encountered, node):
                        return True
        else:
            return True
        return False

    @staticmethod
    def DFS(network, node_id=None):
        """
        Returns bool indicating graph connectivity (path between all nodes).
        This is an iterative DFS.

        :param network: object representing a graph (network)
        :param int node_id: identifies node where search will start (None by default)

        :return: bool indicating graph connectivity
        :rtype: bool
        """
        nodes_encountered = set()
        if not node_id:
            node_id = network.nodes()[0]
        stack = [node_id]
        while stack:
            node = stack.pop()
            if node not in nodes_encountered:
                nodes_encountered.add(node)
                # TODO: this adds all adjacents - this will cause repeat visits
                stack.extend(network.network_dict[node].get_adjacents())

        if len(nodes_encountered) != len(network.nodes()):
            return False
        else:
            return True

    @staticmethod
    def BFS(network, node_id=None):
        """
        Returns bool indicating graph connectivity (path between all nodes).
        This is an iterative BFS.

        :param network: object representing a graph (network)
        :param int node_id: identifies node where search will start (None by default)

        :return: bool indicating graph connectivity
        :rtype: bool
        """
        # mark all the nodes as not visited (value is None)
        visited = dict.fromkeys(network.nodes())
        nodes_encountered = set()
        queue = []

        if not node_id:
            node_id = network.nodes()[0]

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
            for node in network.network_dict[node_id].get_adjacents():
                if visited[node] is None:
                    queue.append(node)
                    visited[node] = True
                    nodes_encountered.add(node)

        # if size of nodes_encountered equals size of nodes(), return True
        if len(nodes_encountered) == len(network.nodes()):
            return True
        else:
            return False

    # @staticmethod
    # def broken_dijkstra(network, source, destination):
    #     """
    #     Returns the shortest path between the initial node and the end
    #     node as well as the total cost of the path. If there is no
    #     path that exists which connects the given nodes, an error message
    #     is printed to the console.
    #
    #     :param network: object representing a graph (network)
    #     :param int source: identifies the source node
    #     :param int destination: identifies the destination node
    #
    #     :return: collection of node ID's that indicate the shortest path
    #         and the total cost of the given path
    #     :rtype: dict {'path': list, 'weight': int}
    #     """
    #     # shortest paths is a dict of nodes
    #     # whose value is a tuple of (previous node, weight)
    #     shortest_paths = {source: (None, 0)}
    #     current_node = source
    #     visited = set()
    #
    #     while current_node != destination:
    #         visited.add(current_node)
    #         destinations = network.network_dict[current_node].get_adjacents()
    #         weight_to_current_node = shortest_paths[current_node][1]
    #
    #         # for node in active adjacents
    #         for next_node in destinations:
    #             weight = network.network_dict[current_node].adjacency_dict[next_node]['weight'] \
    #                      + weight_to_current_node
    #
    #             # if next node hasn't been stored
    #             if next_node not in shortest_paths:
    #                 shortest_paths[next_node] = (current_node, weight)
    #
    #             # if next node has been stored
    #             else:
    #                 current_shortest_weight = shortest_paths[next_node][1]
    #
    #                 # if currently stored weight is greater than this path's weight
    #                 if current_shortest_weight > weight:
    #                     shortest_paths[next_node] = (current_node, weight)
    #
    #         # next destinations are nodes in shortest paths that haven't been visited
    #         next_destinations = {node: shortest_paths[node]
    #                              for node in shortest_paths if node not in visited}
    #         # if next destinations are empty
    #         if not next_destinations:
    #             return f'There is no path connecting Node ID: #{source} ' \
    #                 f'and Node ID: #{destination}.'
    #
    #         # next node is the destination with the lowest weight
    #         current_node = min(next_destinations, key=lambda k: next_destinations[k][1])
    #
    #     # Work back through destinations in shortest path
    #     path = []
    #     cumulative_weight = 0
    #
    #     while current_node:
    #         path.append(current_node)
    #         next_node = shortest_paths[current_node][0]
    #         cumulative_weight += shortest_paths[current_node][1]
    #         current_node = next_node
    #     # Reverse path
    #     path = path[::-1]
    #     shortest_path = {'path': path, 'weight': cumulative_weight}
    #     return shortest_path
