import network_simulator.GraphBuilder as GraphB
import network_simulator.OrganAllocator as oA
import network_simulator.OrganList as oL
import network_simulator.WaitList as wL

network, wait_list, organ_list = None, wL.WaitList(), oL.OrganList()
ANSI_YELLOW, ANSI_YELLOW_BOLD, ANSI_RED = '\033[33m', '\033[33;1m', '\033[31m'
ANSI_RED_BOLD, ANSI_BOLD, ANSI_RESET = '\033[31;1m', '\033[1m', '\033[0m'


def print_menu():
    """
    Prints menu options
    """
    print(f'{ANSI_YELLOW}Main Menu:{ANSI_RESET}\n'
          f'\t{ANSI_YELLOW}1 -{ANSI_RESET} Generate Network\n'
          f'\t{ANSI_YELLOW}2 -{ANSI_RESET} Generate Patients\n'
          f'\t{ANSI_YELLOW}3 -{ANSI_RESET} Harvest Organs (and allocate)\n'
          f'\t{ANSI_YELLOW}4 -{ANSI_RESET} Reset Network (clears list of patients/organs)\n'
          f'\t{ANSI_YELLOW}5 -{ANSI_RESET} Restart\n'
          f'\t{ANSI_YELLOW}0 -{ANSI_RESET} Exit\n')


def main_menu():
    """
    Control structure executes each action corresponding to menu items.
    Loops until user enters 0 to exit.
    """
    global ANSI_YELLOW
    global ANSI_BOLD
    global ANSI_RED
    global ANSI_RED_BOLD
    global ANSI_RESET
    menu_option = None

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
            print(f'\n{ANSI_RED_BOLD}Exiting!{ANSI_RESET}')
        else:
            print(f'\n{ANSI_BOLD}Unrecognized menu selection. Try again!{ANSI_RESET}\n')


def build_network():
    """
    Builds a network passing console input as GraphBuilder parameters (N nodes).
    If a network already exists, a confirmation message verifies
    the user wants to clear the existing data.
    """
    global network
    global wait_list
    global organ_list

    if network:
        response = input(f'\nThere is already an existing network!\n'
                         f'Would you like to clear the network? '
                         f'(this will clear patient and organ lists as well)\n'
                         f'{ANSI_YELLOW}(y/n): {ANSI_RESET}')
        if response.lower() == 'y':
            wait_list = wL.WaitList()
            organ_list = oL.OrganList()
        elif response.lower() == 'n':
            print()
            return
        else:
            print(f'\n{ANSI_BOLD}Unrecognized selection. Returning to '
                  f'main menu.{ANSI_RESET}\n')
            return
    try:
        response = int(input(f'\nEnter the number of hospitals (nodes) '
                             f'you\'d like in the network: '))

        network = GraphB.GraphBuilder.graph_builder(response)
    except ValueError:
        print(f'\n{ANSI_RED_BOLD}ValueError:{ANSI_RED} valid values '
              f'are ints >= 4{ANSI_RESET}\n')
        return

    # network has been generated
    response = input(f'\nA network has been built with {response} nodes. '
                     f'Would you like to print the network to the console?'
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
    """
    Generates N patients in need of organ donations (who are added to the wait list).
    If there is no network present, an error prints and control is returned to the
    main menu loop.
    """
    global network
    global wait_list

    if network:
        try:
            response = int(input(f'\nHow many patients would you like to generate? '))
            wait_list.generate_patients(network, response)
        except ValueError:
            print(f'\n{ANSI_RED_BOLD}ValueError:{ANSI_RED} valid values '
                  f'are positive ints{ANSI_RESET}\n')
            return
    else:
        print(f'\n{ANSI_BOLD}There is no network - one must be built before'
              f' patients can be generated!{ANSI_RESET}\n')
        return

    # patients generated
    response = input(f'\n{response} patients have been generated. '
                     f'Would you like to print the wait list to the console?'
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
    """
    Harvests organs from N patients assuming there is a network and a
    wait list of at least 1 patient. These conditions must be met as
    organs are allocated to patients in need across the network as soon
    as they are harvested.
    """
    global network
    global organ_list

    if network:
        if len(wait_list.wait_list) is not 0:
            try:
                response = int(input('\nHow many patients would you like '
                                     'to harvest organs from? '))
                organ_list.generate_organs(network, response)
            except ValueError:
                print(f'\n{ANSI_RED_BOLD}ValueError:{ANSI_RED} valid values '
                      f'are positive ints{ANSI_RESET}\n')
                return
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
                     f'Would you like to print the organs to the console?'
                     f'\n{ANSI_YELLOW}(y/n): {ANSI_RESET}')
    if response.lower() == 'y':
        print(f'\n{organ_list.__str__()}')
    else:
        print()
    allocate_organs()


def allocate_organs():
    """
    Allocates organs to the most optimal patient matches. The pause is
    to separate harvesting of organs from their allocation. A brief summary
    is printed after all organs have been allocated.
    """
    global ANSI_YELLOW_BOLD
    ansi_cyan = '\033[36m'

    organ_num = len(organ_list.organ_list)
    start_patient_num = len(wait_list.wait_list)

    input(f'{ANSI_YELLOW}Press ENTER to allocate organs{ANSI_RESET}')
    oA.OrganAllocator.allocate_organs(organ_list, wait_list, network)

    end_patient_num = len(wait_list.wait_list)
    difference = start_patient_num - end_patient_num

    print('\n{:s}Summary:'
          '\n\t{:>3s} organs have been transplanted'
          '\n\t{:>3s} organs had no suitable match'
          '\n\t{:>3s} patients remain on the wait list{:s}\n'.format(ansi_cyan,
                                                                     str(difference),
                                                                     str(organ_num - difference),
                                                                     str(end_patient_num),
                                                                     ANSI_RESET))


def reset_network():
    """
    Resets the network by clearing the organ list and wait list variables.
    This leaves an empty network to continue interacting with.
    """
    global organ_list
    global wait_list

    organ_list = oL.OrganList()
    wait_list = wL.WaitList()

    print(f'\n{ANSI_BOLD}The network has been reset. There are no '
          f'patients or organs remaining in the network.{ANSI_RESET}\n')


def restart():
    """
    Clears all data from the system. This removes the existing network,
    wait list, and organ list.
    """
    global network
    global organ_list
    global wait_list

    network = None
    organ_list = oL.OrganList()
    wait_list = wL.WaitList()

    print(f'\n{ANSI_BOLD}The system has been reset. There is no network,'
          f' patients, or organs.{ANSI_RESET}\n')


main_menu()
