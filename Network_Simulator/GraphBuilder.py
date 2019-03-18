from Network_Simulator.Node import Node
from Network_Simulator.Network import Network
import random


class GraphBuilder:
    """
    A class that builds various types of networks (random, connected,
    disconnected, etc.)
    """

    def __init__(self):
        pass

    # TODO random parameter (seed)
    @staticmethod
    def generate_random_network(n):
        """
        Returns randomly generated network with n nodes.

        :param int n: number of nodes generated graph will contain

        :return: randomly generated network with N nodes
        :rtype: Network
        """
        network_dict = {}
        for x in range(1, n + 1):
            adjacency_dict = GraphBuilder.generate_random_adjacency_dict(x, n)
            node = Node(x, 'Node #' + str(x), adjacency_dict)
            network_dict[x] = node
        network = Network(network_dict)
        return network

    # TODO random parameter (seed)
    @staticmethod
    def generate_random_adjacency_dict(node_id, total_nodes):
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
        # same seed each run (temporarily for testing consistency)
        random.seed(1)
        adjacency_dict = {}
        for n in range(random.randint(5, 25)):
            random_node = random.randint(1, total_nodes)
            # ensures node doesn't add itself to adjacency_dict
            # or add a duplicate entry
            while node_id == random_node \
                    or any(random_node == x for x in adjacency_dict.keys()):
                random_node = random.randint(1, total_nodes)

            # updates adjacency dict to new format
            adjacency_dict[random_node] = {'weight': random.randint(1, 50), 'status': True}
        return adjacency_dict
