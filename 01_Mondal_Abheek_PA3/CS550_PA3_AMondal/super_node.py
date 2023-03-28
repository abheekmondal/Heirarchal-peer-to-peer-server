import os
import sys
import json
import socket
import threading
from time import sleep
from uuid import uuid4

# Load configuration
with open("config.json", "r") as file:
    config = json.load(file)["super_peer"]

# Configuration
HOST = config["host"]
PORT = config["port"]
NEIGHBOR_SUPER_PEERS = [(peer["host"], peer["port"]) for peer in config["neighbor_super_peers"]]
WEAK_PEERS = config["weak_peers"]

# Global variables
peer_files = {}
query_messages = {}
queryhit_messages = {}

def read_config(config_file):
    with open(config_file, 'r') as file:
        config = json.load(file)
    return config["host"], config["port"]

# Example usage
#host, port = read_config("config_superpeer1.json")

def handle_weak_peer(conn, addr):
    try:
        print(f"New weak peer connected: {addr}")
        data = conn.recv(1024)
        if not data:
            return

        request = json.loads(data.decode())
        action = request["action"]

        if action == "register":
            peer_files[addr] = request["files"]
            print(f"Weak peer {addr} registered successfully.")
        elif action == "unregister":
            peer_files.pop(addr, None)
            print(f"Weak peer {addr} unregistered successfully.")
        elif action == "add":
            peer_files[addr].extend(request["files"])
        elif action == "delete":
            for filename in request["files"]:
                peer_files[addr].remove(filename)
        elif action == "query":
            query_id = str(uuid4())
            query_messages[query_id] = query_messages[query_id] = {"origin": addr, "ttl": request.get("ttl", 3)}
            broadcast_query(query_id, request["query"])
        elif action == "list":
            all_files = []
            for files in peer_files.values():
                all_files.extend(files)
            response = json.dumps(list(set(all_files))).encode()
            conn.sendall(response)
    except Exception as e:
        print(f"Error handling weak peer {addr}: {e}")
    finally:
        conn.close()

def handle_super_nodes(conn, addr):
    try:
        print(f"New super node connected: {addr}")
        data = conn.recv(1024)
        if not data:
            return

        request = json.loads(data.decode())
        action = request["action"]

        if action == "query":
            query_id = request["query_id"]

            # Check if the query has been seen before
            if query_id in query_messages:
                return

            query = request["query"]
            ttl = request["ttl"]
            query_messages[query_id] = addr
            broadcast_query(query_id, query, ttl)
            
            # Check for query hit in connected weak peers
            for peer, files in peer_files.items():
                if query in files:
                    queryhit_messages[query_id] = peer
                    query_hit(query_id)

        elif action == "queryhit":
            query_id = request["query_id"]
            queryhit_peer = request["peer"]

            if query_id in query_messages:
                original_sender = query_messages[query_id]
                queryhit_messages[query_id] = queryhit_peer
                query_hit(query_id)

    except Exception as e:
        print(f"Error handling super node {addr}: {e}")
    finally:
        conn.close()

def broadcast_query(query_id, query):
    message = {
        "action": "query",
        "query_id": query_id,
        "query": query,
        "ttl": query_messages[query_id]["ttl"]
    }

    # Send to super peers
    for super_peer in NEIGHBOR_SUPER_PEERS:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(super_peer)
                s.sendall(json.dumps(message).encode())
        except Exception as e:
            print(f"Error broadcasting query to super peer {super_peer}: {e}")

    # Check for query hit in connected weak peers
    for peer, files in peer_files.copy().items():
        if query in files:
            queryhit_messages[query_id] = peer
            query_hit(query_id)

    # Decrement TTL and rebroadcast if necessary
    if message["ttl"] > 0:
        query_messages[query_id]["ttl"] -= 1
        threading.Timer(1.0, broadcast_query, [query_id, query]).start()


def query_hit(query_id):
    message = {
        "action": "queryhit",
        "query_id": query_id,
        "peer": queryhit_messages[query_id]
    }

    original_sender = query_messages[query_id]['origin']

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(original_sender)
            s.sendall(json.dumps(message).encode())
    except Exception as e:
        print(f"Error sending queryhit to original sender {original_sender}: {e}")


def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()

        print(f"Super peer node listening on {HOST}:{PORT}")

        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_weak_peer, args=(conn, addr)).start()


if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        print("KeyboardInterrupt received, shutting down...")
        sys.exit(0)

