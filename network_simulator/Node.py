from typing import Dict, Union, List, Optional

edge_details = Dict[str, Union[int, bool]]
adj_dict = Dict[int, edge_details]

neighbor_regions = {1:  [9],
                    2:  [9, 10, 11],
                    3:  [4, 8, 11],  # 3 -> 8?
                    4:  [3, 5, 8],
                    5:  [4, 6, 8],
                    6:  [5, 7, 8],
                    7:  [6, 8, 10],  # 7 -> 11?
                    8:  [3, 4, 5, 6, 7],  # 8 -> 11?
                    9:  [1, 2],
                    10: [2, 7, 11],
                    11: [2, 3, 10]}  # 11 -> 7/8?


# Hawaii and Alaska handling?


class Node:
    """
    A class representing a given node/vertex. A node is defined through
    a unique node ID, label, and adjacency dict that contains all of the
    neighboring nodes along with the weight associated with the shared
    edge, and a status that marks active/inactive nodes.
    """

    def __init__(self, node_id: int, label: str = 'Default node label',
                 adjacency_dict: adj_dict = None, status: bool = None,
                 region: Optional[int] = None, city: Optional[str] = None,
                 state: Optional[str] = None) -> None:
        """
        Creates an instance of a Node

        :param int node_id: unique identifier within a given graph
        :param int/str label: name associated with a node
        :param dict adjacency_dict: {int node_id: {'weight': int, 'status': bool}, ...}
            (None by default)
        :param bool status: flag indicating whether a node is active or inactive
            (None by default)
        :param int region: US organ network region (1-11)
        :param str city: string representation of city
        :param str state: string representation of state
        """
        self.node_id: int = node_id
        self.label: str = label
        self.adjacency_dict: adj_dict
        self.status: bool
        self.region: Optional[int] = region
        self.city: Optional[str] = city
        self.state: Optional[str] = state

        if not adjacency_dict:
            adjacency_dict = {}
        self.adjacency_dict = adjacency_dict

        if status is False:
            for key in adjacency_dict:
                adjacency_dict[key]['status'] = False

        if status is None:
            status = True
        self.status = status

    def is_adjacent(self, node_id: int) -> bool:
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

    def get_adjacents(self) -> List[int]:
        """
        Returns list of adjacent nodes. Nodes are only added to the list
        if they are currently active, and the edge connecting the nodes
        is currently active

        :return: active adjacent nodes
        :rtype: list
        """
        adjacents: List[int] = list()
        if self.status:
            adjacents = [key for key in self.adjacency_dict if self.adjacency_dict[key]['status']]
        return adjacents

    def __str__(self) -> str:
        """
        Returns an easily readable (formatted) string representation of the instance.
        Only active edges are represented. If the node is inactive,
        nothing is returned.

        :return: easily readable string representation of the node
        :rtype: str
        """
        if self.status:

            string = f"\n{'Node ID:':<10}{self.node_id:05d}" \
                f"\n{'Label:':<10}{self.label}" \
                f"\n{'Region:':<10}{self.region}" \
                f"\n{'Location:':<10}{self.city}, {self.state}" \
                f"\nNeighbors:"

            for key in self.adjacency_dict:
                if self.adjacency_dict[key]['status']:
                    string += f"\n\tNode {'#' + str(key):>6}:" \
                        f"\t{self.adjacency_dict[key]['weight']:>2}"
            return string + '\n'
        return ''
