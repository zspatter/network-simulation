import heapq
from typing import Dict, Optional

from network_simulator.Dijkstra import Dijkstra
from network_simulator.Network import Network
from network_simulator.Organ import Organ
from network_simulator.OrganList import OrganList
from network_simulator.Patient import Patient
from network_simulator.WaitList import WaitList


class OrganAllocator:
    """
    A class that automates the allocation process for harvested organs

    Organs are matched to the patient with the highest priority value
    who is a compatible recipient (blood type)
    """

    @staticmethod
    def allocate_organs(organ_list: OrganList, wait_list: WaitList,
                        network: Network) -> None:
        """
        Allocates organs from an OrganList to patients on a WaitList in a given Network.
        Organs are  allocated to the patient with the highest priority within a a suitable proximity.
        The proximity is considered suitable iff  (organ viability) - (cost of travel) >= 10

        :param OrganList organ_list: list of organs available for transplant
        :param WaitList wait_list: list of patients in need of transplant
        :param Network network: hospital network patients and organs are present in
        """
        # ANSI codes to emphasize output
        bold, reset = '\033[1m', '\033[0m'
        source, recipient = None, None

        for organ in organ_list.organ_list:
            if organ.origin_location is source:
                recipient = OrganAllocator.find_best_match(organ, wait_list, dijkstra.weight)
            else:
                source = organ.origin_location
                dijkstra = Dijkstra(network, source)
                recipient = OrganAllocator.find_best_match(organ, wait_list, dijkstra.weight)

            if recipient:
                organ.move_organ(recipient.location, dijkstra.weight[recipient.location],
                                 dijkstra.shortest_path(recipient.location))
                wait_list.remove_patient(recipient)
                print(f'\n{bold}The following pair have been united:{reset}'
                      f'\n{recipient.__str__()}{organ.__str__()}')

            # organ is always removed (either matched, or exceeds max viability)
            organ_list.empty_list()

    @staticmethod
    def find_best_match(organ: Organ, wait_list: WaitList,
                        weights: Dict[int, float]) -> Optional[Patient]:
        """
        Finds the most optimal patient match for a given organ. The optimal match
        is the patient with the highest priority rating of compatible organ_need/blood_type
        who is within a tolerable distance (for organ viability)

        :param Organ organ: individual organ which is being matched with the optimal patient
        :param WaitList wait_list: list of patients in need of a transplant
        :param dict weights: cumulative weights of shortest paths from source node (organ location)
                                to all other nodes in the network
        :return: Patient representing the most optimal match
        """
        # ANSI codes to emphasize output
        bold_red, red, reset = '\033[31;1m', '\033[31m', '\033[0m'
        matches = wait_list.get_prioritized_patients(organ)

        # returns the patient with the highest priority within acceptable proximity
        while len(matches) != 0:
            patient = heapq._heappop_max(matches)
            if organ.viability >= weights[patient.location] - 10:
                return patient

        # in the event there are no matches
        print(f'\n{bold_red}The following organ has no suitable matches:'
              f'\n{red}{organ.__str__()}{reset}')
        return None
