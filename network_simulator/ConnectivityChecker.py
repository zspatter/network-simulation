class ConnectivityChecker:
    """
    This class determines whether a given network is connected or not.

    In a connected network, there exists a path between any given node
    and all other nodes (no nodes exist that cannot be reached)
    """

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
                    if ConnectivityChecker.is_connected(network, nodes_encountered, node):
                        return True
        else:
            return True
        return False

    @staticmethod
    def depth_first_search(network, node_id=None):
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
                stack.extend(network.network_dict[node].get_adjacents())

        if len(nodes_encountered) != len(network.nodes()):
            return False
        else:
            return True

    @staticmethod
    def breadth_first_search(network, node_id=None):
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
