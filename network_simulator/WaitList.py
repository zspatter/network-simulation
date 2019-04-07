class WaitList:
    """
    A class that represents the wait list for all patients waiting on
    a donation. This list accepts all patients in need of organs (generic)
    """
    def __init__(self, wait_list=None):
        if wait_list is None:
            wait_list = list()

        self.wait_list = wait_list
