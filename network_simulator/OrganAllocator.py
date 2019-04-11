import network_simulator.Dijkstra as D


class OrganAllocator:

    @staticmethod
    def allocate_organs(organ_list, wait_list, network):
        # ANSI codes to emphasize output
        bold, reset = '\033[1m', '\033[0m'
        source, weights, recipient = None, None, None

        for organ in organ_list.organ_list:
            if organ.origin_location is source:
                recipient = OrganAllocator.find_best_match(organ, wait_list, weights)
            else:
                source = organ.origin_location
                weights, paths = D.Dijkstra.dijkstra(network, source)
                recipient = OrganAllocator.find_best_match(organ, wait_list, weights)

            if recipient:
                organ.move_organ(recipient.location, weights[recipient.location])
                wait_list.remove_patient(recipient)
                print(f'\n{bold}The following pair have been united:{reset}'
                      f'\n{recipient.__str__()}{organ.__str__()}')

            # organ is always removed (either matched, or exceeds max viability)
            organ_list.empty_list()

    @staticmethod
    def find_best_match(organ, wait_list, weights):
        # ANSI codes to emphasize output
        bold_red, red, reset = '\033[31;1m', '\033[31m', '\033[0m'
        matches = wait_list.get_prioritized_patients(organ)

        # returns the patient with the highest priority within acceptable proximity
        for patient in matches:
            if organ.viability >= weights[patient.location] - 10:
                return patient

        # in the event there are no matches
        print(f'\n{bold_red}The following organ has no suitable matches:'
              f'\n{red}{organ.__str__()}{reset}')
        return None
