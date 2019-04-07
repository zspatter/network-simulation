class OrganList:
    """
    A class that represents all of the available organs waiting to be
    allocated to compatible recipients. This list accepts all organ types (generic)
    """
    def __init__(self, organ_list=None):
        if organ_list is None:
            organ_list = list()

        self.organ_list = organ_list

    def add_organ(self, organ):
        self.organ_list.append(organ)

    def remove_organ(self, organ):
        self.organ_list.remove(organ)
