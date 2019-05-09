from network_simulator.Node import Node


def test_is_adjacent():
    """
    arrange phase: setting up the instances (creating adjacency)
    act phase: performing an action
    assert phase:
    :return:
    """
    node1 = Node(1, 'A', {2: {'weight': 3, 'status': True}})
    
    assert node1.is_adjacent(2)
    assert not node1.is_adjacent(3)
    assert not node1.is_adjacent(node1.node_id)


def test_get_adjacents():
    adjacency_dict = {2: {'weight': 3, 'status': True},
                      3: {'weight': 1, 'status': True},
                      4: {'weight': 4, 'status': True},
                      5: {'weight': 2, 'status': True}}
    
    node_1 = Node(1, 'A', adjacency_dict)
    
    adjacents = node_1.get_adjacents()
    assert len(adjacents) is len(adjacency_dict)
    
    for key in adjacency_dict:
        assert key in adjacents


def test_str():
    adjacency_dict = {2: {'weight': 3, 'status': True},
                      3: {'weight': 1, 'status': True},
                      4: {'weight': 4, 'status': True},
                      5: {'weight': 2, 'status': True}}
    
    node_1 = Node(1, 'A', adjacency_dict)
    string = node_1.__str__()
    
    for key in node_1.get_adjacents():
        assert 'Node     #' + str(key) in string
