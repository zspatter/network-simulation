import random
from typing import Dict, Optional, Union

from network_simulator.Network import Network
from network_simulator.Node import Node

edge_details = Dict[str, Union[int, bool]]
adj_dict = Dict[int, edge_details]


class GraphBuilder:
    """
    A class that builds networks with variable number of nodes
    and random adjacency lists
    """
    
    @staticmethod
    def graph_builder(n: int, max_weight: Optional[int] = None,
                      rng: Optional[random.Random] = None) -> Network:
        """
        Returns randomly generated network with n nodes.

        :param int n: number of nodes generated graph will contain
        :param int max_weight: optional param that sets a maximum weight for edges
        :param random.Random rng: optional random source (defaults to the
            shared global random module); pass a seeded instance for
            reproducible generation, e.g. in the benchmark harness

        :return: randomly generated network with N nodes
        :rtype: Network
        """

        network_dict = {}
        if not max_weight:
            max_weight = 50

        for x in range(1, n + 1):
            adjacency_dict = GraphBuilder.generate_random_adjacency_dict(x, n, max_weight, rng)
            node = Node(x, 'Node #' + str(x), adjacency_dict)
            network_dict[x] = node
        network = Network(network_dict)
        return network

    @staticmethod
    def generate_random_adjacency_dict(node_id: int, total_nodes: int, max_weight: int,
                                       rng: Optional[random.Random] = None) -> adj_dict:
        """
        Returns randomly generated adjacency dict for an instance of a node.
        The generated adjacency list can contain a connection to any node
        in the graph (except itself). This will prevent parallel edges from
        being generated. A random number of edges between 3 and 10 (inclusive)
        will be generated and a random weight between 1 and 50 (inclusive)
        will be assigned to each edge.
        This is called by the generate_network function.

        :param int node_id: unique identifier for the node that the
            adjacency dict is being generated for
        :param int max_weight: optional param that sets a maximum weight for edges
        :param int total_nodes: total number of nodes present in the generated graph
        :param random.Random rng: optional random source (defaults to the
            shared global random module); pass a seeded instance for
            reproducible generation, e.g. in the benchmark harness

        :return: randomly generated adjacency_dict
        :rtype: dict
        """

        # prevents infinite loop resulting from fewer total nodes than randomly generated bound
        adjacent_bound = 8
        bound = total_nodes - 1 if total_nodes <= adjacent_bound else adjacent_bound

        source = rng or random
        adjacency_dict: adj_dict = {}
        for _ in range(source.randint(3, bound)):
            random_node = source.randint(1, total_nodes)
            # ensures node doesn't add itself or add a duplicate entry to adjacency_dict
            while node_id == random_node \
                    or any(random_node == x for x in adjacency_dict.keys()):
                random_node = source.randint(1, total_nodes)

            # updates adjacency dict to new format
            adjacency_dict[random_node] = {
                'weight': source.randint(1, max_weight),
                'status': True}
        return adjacency_dict
