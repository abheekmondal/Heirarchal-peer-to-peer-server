weak_peer.py:

This program simulates a weak peer node in a peer-to-peer file sharing network. It is designed to be run with Python 3. To use, simply run the script with the appropriate configuration file as an argument. The configuration file should be a JSON file that specifies the host and port number of the weak peer. The weak peer will listen for connections from super peer nodes and respond to requests to register, unregister, add files, delete files, query for files, and list all available files.

super_node.py:

This program simulates a super peer node in a peer-to-peer file sharing network. It is designed to be run with Python 3. To use, simply run the script with the appropriate configuration file as an argument. The configuration file should be a JSON file that specifies the host and port number of the super peer, as well as the host and port numbers of neighboring super peers and any weak peers that the super peer should be aware of. The super peer will listen for connections from weak peer nodes and respond to requests to register, unregister, add files, delete files, query for files, and list all available files. Additionally, the super peer will broadcast queries to neighboring super peers and check its connected weak peers for query hits.

launch_superpeers.py:

This program launches multiple instances of super_node.py with different configuration files, simulating a network of super peers. It is designed to be run with Python 3. To use, simply edit the superpeer_configs list at the top of the file to include the paths to the configuration files for each super peer that you wish to launch, then run the script. The script will launch each super peer in a separate subprocess and give them time to start up before proceeding.


TO create additional superpeers for simulating the system, simply copy and paste the following template
{
    "host": "127.0.0.1",
    "port": 9000,
    "neighbors": [
        {"host": "127.0.0.1", "port": 9001},
        {"host": "127.0.0.1", "port": 9002}
    ],
    "weak_peers": [
        {"host": "127.0.0.1", "port": 10000}
    ]
}

In this example, add the current port number 9000, in the list of neighbors like: {"host": "127.0.0.1", "port": 9000}, make sure all the neighbors are seperated with a comma. Update the port number to a desired one, lets say 9004. Save this file as config_superpeer4. Then copy and paste, the following neigbor code:  {"host": "127.0.0.1", "port": 9004}, to all the other config_superpeers. Lastly open the all2all.py file, paste the following line under superpeer_configs = ""config_superpeer4.json","