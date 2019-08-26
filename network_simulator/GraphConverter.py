import networkx as nx  # type: ignore

from network_simulator.Network import Network


class GraphConverter:

    @staticmethod
    def convert_to_networkx(network: Network,
                            is_regional_weight: bool = None) -> nx.Graph:
        """
        Converts a Network object to a NetworkX graph

        :param Network network:
        :param bool is_regional_weight: indicates whether weight metric should
                be regional weight or distance
        :return: NetworkX Graph
        """
        nx_graph = nx.Graph()
        nodes = network.nodes()

        for node in nodes:
            nx_graph.add_node(node)
            GraphConverter.add_edges(network, node, nx_graph, is_regional_weight)

        return nx_graph

    @staticmethod
    def convert_to_attribute_nx(network: Network,
                                is_regional_weight: bool = None,
                                state_dict=None,
                                region_dict=None) -> nx.Graph:
        """
        Converts a Network object to a NetworkX graph

        :param Network network:
        :param bool is_regional_weight: indicates whether weight metric should
                be regional weight or distance
        :param dict state_dict: quanitfies how many hospitals share the state
        :param dict region_dict: quanitfies how many hospitals share the region
        :return: NetworkX Graph
        """
        nx_graph = nx.Graph()
        nodes = network.nodes()

        for node in nodes:
            state = network.network_dict[node].state
            state = 'Washington D.C.' if state == 'US' else state
            region = network.network_dict[node].region

            nx_graph.add_node(node,
                              state_count=state_dict[state],
                              region_count=region_dict[region])

            GraphConverter.add_edges(network, node, nx_graph, is_regional_weight)

        return nx_graph

    @staticmethod
    def add_edges(network, node, nx_graph, is_regional_weight):
        adjacents = network.network_dict[node].get_adjacents()
        for adjacent in adjacents:
            if network.network_dict[node].adjacency_dict[adjacent]['status']:
                weight = network.network_dict[node].adjacency_dict[adjacent]['weight'] \
                    if not is_regional_weight else \
                    network.network_dict[node].adjacency_dict[adjacent]['regional weight']
                nx_graph.add_edge(node, adjacent, weight=weight)
