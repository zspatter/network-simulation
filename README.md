# Network Simulation

This project is designed to simulate an organ transplant system. Its aim is to simulate the organ transplant matching process. To accomplish this, there will be a list of patients in need of an organ transplant within a given network of hospitals. After organs are harvested from a deceased organ donor, the system will find the most optimal match by looking at the list of patients, then the organ will be allocated to the matched patient. 

**<ins>The following criteria are used to determine matches</ins>:**
1. The patient's need must be of the same organ type (kidney, lungs, heart, etc.)
2. The patient must be of a compatible blood type (example: patient: AB-, organ: B-)
3. The organ must be able to be transported to the patient's hospital while remaining viable (organ-specific time limit)
4. The optimal match will be the patient who matches the above criteria with the highest priority rating

## Classes

### <ins>Node</ins>:
The smallest element within the network is a Node object. Each node represents a specific hospital where both patients and organs can be located. These will represent the 'addresses' of sources and destinations within the graph based on an organ's location and the matched patient's location.

**<ins>Nodes consist of</ins>:**
1. <ins>node ID</ins> - a unique identifier
2. <ins>label</ins> - describes/names the node
3. <ins>adjacency dictionary</ins> - where the adjacent node's id is the key and another dictionary with two entries is the value. This allows each edge to have two important attributes - weight and status (active or inactive)
4. <ins>status</ins> - indicates if a node is active or inactive. If the node is inactive, all edges contained in the adjacency list are consequently inactive as well

### <ins>Network</ins>:
The network is a graph that is represented as a collection of nodes. The network represents the entire network of hospitals. The network will be traversed from node to node to. The weights of individual edges traveled will be added together to represent the total cost of the traveled path.

**<ins>Networks consist of</ins>:**
1. <ins>network dictionary</ins> - contains a collection of node ID's that point to their corresponding Node objects
2. <ins>label</ins> - describes/names the graph

### <ins>Other Classes</ins>:
- <ins>*Dijkstra*</ins> - finds all shortest paths from a source node in a given graph (also contains some connectivity helper functions)
- <ins>*Organ*</ins> - represent the donated organs (these will be distributed across the system)
- <ins>*Patient*</ins> - represent individuals in need of a transplant
- <ins>*OrganList*</ins> - represents all donor organs currently available to be allocated to patients
- <ins>*WaitList*</ins> - represents all patients in need of a transplant
- <ins>*MatchIdentifier*</ins> - determines if a given patient and organ combination are compatible (suitable for transplant)
- <ins>*GraphBuilder*</ins> - builds a random network with N nodes
- <ins>*OrganGenerator*</ins> - simulates harvesting organs from N patients where each organ has a 75% of being successfully harvested and adds the generated organs to an OrganList
- <ins>*PatientGenerator*</ins> - generates N patients each with a random organ need, blood type, priority, and location (node) and adds the generated patients to a WaitList
- <ins>*OrganAllocator*</ins> - allocates harvested organs (OrganList) to the most optimal matching patient (WaitList)
- <ins>*ConnectivityChecker*</ins> - determines if a given graph is connected 

### <ins>Simulator</ins>: 
The simulator allows for an interactive experience through the console by harnessing the functions of the GraphBuilder, GeneratePatients, GenerateOrgans, and OrganAllocator classes. This allows users to choose the number of nodes in the network, number of patients on the wait list, and number of bodies to harvest organs from all on the fly.

## UML Diagram
![alt text](https://github.com/zspatter/network-simulation/blob/master/UML.png)
