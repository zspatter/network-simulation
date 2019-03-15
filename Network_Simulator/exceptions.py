class Error(Exception):
    """Base class of exceptions in this module"""
    pass


class NodeAlreadyExistsError(Error):
    """Raised when node is already present in a graph"""

    def __init__(self, message=None):
        self.message = 'NodeAlreadyExistsError: ' + str(message)


class NodeDoesNotExistError(Error):
    """Raised when node is not present in a graph"""

    def __init__(self, message=None):
        self.message = 'NodeDoesNotExistError: ' + str(message)


class EdgeAlreadyExistsError(Error):
    """Raised when edge is already present in a graph"""

    def __init__(self, message=None):
        self.message = 'EdgeAlreadyExistsError: ' + str(message)


class EdgeDoesNotExistError(Error):
    """Raised when edge is not present in a graph"""

    def __init__(self, message=None):
        self.message = 'EdgeDoesNotExistError: ' + str(message)


class ElementActiveError(Error):
    """Raised when graph element is active"""

    def __init__(self, message=None):
        self.message = 'ElementActiveError: ' + str(message)


class ElementInactiveError(Error):
    """Raised when graph element is inactive"""

    def __init__(self, message=None):
        self.message = 'ElementInactiveError: ' + str(message)
