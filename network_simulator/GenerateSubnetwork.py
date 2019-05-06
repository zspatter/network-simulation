from network_simulator.WaitList import WaitList
from network_simulator.OrganList import OrganList
import copy


class GenerateSubnetwork:
    @staticmethod
    def generate_subnetwork(network, collection):
        subnetwork = GenerateSubnetwork.copy_network(network)
        GenerateSubnetwork.mark_network_inactive(subnetwork)
        active_nodes = set()
        # print('waitlist: ', isinstance(collection, WaitList))
        # print('organlist: ', isinstance(collection, OrganList))

        if isinstance(collection, WaitList):
            for x in collection.wait_list:
                if x.location not in active_nodes:
                    active_nodes.add(x.location)
        elif isinstance(collection, OrganList):
            for x in collection.organ_list:
                if x.origin_location not in active_nodes:
                    active_nodes.add(x.origin_location)
        else:
            return None

        for node in active_nodes:
            subnetwork.mark_node_active(node, feedback=False)

        return subnetwork


    @staticmethod
    def copy_network(network):
        return copy.deepcopy(network)

    @staticmethod
    def mark_network_inactive(network):
        for node in network.nodes():
            network.mark_node_inactive(node, feedback=False)
