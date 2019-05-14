import copy
from typing import Set, Union

from network_simulator.Network import Network
from network_simulator.OrganList import OrganList
from network_simulator.WaitList import WaitList


class SubnetworkGenerator:
    @staticmethod
    def generate_subnetwork(network: Network, collection: Union[OrganList, WaitList]) -> Network:
        """
        Takes a graph and a collection and creates a subnetwork that
        only consists of nodes which are present in the collection.
        (generates a subnetwork of patients OR organs)
        
        :param Network network: global network of hospitals
        :param collection: list of patients OR organs
        :return: Network subnetwork filtered by the passed collection
        """
        subnetwork = SubnetworkGenerator.copy_network(network)
        SubnetworkGenerator.mark_network_inactive(subnetwork)
        active_nodes: Set[int] = set()

        if isinstance(collection, WaitList):
            for x in collection.wait_list:
                if x.location not in active_nodes:
                    active_nodes.add(x.location)
        elif isinstance(collection, OrganList):
            for x in collection.organ_list:
                if x.origin_location not in active_nodes:
                    active_nodes.add(x.origin_location)
        else:
            return NotImplemented

        for node in active_nodes:
            subnetwork.mark_node_active(node, feedback=False)

        return subnetwork

    @staticmethod
    def copy_network(network: Network) -> Network:
        """
        Takes a Network object and returns a deep copy of the network
        (this is what the subnetwork is built upon)
        
        :param Network network: network to be copied (global network)
        :return: Network copy
        """
        return copy.deepcopy(network)

    @staticmethod
    def mark_network_inactive(network: Network) -> None:
        """
        Marks all nodes in a given network inactive
        (this is the starting point for the subnetwork)
        
        :param Network network: graph that is the foundation for subnetworks
        """
        for node in network.nodes():
            network.mark_node_inactive(node, feedback=False)
