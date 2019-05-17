from typing import List, Dict, Tuple, Optional, Union

from network_simulator.Network import Network

node_id = int
weight_structure = Dict[int, float]
previous_structure = Dict[int, Union[int, None]]
dijkstra_structure = Tuple[weight_structure, previous_structure]
path_structure = Optional[List[Optional[int]]]
shortest_path_structure = Tuple[path_structure, float]
all_paths = Dict[node_id, Tuple[path_structure, float]]


class Dijkstra:
    """
    A class which will be used to analyze graphs. This class determines shortest
    paths and cumulative weights for various paths.

    This can find all shortest paths from a given source node to all other nodes.
    """
    
    def __init__(self, graph: Network, source: int) -> None:
        self.weight: weight_structure
        self.previous: previous_structure
        
        self.source: int = source
        self.weight, self.previous = Dijkstra.dijkstra(graph, source)
    
    @staticmethod
    def dijkstra(graph: Network, source: int) -> dijkstra_structure:
        """
        This function finds the shortest path to all connected nodes
        from a given source node. The return are two dicts:
            1) the weight from source to the key
            2) the node preceding the key

        This function is intended to be used by the initializer when
        creating and Dijkstra instance. The output will be stored as
        attributes of the object. These structures can be referenced later
        to determine the shortest path (and cost) to a given destination

        :param graph: network which will be used for path finding
        :param source: source node (where all paths will start)

        :return: weight: dict represented as {node_id: <weight>, ...}
        :return: previous: dict represented as {node_id: <previous_node_id>, ...}
        """
        unvisited = graph.nodes()
        weight = dict.fromkeys(graph.nodes(), float('inf'))
        previous: Dict[int, Union[int, None]] = dict.fromkeys(graph.nodes(), None)
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
    def minimum_unvisited_distance(unvisited: List[int], weight: weight_structure) -> node_id:
        """
        Helper method used by dijkstra (function) to determine which
        node should be traversed next
        (the node with the lowest weight which hasn't already been visited)

        :param list unvisited: list of node_ids which haven't been visited
        :param dict weight: dict of weights associated with traveling to each node

        :return: node_id corresponding to the least costly unvisited node
        """
        min_weight = float('inf')
        min_node = unvisited[0]
        
        for node in unvisited:
            if weight[node] < min_weight:
                min_weight = weight[node]
                min_node = node
        
        return min_node
    
    def shortest_path(self, destination: int) -> shortest_path_structure:
        """
        Returns both the shortest path and the cost of said path between
        this object's source (attribute) and the passed destination.

        If the source and destination are disconnected, the path returned
        is None and the weight returned is infinity

        :param int destination: represents the destination's node_id
        :return: list of node_id's which represent the shortest path between
                    the source and destination and an int representing the  weight
        """
        if self.weight[destination] == float('inf'):
            print('No paths (check connectivity to source)')
            return None, float('inf')
        
        # set current node to destination and add to path (where reverse path starts)
        current: Union[int, None] = destination
        path = [current]
        
        # while there is a previous node, append previous to path
        while current:
            current = self.previous[current]
            if current:
                path.append(current)
        
        # reverse path and return
        path = path[::-1]
        return path, self.weight[destination]
    
    def all_shortest_paths(self) -> all_paths:
        """
        Harnesses the functionality of shortest_path() to gather all shortest
        paths and store them in a dictionary

        :return: dict in the form {node_id: ([path], weight), ...} which can easily be unpacked
        """
        shortest_paths = {}
        for key in self.weight:
            shortest_paths[key] = (self.shortest_path(key))

        return shortest_paths
