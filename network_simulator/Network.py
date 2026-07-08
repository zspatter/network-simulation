from typing import Dict, Iterator, List, Optional

from network_simulator.distance import estimate_transit_hours, haversine_km
from network_simulator.exceptions import GraphElementError
from network_simulator.Node import Node

nodes_to_remove = List[List[int]]


class Network:
    """
    A class representing a network (graph). A network is defined through
    a label and a collection of nodes (and their adjacency dicts).
    A network consists of a network dict that contains all of the
    nodes contained within the graph.

    Edge weight convention: every edge weight represents estimated transit
    time in hours (see network_simulator.distance for how real hospital
    networks derive this from coordinates). This matches the unit
    Organ.viability is expressed in, which is what makes shortest-path costs
    from Dijkstra directly comparable to an organ's remaining viability.
    Synthetic networks from GraphBuilder use arbitrary weights in the same
    unit for stress-testing purposes.
    """

    def __init__(self, network_dict: Optional[Dict[int, Node]] = None,
                 label: str = 'Default network label') -> None:
        """
        Creates an instance of a Network. This function ensures that
        the adjacency dicts of nodes mirror each other (undirected graph).
        Furthermore, this function ensures nodes present in an adjacency
        list are present in the graph.

        :param dict network_dict: {int node_id: Node, ...} (None by default)
        """

        if not network_dict:
            network_dict = {}

        to_remove: nodes_to_remove = list()

        # ensures adjacency lists mirror each other (undirected weighted edges)
        nodes = network_dict.keys()
        # iterates through all nodes
        for node in nodes:
            Network.mirror_adjacency_dicts(network_dict, node, to_remove)

        # remove edges to nodes that don't exist in graph
        for node, adjacent in to_remove:
            del network_dict[node].adjacency_dict[adjacent]

        self.network_dict: Dict[int, Node] = network_dict
        self.label: str = label
        # Per-source transit-hour maps, memoized. The network is static across a
        # simulation trial, so each source's transit is computed at most once
        # rather than once per round (see transit_from). Invalidated by any
        # topology/status mutation via _invalidate_transit_cache.
        self._transit_cache: Dict[int, Dict[int, float]] = {}

    def _invalidate_transit_cache(self) -> None:
        """Drops memoized transit maps after any topology or status change."""
        self._transit_cache.clear()

    def transit_from(self, source: int) -> Dict[int, float]:
        """
        Estimated transit time (hours) from `source` to every active node,
        memoized for the network's current topology.

        For a coordinate-bearing network (real hospital imports - every node has
        latitude/longitude), transit is the *direct* point-to-point estimate from
        coordinates: an organ is flown straight from the donor hospital to the
        recipient's, not routed hop-by-hop through intermediate hospitals. This
        both matches reality and avoids summing any per-trip fixed overhead once
        per hop (see network_simulator.distance). Measured against the real
        network, direct transit tracks the old Dijkstra path cost to within ~1%.

        For a synthetic network (GraphBuilder - arbitrary edge weights, no
        coordinates), the graph itself *is* the distance model, so transit falls
        back to a Dijkstra shortest-path sum.

        :param int source: node id an organ originates at
        :return: {node_id: transit_hours} over active nodes (unreachable -> inf)
        """
        cached = self._transit_cache.get(source)
        if cached is not None:
            return cached

        origin = self.network_dict[source]
        if origin.latitude is not None and origin.longitude is not None:
            transit = {
                node_id: estimate_transit_hours(haversine_km(
                        origin.latitude, origin.longitude, node.latitude, node.longitude))
                for node_id, node in self.network_dict.items()
                if node.status and node.latitude is not None and node.longitude is not None
            }
        else:
            # Local import avoids a circular dependency (Dijkstra imports Network).
            from network_simulator.Dijkstra import Dijkstra
            transit = Dijkstra.dijkstra(self, source)[0]

        self._transit_cache[source] = transit
        return transit

    @staticmethod
    def mirror_adjacency_dicts(network_dict: Dict[int, Node], node: int,
                               to_remove: nodes_to_remove) -> None:
        """
        :param dict network_dict: {int node_id: Node, ...}
        :param int node: current node
        :param to_remove: list of edges that cannot exist in graph
            (adjacent node isn't present) and will be removed from dict by caller
        """
        adjacents = network_dict[node].adjacency_dict.keys()

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

    # allows graphs to be iterated through (via active nodes)
    def __iter__(self) -> Iterator[int]:
        """
        Creates and returns a custom iterator for the network.
        This iterates through currently active nodes.

        :return: iterator
        """
        return iter(self.nodes())

    def nodes(self) -> List[int]:
        """
        Returns list of active nodes within the graph.

        :return: active nodes in graph
        :rtype: list
        """
        nodes = set(self.network_dict.keys())
        active_nodes = [node for node in nodes if self.network_dict[node].status]
        return sorted(active_nodes)

    def add_node(self, node: Node) -> None:
        """
        Adds a node to the graph, wiring up (in both directions) any edges its
        adjacency dict already names.

        :param Node node: node that will be added to the graph
        :raises GraphElementError: if a node with the same id is already present
        """
        if node.node_id in self.network_dict:
            raise GraphElementError(f'Node ID: #{node.node_id} is already present in this '
                                    f'network! This node could not be added.')

        self._invalidate_transit_cache()
        self.network_dict[node.node_id] = node
        # ensure each named edge is represented on the neighbour as well
        for key in node.adjacency_dict:
            self.network_dict[key].adjacency_dict[node.node_id] = node.adjacency_dict[key]

    def remove_node(self, node_id: int) -> None:
        """
        Removes the node with the passed node_id and every edge incident to it.

        :param int node_id: unique identifier within a given graph
        :raises GraphElementError: if the node is not present in the graph
        """
        if node_id not in self.network_dict:
            raise GraphElementError(f'Node ID: #{node_id} is not present in this network! '
                                    f'This node does not exist and could not be removed.')

        self._invalidate_transit_cache()
        # drop the mirrored edge stored on each neighbour, then the node itself
        for key in self.network_dict[node_id].get_adjacents():
            del self.network_dict[key].adjacency_dict[node_id]
        del self.network_dict[node_id]

    def add_edge(self, node_id1: int, node_id2: int, weight: int,
                 regional_weight: Optional[int] = None) -> None:
        """
        Adds an active edge between two nodes with a specified weight.

        :param int node_id1: unique identifier within a given graph
            (one of the vertices to be connected by the added edge)
        :param int node_id2: unique identifier within a given graph
            (one of the vertices to be connected by the added edge)
        :param int weight: cost associated with the edge
        :param int regional_weight: optional regional weight which can
                be included in the adjacency dicts
        :raises GraphElementError: if a node is missing/inactive or the edge already exists
        """
        if node_id1 not in self.network_dict or node_id2 not in self.network_dict:
            raise GraphElementError('One of the passed nodes does not exist! As a result, '
                                    'there cannot be an edge, so it cannot be added.')
        self.add_edge_to_dict(node_id1, node_id2, weight, regional_weight)

    def add_edge_to_dict(self, node_id1: int, node_id2: int, weight: int,
                         regional_weight: Optional[int] = None) -> None:
        """
        Writes an edge into both nodes' adjacency dicts, once the connecting
        nodes are confirmed active and no edge already exists.

        :param int node_id1: unique identifier within a given graph
            (one of the vertices to be connected by the added edge)
        :param int node_id2: unique identifier within a given graph
            (one of the vertices to be connected by the added edge)
        :param int weight: cost associated with the edge
        :param int regional_weight: optional regional weight which can
                be included in the adjacency dicts
        :raises GraphElementError: if a connecting node is inactive or the edge already exists
        """
        active_nodes = self.nodes()
        if node_id1 not in active_nodes or node_id2 not in active_nodes:
            raise GraphElementError('One of the connecting nodes is inactive! As a result, '
                                    'this edge cannot be added.')

        if node_id2 in self.network_dict[node_id1].get_adjacents() \
                or node_id1 in self.network_dict[node_id2].get_adjacents():
            raise GraphElementError(f'There already exists an edge between Node ID: '
                                    f'#{node_id1} and Node ID: #{node_id2}! This edge '
                                    f'could not be added.')

        self._invalidate_transit_cache()
        self.network_dict[node_id1].adjacency_dict[node_id2] = {'weight': weight, 'status': True}
        self.network_dict[node_id2].adjacency_dict[node_id1] = {'weight': weight, 'status': True}
        if regional_weight:
            self.network_dict[node_id1].adjacency_dict[node_id2]['regional weight'] = \
                regional_weight
            self.network_dict[node_id2].adjacency_dict[node_id1]['regional weight'] = \
                regional_weight

    def remove_edge(self, node_id1: int, node_id2: int) -> None:
        """
        Removes the edge between two nodes from the graph.

        :param int node_id1: unique identifier within a given graph
            (one of the vertices connected by the edge to be removed)
        :param int node_id2: unique identifier within a given graph
            (one of the vertices connected by the edge to be removed)
        :raises GraphElementError: if a node is missing or no edge connects them
        """
        if node_id1 not in self.network_dict or node_id2 not in self.network_dict:
            raise GraphElementError('One of the passed nodes does not exist! As a result, '
                                    'there cannot be an edge, so it cannot be removed.')
        self.remove_edge_from_dict(node_id1, node_id2)

    def remove_edge_from_dict(self, node_id1: int, node_id2: int) -> None:
        """
        Removes a shared edge from both nodes' adjacency dicts.

        :param int node_id1: unique identifier within a given graph
            (one of the vertices connected by the edge to be removed)
        :param int node_id2: unique identifier within a given graph
            (one of the vertices connected by the edge to be removed)
        :raises GraphElementError: if no edge connects the two nodes
        """
        # the edge must be present in both adjacency dicts (an undirected edge is mirrored)
        if node_id2 in self.network_dict[node_id1].adjacency_dict \
                and node_id1 in self.network_dict[node_id2].adjacency_dict:
            self._invalidate_transit_cache()
            del self.network_dict[node_id1].adjacency_dict[node_id2]
            del self.network_dict[node_id2].adjacency_dict[node_id1]
        else:
            raise GraphElementError(f'There is no edge connecting Node ID: #{node_id1} and '
                                    f'Node ID: #{node_id2}, so there is no edge to remove!')

    def mark_node_inactive(self, node_id: int) -> None:
        """
        Marks the node and all of its edges inactive (mirrored on neighbours).

        :param int node_id: unique identifier within a given graph
        :raises GraphElementError: if the node is missing or already inactive
        """
        if node_id not in self.network_dict:
            raise GraphElementError(f'Node ID: #{node_id} is not present in this network! '
                                    f'Node could not be marked inactive.')
        if not self.network_dict[node_id].status:
            raise GraphElementError(f'Node ID: #{node_id} is already inactive!')

        self.mark_node_edges_inactive(node_id)
        self.network_dict[node_id].status = False

    def mark_node_edges_inactive(self, node_id: int) -> None:
        """
        Marks all of the edges of the passed node inactive

        :param int node_id: unique identifier within a given graph
        """
        self._invalidate_transit_cache()
        # gathers list of adjacent node id's
        adjacency_dict = self.network_dict[node_id].get_adjacents()
        # marks all edges of node as inactive, and mirrors
        # the status on all adjacents edges connected to the node
        for key in adjacency_dict:
            self.network_dict[key].adjacency_dict[node_id]['status'] = False
            self.network_dict[node_id].adjacency_dict[key]['status'] = False

    def mark_node_active(self, node_id: int) -> None:
        """
        Marks the node active, reactivating each edge whose other endpoint is
        also active.

        :param int node_id: unique identifier within a given graph
        :raises GraphElementError: if the node is missing or already active
        """
        if node_id not in self.network_dict:
            raise GraphElementError(f'Node ID: #{node_id} is not present in this network! '
                                    f'Node could not be marked active.')
        if self.network_dict[node_id].status:
            raise GraphElementError(f'Node ID: #{node_id} is already active! '
                                    f'This node could not be marked active.')

        self._invalidate_transit_cache()
        for key in self.network_dict[node_id].adjacency_dict:
            if self.network_dict[key].status:
                self.network_dict[key].adjacency_dict[node_id]['status'] = True
                self.network_dict[node_id].adjacency_dict[key]['status'] = True
        self.network_dict[node_id].status = True

    def _shared_edge_exists(self, node_id1: int, node_id2: int) -> bool:
        """True iff an edge between the two nodes is present in both adjacency dicts."""
        return node_id2 in self.network_dict[node_id1].adjacency_dict \
            and node_id1 in self.network_dict[node_id2].adjacency_dict

    def mark_edge_inactive(self, node_id1: int, node_id2: int) -> None:
        """
        Marks the shared edge inactive in both adjacency dicts.

        :param int node_id1: unique identifier within a given graph
        :param int node_id2: unique identifier within a given graph
        :raises GraphElementError: if a node is missing, no shared edge exists,
            or the edge is already inactive
        """
        if node_id1 not in self.network_dict or node_id2 not in self.network_dict:
            raise GraphElementError('One of the passed nodes does not exist! As a result, '
                                    'there cannot be an edge, so it cannot be marked inactive.')
        if not self._shared_edge_exists(node_id1, node_id2):
            raise GraphElementError(f'There is not a shared edge between Node ID: #{node_id1} '
                                    f'and Node ID: #{node_id2}! As a result, the edge cannot '
                                    f'be marked inactive.')
        if not (self.network_dict[node_id1].adjacency_dict[node_id2]['status']
                and self.network_dict[node_id2].adjacency_dict[node_id1]['status']):
            raise GraphElementError(f'The edge connecting Node ID: #{node_id1} and Node ID: '
                                    f'#{node_id2} is already inactive! As a result, the edge '
                                    f'cannot be marked inactive.')

        self._invalidate_transit_cache()
        self.network_dict[node_id1].adjacency_dict[node_id2]['status'] = False
        self.network_dict[node_id2].adjacency_dict[node_id1]['status'] = False

    def mark_edge_active(self, node_id1: int, node_id2: int) -> None:
        """
        Marks the shared edge active in both adjacency dicts.

        :param int node_id1: unique identifier within a given graph
        :param int node_id2: unique identifier within a given graph
        :raises GraphElementError: if a node is missing, no shared edge exists,
            a connecting node is inactive, or the edge is already active
        """
        if node_id1 not in self.network_dict or node_id2 not in self.network_dict:
            raise GraphElementError('One of the passed nodes does not exist! As a result, '
                                    'there cannot be an edge, so it cannot be marked active.')
        if not self._shared_edge_exists(node_id1, node_id2):
            raise GraphElementError(f'There is not a shared edge between Node ID: #{node_id1} '
                                    f'and Node ID: #{node_id2}! As a result, the edge cannot '
                                    f'be marked active.')
        if not (self.network_dict[node_id1].status and self.network_dict[node_id2].status):
            raise GraphElementError('One of the connecting nodes is inactive! As a result, '
                                    'this edge cannot be marked active.')
        if self.network_dict[node_id1].adjacency_dict[node_id2]['status'] \
                or self.network_dict[node_id2].adjacency_dict[node_id1]['status']:
            raise GraphElementError(f'The edge connecting Node ID: #{node_id1} and Node ID: '
                                    f'#{node_id2} is already active! As a result, the edge '
                                    f'cannot be marked active.')

        self._invalidate_transit_cache()
        self.network_dict[node_id1].adjacency_dict[node_id2]['status'] = True
        self.network_dict[node_id2].adjacency_dict[node_id1]['status'] = True

    def __str__(self) -> str:
        """
        Returns an easily readable (formatted) string representation of
        the instance. Only active nodes and edges are represented. This
        calls the Node.__str__ function.

        :return: easily readable string representation of the graph
        :rtype: str
        """
        string = ''
        for node_id in self.nodes():
            # if self.network_dict[key].status:
            string += f'{self.network_dict[node_id].__str__()}'
        return string + '\n===============================\n'
