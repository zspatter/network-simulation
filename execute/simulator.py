from organflow.allocation import STRATEGIES
from organflow.GraphBuilder import GraphBuilder
from organflow.OrganGenerator import OrganGenerator
from organflow.OrganList import OrganList
from organflow.PatientGenerator import PatientGenerator
from organflow.WaitList import WaitList

ANSI_YELLOW, ANSI_YELLOW_BOLD, ANSI_RED = '\033[33m', '\033[33;1m', '\033[31m'
ANSI_RED_BOLD, ANSI_BOLD, ANSI_RESET = '\033[31;1m', '\033[1m', '\033[0m'


class SimulatorSession:
    """
    Holds one interactive session's state (network, wait list, organ list, and
    the selected allocation strategy) and drives the console menu. State lives on
    the instance rather than in module globals, so a session can be created and
    driven programmatically - which is what makes the menu actions testable
    without mutating shared module state.
    """

    def __init__(self) -> None:
        self.network = None
        self.wait_list = WaitList()
        self.organ_list = OrganList()
        self.selected_strategy = STRATEGIES['baseline']

    def print_menu(self) -> None:
        """Prints menu options."""
        print(f'{ANSI_YELLOW}Main Menu:{ANSI_RESET}\n'
              f'\t{ANSI_YELLOW}1 -{ANSI_RESET} Generate Network\n'
              f'\t{ANSI_YELLOW}2 -{ANSI_RESET} Generate Patients\n'
              f'\t{ANSI_YELLOW}3 -{ANSI_RESET} Harvest Organs (and allocate)\n'
              f'\t{ANSI_YELLOW}4 -{ANSI_RESET} Reset Network (clears list of patients/organs)\n'
              f'\t{ANSI_YELLOW}5 -{ANSI_RESET} Restart\n'
              f'\t{ANSI_YELLOW}6 -{ANSI_RESET} Select Allocation Strategy '
              f'(current: {self.selected_strategy.name})\n'
              f'\t{ANSI_YELLOW}0 -{ANSI_RESET} Exit\n')

    def main_menu(self) -> None:
        """
        Control structure executes each action corresponding to menu items.
        Loops until user enters 0 to exit.
        """
        menu_option = None

        while menu_option != '0':
            self.print_menu()
            menu_option = input('Please select an option: ')

            if menu_option == '1':
                self.build_network()
            elif menu_option == '2':
                self.generate_patients()
            elif menu_option == '3':
                self.harvest_organs()
            elif menu_option == '4':
                self.reset_network()
            elif menu_option == '5':
                self.restart()
            elif menu_option == '6':
                self.select_strategy()
            elif menu_option == '0':
                print(f'\n{ANSI_RED_BOLD}Exiting!{ANSI_RESET}')
            else:
                print(f'\n{ANSI_BOLD}Unrecognized menu selection. Try again!{ANSI_RESET}\n')

    def build_network(self) -> None:
        """
        Builds a network passing console input as GraphBuilder parameters (N nodes).
        If a network already exists, a confirmation message verifies
        the user wants to clear the existing data.
        """
        if self.network:
            response = input(f'\nThere is already an existing network!\n'
                             f'Would you like to clear the network? '
                             f'(this will clear patient and organ lists as well)\n'
                             f'{ANSI_YELLOW}(y/n): {ANSI_RESET}')
            if response.lower() == 'y':
                self.wait_list = WaitList()
                self.organ_list = OrganList()
            elif response.lower() == 'n':
                print()
                return
            else:
                print(f'\n{ANSI_BOLD}Unrecognized selection. Returning to '
                      f'main menu.{ANSI_RESET}\n')
                return
        try:
            response = int(input('\nEnter the number of hospitals (nodes) '
                                 'you\'d like in the network: '))

            self.network = GraphBuilder.graph_builder(response)
        except ValueError:
            print(f'\n{ANSI_RED_BOLD}ValueError:{ANSI_RED} valid values '
                  f'are ints >= 4{ANSI_RESET}\n')
            return

        # network has been generated
        response = input(f'\nA network has been built with {response} nodes. '
                         f'Would you like to print the network to the console?'
                         f'\n{ANSI_YELLOW}(y/n): {ANSI_RESET}')
        if response.lower() == 'y':
            print(self.network)
        elif response.lower() == 'n':
            print()
            return
        else:
            print(f'\n{ANSI_BOLD}Unrecognized selection. Returning to '
                  f'main menu.\n{ANSI_RESET}')

    def generate_patients(self) -> None:
        """
        Generates N patients in need of organ donations (who are added to the wait list).
        If there is no network present, an error prints and control is returned to the
        main menu loop.
        """
        if self.network:
            try:
                response = int(input('\nHow many patients would you like to generate? '))
                PatientGenerator.generate_patients_to_list(self.network, response, self.wait_list)

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
            print(f'\n{self.wait_list.__str__()}')
        elif response.lower() == 'n':
            print()
            return
        else:
            print(f'\n{ANSI_BOLD}Unrecognized selection. Returning to '
                  f'main menu.{ANSI_RESET}\n')

    def harvest_organs(self) -> None:
        """
        Harvests organs from N patients assuming there is a network and a
        wait list of at least 1 patient. These conditions must be met as
        organs are allocated to patients in need across the network as soon
        as they are harvested.
        """
        if self.network:
            if len(self.wait_list.wait_list) != 0:
                try:
                    response = int(input('\nHow many patients would you like '
                                         'to harvest organs from? '))
                    OrganGenerator.generate_organs_to_list(self.network, response,
                                                           self.organ_list)

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
            print(f'\n{self.organ_list.__str__()}')
        else:
            print()
        self.allocate_organs()

    def allocate_organs(self) -> None:
        """
        Allocates organs to the most optimal patient matches using the currently
        selected strategy (see select_strategy()). The pause is to separate
        harvesting of organs from their allocation. A brief summary is printed
        after all organs have been allocated.
        """
        ansi_cyan = '\033[36m'
        bold, reset = '\033[1m', '\033[0m'
        bold_red, red = '\033[31;1m', '\033[31m'

        organ_num = len(self.organ_list.organ_list)

        input(f'{ANSI_YELLOW}Press ENTER to allocate organs{ANSI_RESET}')
        result = self.selected_strategy.allocate(self.organ_list, self.wait_list, self.network)

        for organ, patient in result.matches:
            print(f'\n{bold}The following pair have been united:{reset}'
                  f'\n{patient}{organ}')
        for organ in result.unmatched_organs:
            print(f'\n{bold_red}The following organ has no suitable matches:'
                  f'\n{red}{organ}{reset}')

        result.apply(self.wait_list, self.organ_list)
        self.wait_list.increment_wait_times()

        print('\n{:s}Summary:'
              '\n\t{:>3s} organs have been transplanted'
              '\n\t{:>3s} organs had no suitable match'
              '\n\t{:>3s} patients remain on the wait list{:s}\n'.format(
                      ansi_cyan,
                      str(len(result.matches)),
                      str(organ_num - len(result.matches)),
                      str(len(self.wait_list.wait_list)),
                      ANSI_RESET))

    def select_strategy(self) -> None:
        """
        Lets the user choose which allocation strategy allocate_organs() should
        use (see organflow.allocation.STRATEGIES). The selection
        persists across harvests until changed again.
        """
        print(f'\n{ANSI_YELLOW}Available strategies:{ANSI_RESET}')
        names = list(STRATEGIES.keys())
        for index, name in enumerate(names, start=1):
            marker = ' (current)' if STRATEGIES[name] is self.selected_strategy else ''
            print(f'\t{ANSI_YELLOW}{index} -{ANSI_RESET} {name}{marker}')

        response = input(f'\nSelect a strategy {ANSI_YELLOW}(1-{len(names)}): {ANSI_RESET}')
        try:
            index = int(response)
            if not 1 <= index <= len(names):
                raise ValueError
        except ValueError:
            print(f'\n{ANSI_RED_BOLD}ValueError:{ANSI_RED} valid values '
                  f'are ints between 1 and {len(names)}{ANSI_RESET}\n')
            return

        self.selected_strategy = STRATEGIES[names[index - 1]]
        print(f'\n{ANSI_BOLD}Strategy set to: {self.selected_strategy.name}{ANSI_RESET}\n')

    def reset_network(self) -> None:
        """
        Resets the network by clearing the organ list and wait list.
        This leaves an empty network to continue interacting with.
        """
        self.organ_list = OrganList()
        self.wait_list = WaitList()

        print(f'\n{ANSI_BOLD}The network has been reset. There are no '
              f'patients or organs remaining in the network.{ANSI_RESET}\n')

    def restart(self) -> None:
        """
        Clears all data from the system. This removes the existing network,
        wait list, and organ list.
        """
        self.network = None
        self.organ_list = OrganList()
        self.wait_list = WaitList()

        print(f'\n{ANSI_BOLD}The system has been reset. There is no network,'
              f' patients, or organs.{ANSI_RESET}\n')


if __name__ == '__main__':
    SimulatorSession().main_menu()
