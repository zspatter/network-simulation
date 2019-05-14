from __future__ import annotations

from typing import List

from network_simulator.Organ import Organ


class OrganList:
    """
    A class that represents all of the available organs waiting to be
    allocated to compatible recipients. This list accepts all organ types (generic)
    """
    
    def __init__(self, organ_list: List[Organ] = None, label: str = None) -> None:
        """
        Creates a OrganList object. If no organ_list parameter is provided,
        an empty list is created

        :param list organ_list: optional organ_list parameter (if preexisting list exists)
        :param str label: label for the list/collection of organs
        """
        self.organ_list: List[Organ]
        self.label: str
        
        if not organ_list:
            organ_list = list()
        
        if not label:
            label = 'Default list of organs'
        self.label = label
        self.organ_list = organ_list
    
    def add_organ(self, organ: Organ) -> None:
        """
        Adds an organ to the existing organ list

        :param Organ organ: object to be added to the organ list
        """
        if organ not in self.organ_list:
            self.organ_list.append(organ)
            return
        print('This organ is already in the organ list!')
        
    def add_organs(self, organs: List[Organ]) -> None:
        for organ in organs:
            self.add_organ(organ)
    
    def remove_organ(self, organ: Organ) -> None:
        """
        Removes an organ from the existing organ list

        :param Organ organ: object to be removed from the organ list
        """
        if organ in self.organ_list:
            self.organ_list.remove(organ)
            return
        print('This organ isn\'t in the organ list!')
    
    def empty_list(self) -> None:
        """
        Clears entire organ_list (utility function for the organ allocator)
        """
        self.organ_list = list()
    
    def __str__(self) -> str:
        string = ''
        for organ in self.organ_list:
            string += organ.__str__() + '\n'
        
        return string + '===============================\n'
