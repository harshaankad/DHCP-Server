import socket
import threading
import json
import time

from config import HOST, PORT, REQUEST_IP, UPDATE_LEASE, ASSIGNED_IP, LEASE_UPDATED, NO_IP_ASSIGNED

# Dictionary to map MAC addresses to assigned IP addresses and renewal times
mac_to_ip = {}
# Set to keep track of assigned IP addresses
assigned_ips = set()
# Lock for synchronizing access to data structures
lock = threading.Lock()
lease_time = 10
STARTING_IP = '192.168.1.1'
IP_RANGE_SIZE = 5
running = True  # Flag to control the loop


# Function to handle client requests
def handle_client():
    # Create a UDP socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        print(f"Attempting to bind to {HOST}:{PORT}")
        # Bind the socket to the address and port
        server_socket.bind((HOST, PORT))

        print("Server is listening...")

        # Start a thread for checking lease time expiration
        lease_checker_thread = threading.Thread(target=check_lease_time_expiration)
        lease_checker_thread.start()

        # Receive data from the client and process requests
        while running:
            try:
                data, client_address = server_socket.recvfrom(1024)
            except socket.error as e:
                print(f"Socket error occurred: {e}")
                continue
            except socket.timeout:
                print("Socket timeout occurred")
                continue

            data = data.decode().strip()
            print(f"Received from client {client_address}: {data}")

            try:
                # Parse the JSON message
                message = json.loads(data)
                command = message.get('command')
                mac_address = message.get('mac_address')
            except json.JSONDecodeError:
                print(f"Invalid JSON format received from client {client_address}: {data}")
                continue

            if command == REQUEST_IP:
                handle_ip_request(server_socket, client_address, mac_address)
            elif command == UPDATE_LEASE:
                handle_lease_update(server_socket, client_address, mac_address)
            else:
                print(f"Unknown command received from client {client_address}: {command}")


# Function to handle IP address requests
def handle_ip_request(server_socket, client_address, mac_address):
    with lock:
        global assigned_ips
        if len(assigned_ips) >= IP_RANGE_SIZE:
            # Inform the client that the cache is full
            response = {"status": NO_IP_ASSIGNED, "message": "Cache is full. No new IP address can be assigned."}
            server_socket.sendto(json.dumps(response).encode(), client_address)
            print("Cache is full. No new IP address can be assigned.")
            return

        if mac_address not in mac_to_ip:
            assigned_ip = get_next_available_ip()
            if assigned_ip:
                mac_to_ip[mac_address] = (assigned_ip, time.time() + lease_time)  # Store lease expiration time
                print(f"Assigned IP address: {assigned_ip}, Lease Time: {lease_time}")
                response = {"status": ASSIGNED_IP, "assigned_ip": assigned_ip, "lease_time": lease_time}
                server_socket.sendto(json.dumps(response).encode(), client_address)
            else:
                print("No available IP addresses.")
                response = {"status": NO_IP_ASSIGNED, "message": "No available IP addresses."}
                server_socket.sendto(json.dumps(response).encode(), client_address)
        else:
            assigned_ip, renewal_time = mac_to_ip[mac_address]
            print(f"IP address already assigned: {assigned_ip}, Renewal Time: {renewal_time}")
            response = {"status": ASSIGNED_IP, "assigned_ip": assigned_ip, "lease_time": int(renewal_time - time.time())}
            server_socket.sendto(json.dumps(response).encode(), client_address)


# Function to get the next available IP address
def get_next_available_ip():
    global assigned_ips
    for i in range(IP_RANGE_SIZE):
        ip = f"{STARTING_IP[:-1]}{i + 1}"
        if ip not in assigned_ips:
            assigned_ips.add(ip)
            return ip
    return None


# Function to handle lease time updates
def handle_lease_update(server_socket, client_address, mac_address):
    new_lease_time = lease_time  # Assuming the server does not allow clients to change lease time
    if mac_address in mac_to_ip:
        mac_to_ip[mac_address] = (mac_to_ip[mac_address][0], time.time() + lease_time)  # Update lease expiration time
        print(f"Lease time updated for MAC address {mac_address}: {new_lease_time}")
        response = {"status": LEASE_UPDATED}
        server_socket.sendto(json.dumps(response).encode(), client_address)
    else:
        print(f"No assigned IP found for MAC address {mac_address}")
        response = {"status": NO_IP_ASSIGNED}
        server_socket.sendto(json.dumps(response).encode(), client_address)


# Function to check and remove expired lease entries
def check_lease_time_expiration():
    global running
    while running:
        current_time = time.time()
        expired_entries = [mac_address for mac_address, (_, expiration_time) in mac_to_ip.items() if expiration_time < current_time]
        with lock:
            for mac_address in expired_entries:
                ip = mac_to_ip[mac_address][0]
                assigned_ips.remove(ip)
                del mac_to_ip[mac_address]
                print(f"Expired lease removed for MAC address: {mac_address}")
        time.sleep(1)  # Check every second


# Start handling client requests
handle_client()
