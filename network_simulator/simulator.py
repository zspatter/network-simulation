import network_simulator.GraphBuilder as GraphB
import network_simulator.OrganAllocator as OA
import network_simulator.WaitList as WL
import network_simulator.OrganList as OL

network = None
wait_list = WL.WaitList()
organ_list = OL.OrganList()


def print_menu():
    print(f'\nMain Menu:\n'
          f'\t{"{:d}".format(1)} - Generate Network\n'
          f'\t{"{:d}".format(2)} - Generate Patients\n'
          f'\t{"{:d}".format(3)} - Harvest Organs (and allocate)\n'
          f'\t{"{:d}".format(4)} - Reset Network (clears list of patients/organs)\n'
          f'\t{"{:d}".format(5)} - Restart\n'
          f'\t{"{:d}".format(0)} - Exit\n')


def main_menu():
    menu_option = None

    while menu_option != '0':
        print_menu()
        menu_option = input('Please select an option: ')

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
            print('Exiting!')
        else:
            print('Unrecognized menu selection. Try again!')


def build_network():
    global network
    global wait_list
    global organ_list

    if network:
        response = input('\nThere is already an existing network!\n'
                         'Would you like to clear the network? '
                         '(this will clear patient and organ lists as well)\n'
                         '(y/n): ')
        if response.lower() == 'y':
            wait_list = WL.WaitList()
            organ_list = OL.OrganList()
        elif response.lower() == 'n':
            return
        else:
            print('\nUnrecognized selection. Returning to main menu.\n')
            return

    response = int(input('\nEnter the number of hospitals (nodes) you\'d like in the network: '))
    network = GraphB.GraphBuilder.graph_builder(response)

    # network has been generated
    response = input(f'\nA network has been built with {response} nodes.'
                     f'\nWould you like to print the network to the console? \n(y/n): ')
    if response.lower() == 'y':
        print(network)
    elif response.lower() == 'n':
        return
    else:
        print('\nUnrecognized selection. Returning to main menu.\n')


def generate_patients():
    global network
    global wait_list

    if network:
        response = int(input('\nHow many patients would you like to generate? '))
        wait_list.generate_patients(network, response)
    else:
        print('\nThere is no network - one must be built before patients can be generated!')
        return

    # patients generated
    response = input(f'\n{response} patients have has been generated. '
                     f'\nWould you like to print the wait list to the console? \n(y/n): ')
    if response.lower() == 'y':
        print('\n' + wait_list.__str__())
    elif response.lower() == 'n':
        return
    else:
        print('\nUnrecognized selection. Returning to main menu.\n')


def harvest_organs():
    global network
    global organ_list

    if network:
        if len(wait_list.wait_list) is not 0:
            response = int(input('\nHow many patients would you like to harvest organs from? '))
            organ_list.generate_organs(network, response)
        else:
            print('\nThere are no patients. Patients must be generated '
                  'before organs can be harvested/allocated.')
            return
    else:
        print('\nThere is no network. A network must be built and patients '
              'must be generated before organs can be harvested/allocated')
        return

    # organs have been harvested
    response = input(f'\nOrgans have been harvested from {response} bodies. '
                     f'\nWould you like to print the organs to the console? (y/n): ')
    if response.lower() == 'y':
        print(organ_list)
        print('\nUnrecognized selection. Returning to main menu.\n')
    elif response.lower() == 'n':
        pass
    else:
        return
    allocate_organs()


def allocate_organs():
    organ_num = len(organ_list.organ_list)
    start_patient_num = len(wait_list.wait_list)
    input('\nPress ENTER to allocate organs')
    OA.OrganAllocator.allocate_organs(organ_list, wait_list, network)
    end_patient_num = len(wait_list.wait_list)
    print(f'\nSummary:\n'
          f'\t{start_patient_num - end_patient_num} organs have been transplanted\n'
          f'\t{organ_num - (start_patient_num - end_patient_num)} organs had no suitable match\n'
          f'\t{end_patient_num} patients remain on the wait list\n')


def reset_network():
    global organ_list
    global wait_list

    organ_list = OL.OrganList()
    wait_list = WL.WaitList()

    print('\nThe network has been reset. There are no patients or organs remaining in the network.')


def restart():
    global network
    global organ_list
    global wait_list

    network = None
    organ_list = OL.OrganList()
    wait_list = WL.WaitList()

    print('\nThe system has been reset. There is no network, patients, or organs.')


main_menu()
