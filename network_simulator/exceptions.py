class Error(Exception):
    """Base class of exceptions in this module"""
    pass


class GraphElementError(Error):
    """Raised when there is an error with the graph such as
        a node/edge already exists or an element is already active
    """
    def __init__(self, message=None):
        self.message = 'GraphElementError: ' + str(message)
