# Network-Simulation

This project is designed to simulate an organ transplant system. Its aim is to simulate potential problems that may occur while transporting organs from facility to facility. Factors that could affect the system include: the number of vehicles available in circulation, construction (closed roads), the amount of time an organ remains viable out of the human body, traffic, and natural disasters. For the purposes of this simulated model, problems during transport will be represented by removing paths between two given nodes. The system will handle these problems by finding alternative routes between two destinations.

The network will be represented by a collection of dictionaries. 

###### The smallest element within our graph is a Node object. A Node consists of:
1. A node ID which is a unique identifier. 
2. A label which describes/names the node.
3. An adjacency dictionary where the adjacent node's id is the key and another dictionary with two entries is the value. This allows each edge to have two important attributes - weight and status (active or inactive).
4. A status which indicates if a node is active or inactive. If the node is inactive, all edges contained in the adjacency list are consequently inactive as well.

###### The graph is represented as a collction of nodes. The Network objects will consist of:
1. A graph ID which is a unique identifier.
2. A label which describes/names the graph.
3. A dictionary which contains a collection of node ID's that point to the corresponding Node objects.
