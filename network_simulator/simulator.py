import network_simulator.GraphBuilder as GraphB
import network_simulator.OrganAllocator as OA
import network_simulator.WaitList as WL
import network_simulator.OrganList as OL

network = None
wait_list = WL.WaitList()
organ_list = OL.OrganList()
ANSI_YELLOW = '\033[33m'
ANSI_YELLOW_BOLD = '\033[33;1m'
ANSI_BOLD = '\033[1m'
ANSI_RESET = '\033[0m'


def print_menu():
    print(f'\033[33mMain Menu:\n'
          f'\t{"{:d}".format(1)} - Generate Network\n'
          f'\t{"{:d}".format(2)} - Generate Patients\n'
          f'\t{"{:d}".format(3)} - Harvest Organs (and allocate)\n'
          f'\t{"{:d}".format(4)} - Reset Network (clears list of patients/organs)\n'
          f'\t{"{:d}".format(5)} - Restart\n'
          f'\t{"{:d}".format(0)} - Exit\033[0m\n')


def main_menu():
    menu_option = None
    global ANSI_YELLOW
    global ANSI_BOLD
    global ANSI_RESET
    ansi_red = '\033[31;1m'

    while menu_option != '0':
        print_menu()
        menu_option = input(f'Please select an option: ')

        if menu_option == '1':
            build_network()
        elif menu_option == '2':
            generate_patients()
        elif menu_option == '3':
            harvest_organs()
        elif menu_option == '4':
            reset_network()
        elif menu_option == '5':
            restart()
        elif menu_option == '0':
            print(f'\n{ansi_red}Exiting!{ANSI_RESET}')
        else:
            print(f'{ANSI_BOLD}Unrecognized menu selection. Try again!{ANSI_RESET}')


def build_network():
    global network
    global wait_list
    global organ_list

    if network:
        response = input(f'\nThere is already an existing network!\n'
                         f'Would you like to clear the network? '
                         f'(this will clear patient and organ lists as well)\n'
                         f'{ANSI_YELLOW}(y/n): {ANSI_RESET}')
        if response.lower() == 'y':
            wait_list = WL.WaitList()
            organ_list = OL.OrganList()
        elif response.lower() == 'n':
            print()
            return
        else:
            print(f'\n{ANSI_BOLD}Unrecognized selection. Returning to '
                  f'main menu.{ANSI_RESET}\n')
            return

    response = int(input(f'\nEnter the number of hospitals (nodes) '
                         f'you\'d like in the network: '))
    network = GraphB.GraphBuilder.graph_builder(response)

    # network has been generated
    response = input(f'\nA network has been built with {response} nodes.'
                     f'\nWould you like to print the network to the console?'
                     f'\n{ANSI_YELLOW}(y/n): {ANSI_RESET}')
    if response.lower() == 'y':
        print(network)
    elif response.lower() == 'n':
        print()
        return
    else:
        print(f'\n{ANSI_BOLD}Unrecognized selection. Returning to '
              f'main menu.\n{ANSI_RESET}')


def generate_patients():
    global network
    global wait_list

    if network:
        response = int(input(f'\nHow many patients would you like to generate? '))
        wait_list.generate_patients(network, response)
    else:
        print(f'\n{ANSI_BOLD}There is no network - one must be built before'
              f' patients can be generated!{ANSI_RESET}\n')
        return

    # patients generated
    response = input(f'\n{response} patients have has been generated. '
                     f'\nWould you like to print the wait list to the console?'
                     f'\n{ANSI_YELLOW}(y/n): {ANSI_RESET}')
    if response.lower() == 'y':
        print(f'\n{wait_list.__str__()}')
    elif response.lower() == 'n':
        print()
        return
    else:
        print(f'\n{ANSI_BOLD}Unrecognized selection. Returning to '
              f'main menu.{ANSI_RESET}\n')


def harvest_organs():
    global network
    global organ_list

    if network:
        if len(wait_list.wait_list) is not 0:
            response = int(input('\nHow many patients would you like '
                                 'to harvest organs from? '))
            organ_list.generate_organs(network, response)
        else:
            print(f'\n{ANSI_BOLD}There are no patients. Patients must be generated '
                  f'before organs can be harvested/allocated{ANSI_RESET}\n.')
            return
    else:
        print(f'\n{ANSI_BOLD}There is no network. A network must be built and patients '
              f'must be generated before organs can be harvested/allocated{ANSI_RESET}\n')
        return

    # organs have been harvested
    response = input(f'\nOrgans have been harvested from {response} bodies. '
                     f'\nWould you like to print the organs to the console?'
                     f'\n{ANSI_YELLOW}(y/n): {ANSI_RESET}')
    if response.lower() == 'y':
        print(f'\n{organ_list.__str__()}')
    elif response.lower() == 'n':
        print()
        pass
    else:
        return
    allocate_organs()


def allocate_organs():
    global ANSI_YELLOW_BOLD

    organ_num = len(organ_list.organ_list)
    start_patient_num = len(wait_list.wait_list)
    input(f'{ANSI_YELLOW}Press ENTER to allocate organs{ANSI_RESET}')
    OA.OrganAllocator.allocate_organs(organ_list, wait_list, network)
    end_patient_num = len(wait_list.wait_list)
    difference = start_patient_num - end_patient_num
    print(f'\n{ANSI_YELLOW_BOLD}Summary:'
          f'\n\t{start_patient_num - end_patient_num}{ANSI_YELLOW} organs '
          f'have been transplanted\n\t{ANSI_YELLOW_BOLD}'
          f'{organ_num - difference}{ANSI_YELLOW} organs had no suitable match'
          f'\n\t{ANSI_YELLOW_BOLD}{end_patient_num}{ANSI_YELLOW} '
          f'patients remain on the wait list{ANSI_RESET}\n')


def reset_network():
    global organ_list
    global wait_list

    organ_list = OL.OrganList()
    wait_list = WL.WaitList()

    print(f'\n{ANSI_BOLD}The network has been reset. There are no '
          f'patients or organs remaining in the network.{ANSI_RESET}')


def restart():
    global network
    global organ_list
    global wait_list

    network = None
    organ_list = OL.OrganList()
    wait_list = WL.WaitList()

    print(f'\n{ANSI_BOLD}The system has been reset. There is no network,'
          f' patients, or organs.{ANSI_RESET}')


main_menu()
