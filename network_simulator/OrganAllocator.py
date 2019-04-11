import network_simulator.Dijkstra as D


class OrganAllocator:

    @staticmethod
    def allocate_organs(organ_list, wait_list, network):
        source, weights, recipient = None, None, None
        for organ in organ_list.organ_list:
            if organ.origin_location is source:
                recipient = OrganAllocator.find_best_match(organ, wait_list, weights)
            else:
                source = organ.origin_location
                weights, paths = D.Dijkstra.dijkstra(network, source)
                recipient = OrganAllocator.find_best_match(organ, network, source)

            if recipient:
                organ.move_organ(recipient.location, weights[recipient.location])
                wait_list.remove_patient(recipient)
                print('The following pair have been united:\n'
                      + recipient.__str__() + organ.__str__())

            # organ is always removed (either matched, or exceeds max viability)
            organ_list.remove_organ(organ)

    @staticmethod
    def find_best_match(organ, wait_list, weights):
        matches = wait_list.get_prioritized_patients(organ)
        for patient in matches:
            if organ.viability >= weights[patient.location] - 10:
                return patient

        print('\033[31;1m' + 'The following organ has no suitable matches:\n'
              + '\033[0m' + organ.__str__())

        return None
