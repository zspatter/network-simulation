# Network-Simulation

This project is designed to simulate an organ transplant system. Its aim is to simulate potential problems that may occur while transporting organs from facility to facility. Factors that could affect the system include: the number of vehicles available in circulation, construction (closed roads), the amount of time an organ remains viable out of the human body, traffic, and natural disasters. For the purposes of this simulated model, problems during transport will be represented by removing paths between two given nodes. The system will handle these problems by finding alternative routes between two destinations.

The network will be represented by a collection of dictionaries. 

#### The smallest element within our graph is a Node object. A Node consists of:
1. A node ID which is a unique identifier. 
2. A label which describes/names the node.
3. An adjacency dictionary where the adjacent node's id is the key and another dictionary with two entries is the value. This allows each edge to have two important attributes - weight and status (active or inactive).
4. A status which indicates if a node is active or inactive. If the node is inactive, all edges contained in the adjacency list are consequently inactive as well.

#### The graph is represented as a collection of nodes. The Network objects will consist of:
1. A dictionary which contains a collection of node ID's that point to the corresponding Node objects.
2. A label which describes/names the graph.

#### Other Classes:
- <ins>*Dijkstras*</ins> - finds all shortest paths from a source node in a given graph (also contains some connectivity helper functions)
- <ins>*Organ*</ins> - represent the donated organs (these will be distributed across the system)
- <ins>*Patient*</ins> - represent individuals in need of a transplant
- <ins>*OrganList*</ins> - represents all donor organs currently available to be allocated to patients
- <ins>*WaitList*</ins> - represents all patients in need of a transplant
- <ins>*MatchIdentifier*</ins> - determines if a given patient and organ combination are compatible (suitable for transplant)
- <ins>*GraphBuilder*</ins> - builds a random network with N nodes
- <ins>*GenerateOrgans*</ins> - simulates harvesting organs from N patients and adds generated organs to an OrganList
- <ins>*GeneratePatients*</ins> - generates N patients each with a random organ need, blood type, priority, and location (node)
- <ins>*OrganAllocator*</ins> - allocates harvested organs (OrganList) to the most optimal matching patient (WaitList)

#### Simulator:
The simulator allows for an interactive experience through the console by harnessing the functions of the GraphBuilder, GeneratePatients, GenerateOrgans, and OrganAllocator classes. This allows users to choose the number of nodes in the network, number of patients on the wait list, and number of bodies to harvest organs from all on the fly.

## UML Diagram
![alt text](https://github.com/zspatter/network-simulation/blob/master/UML.png)
