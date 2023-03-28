import os
import sys
import json
import socket
import threading
from time import sleep
import time

# Load configuration
with open("config.json", "r") as file:
    config = json.load(file)["weak_peer"]

# Configuration
HOST = config["host"]
PORT = config["port"]
FILES_DIR = config["files_directory"]
SUPER_PEER = (config["super_peer"]["host"], config["super_peer"]["port"])

# Global variables
files = set()
connections_log = []

def load_files():
    global files
    files = set(os.listdir(FILES_DIR))

def update_files():
    while True:
        new_files = set(os.listdir(FILES_DIR))
        if new_files != files:
            diff_added = new_files - files
            diff_removed = files - new_files
            files.update(new_files)

            if diff_added:
                register_files(diff_added)
            if diff_removed:
                unregister_files(diff_removed)

        sleep(5)

def register_files(files_to_register):
    send_to_super_peer({"action": "register", "files": list(files_to_register)})

def unregister_files(files_to_unregister):
    send_to_super_peer({"action": "unregister", "files": list(files_to_unregister)})

def send_query(query):
    message = {
        "action": "query",
        "query": query
    }

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(SUPER_PEER)
            s.sendall(json.dumps(message).encode())

            # Wait for queryhit response
            data = s.recv(1024)
            if data:
                response = json.loads(data.decode())
                if response["action"] == "queryhit":
                    return response["peer"]
            else:
                print("File not found in the network.")
                return None
    except Exception as e:
        print(f"Error sending query to super peer: {e}")
        return None

def download_file(peer, filename):
    message = {
        "action": "download",
        "filename": filename
    }

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(peer)
            s.sendall(json.dumps(message).encode())

            # Receive the file data
            file_data = b""
            while True:
                data = s.recv(1024)
                if not data:
                    break
                file_data += data

            # Save the downloaded file
            with open(os.path.join(FILES_DIR, filename), "wb") as f:
                f.write(file_data)

            print(f"File '{filename}' downloaded successfully.")
    except Exception as e:
        print(f"Error downloading file from peer {peer}: {e}")


def send_to_super_peer(data):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(SUPER_PEER)
            s.sendall(json.dumps(data).encode())
    except Exception as e:
        print(f"Error sending data to super peer: {e}")

def handle_client(conn, addr):
    try:
        print(f"New client connected: {addr}")
        data = conn.recv(1024)
        if not data:
            return

        request = json.loads(data.decode())
        action = request["action"]

        if action == "download":
            filename = request["filename"]
            if filename in files:
                with open(os.path.join(FILES_DIR, filename), "rb") as file:
                    conn.sendall(file.read())
                    print(f"Sent file '{filename}' to {addr}")
                connections_log.append({"type": "sent", "filename": filename, "peer": addr})
            else:
                conn.sendall(b"")
                print(f"File '{filename}' not found for {addr}")
        elif action == "query":
            query = request["query"]
            send_to_super_peer({"action": "query", "query": query, "client_addr": addr})
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        conn.close()

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        print(f"Weak peer node listening on {HOST}:{PORT}")
        load_files()
        register_files(files)

        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()

def list_files():
    super_peer_host, super_peer_port = SUPER_PEER

    message = {"action": "list"}

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((super_peer_host, super_peer_port))
            s.sendall(json.dumps(message).encode())

            data = s.recv(1024)
            if not data:
                print("No response from super peer.")
                return

            files = json.loads(data.decode())
            print("Files available in the super peer network:")
            for file in files:
                print(f" - {file}")

    except Exception as e:
        print(f"Error listing files: {e}")


def send_query(query):
    super_peer_host, super_peer_port = SUPER_PEER
    start_time = time.time()
    message = {
        "action": "query",
        "query": query
    }

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((super_peer_host, super_peer_port))
            s.sendall(json.dumps(message).encode())
            response = s.recv(1024)  # Listen for a response
            if response:
                print(f"Response: {response.decode()}")
    except Exception as e:
        print(f"Error sending query to super node: {e}")
    # Process the query and receive the response
    end_time = time.time()
    response_time = end_time - start_time
    print(f"Response time: {response_time:.2f} seconds")


def register():
    message = {
        "action": "register",
        "files": list(files)
    }
    send_to_super_peer(message)

def unregister():
    message = {
        "action": "unregister"
    }
    send_to_super_peer(message)

def add_files(filenames):
    message = {
        "action": "add",
        "files": filenames
    }
    send_to_super_peer(message)

def delete_files(filenames):
    message = {
        "action": "delete",
        "files": filenames
    }
    send_to_super_peer(message)

def user_interface():
    print("Enter a command (search [filename] | list | register | unregister | add [filename1,filename2,...] | delete [filename1,filename2,...] | exit):")
    while True:
        command = input()
        if command.startswith("search "):
            query = command[7:]
            if query:
                send_query(query)
            else:
                print("Please provide a file name to search.")
        elif command == "list":
            list_files()
        elif command == "register":
            register()
        elif command == "unregister":
            unregister()
        elif command.startswith("add "):
            filenames = command[4:].split(',')
            add_files(filenames)
        elif command.startswith("delete "):
            filenames = command[7:].split(',')
            delete_files(filenames)
        elif command == "exit":
            sys.exit(0)
        else:
            print("Invalid command. Please try again.")


if __name__ == "__main__":
    try:
        # Start the server in a separate thread
        server_thread = threading.Thread(target=start_server)
        server_thread.start()

        # Start the user interface for sending query requests
        user_interface()

    except KeyboardInterrupt:
        print("KeyboardInterrupt received, shutting down...")
        sys.exit(0)
