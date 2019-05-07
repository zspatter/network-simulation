import networkx as nx


class GraphConverter:

    @staticmethod
    def convert_to_networkx(network):
        nx_graph = nx.Graph()
        nodes = network.nodes()

        for node in nodes:
            adjacents = network.network_dict[node].get_adjacents()
            for adjacent in adjacents:
                if network.network_dict[node].adjacency_dict[adjacent]['status']:
                    weight = network.network_dict[node].adjacency_dict[adjacent]['weight']
                    nx_graph.add_edge(node, adjacent, weight=weight)

        return nx_graph
