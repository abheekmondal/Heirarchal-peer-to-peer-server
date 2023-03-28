import argparse
import os
import subprocess
import time
import json
import socket
import threading
from typing import List
import matplotlib.pyplot as plt

# Add command-line argument for the number of clients
parser = argparse.ArgumentParser()
parser.add_argument("--num_clients", type=int, default=8, help="Number of clients to simulate")
args = parser.parse_args()

# ----- Deploying super-peers -----
superpeer_configs = [
    "config_superpeer1.json",
    "config_superpeer2.json",
    "config_superpeer3.json",
]

for config in superpeer_configs:
    subprocess.Popen(["python", "super_node.py", config], env=os.environ)

# Give some time for super-peers to start
time.sleep(5)

#-------Deploying weak-peers ---------
weak_peer_configs = [
    "config_weakpeer1.json",
    "config_weakpeer2.json",
    "config_weakpeer3.json",
    # Add more config files for more weak-peers
]

for config in weak_peer_configs:
    subprocess.Popen(["python", "weak_peer.py", config], env=os.environ)

# Give some time for weak-peers to start
time.sleep(5)    
# ----- Client (peer nodes) code -----
def send_query(peer_host, peer_port, query):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((peer_host, peer_port))
        s.sendall(json.dumps(query).encode())

        start_time = time.time()
        data = s.recv(1024)
        end_time = time.time()

    response_time = end_time - start_time
    return response_time

def measure_average_response_time(peer_host, peer_port, query, num_iterations=300):
    total_time = 0
    for _ in range(num_iterations):
        response_time = send_query(peer_host, peer_port, query)
        total_time += response_time
    average_response_time = total_time / num_iterations
    return average_response_time

def client_task(peer_host, peer_port, query, results, index):
    average_response_time = measure_average_response_time(peer_host, peer_port, query)
    results[index] = average_response_time

def measure_clients_response_times(peer_hosts, peer_ports, query, client_counts: List[int]):
    results = {}
    for count in client_counts:
        threads = []
        response_times = [0] * count

        for i in range(count):
            t = threading.Thread(target=client_task, args=(peer_hosts[i], int(peer_ports[i]), query, response_times, i))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        results[count] = sum(response_times) / len(response_times)

    return results

# ----- Main part of the script -----
peer_hosts = ["127.0.0.1"] * 3
peer_ports = [10000, 10001, 10002] 
#[10000, 10001, 10002, 10003, 10004, 10005, 10006, 10007, 10008]
query = {"action": "search", "filename": "example_file.txt"}
client_counts = [1, 2, 4, 8]

response_times = measure_clients_response_times(peer_hosts, peer_ports, query, client_counts)

print("Response times:")
for count, response_time in response_times.items():
    print(f"{count} clients: {response_time:.3f} seconds")

# Plot the results using matplotlib
x = list(response_times.keys())
y = list(response_times.values())

plt.plot(x, y, marker="o")
plt.xlabel("Number of Clients")
plt.ylabel("Average Response Time (s)")
plt.title("Average Response Time vs Number of Clients")
plt.grid()
plt.show()

