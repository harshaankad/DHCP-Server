import socket
import threading
import json
import time
import random

from config import HOST, PORT, REQUEST_IP, UPDATE_LEASE

# Function to generate a MAC address
def generate_mac_address():
    mac = [0x00, 0x16, 0x3e] + [random.randint(0x00, 0xff) for _ in range(3)]
    return ':'.join(map(lambda x: "%02x" % x, mac))

# Function to start a client
def start_client(client_id):
    # Create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(5)  # Set socket timeout to 5 seconds

    mac_address = generate_mac_address()
    print(f"Client {client_id} MAC address: {mac_address}")

    message_dict = {
        "command": REQUEST_IP,
        "mac_address": mac_address
    }
    # Send client MAC address to the server
    json_message = json.dumps(message_dict)
    client_socket.sendto(json_message.encode(), (HOST, PORT))
    print(f"Client {client_id}: Sent request to server")

    try:
        response, _ = client_socket.recvfrom(1024)
        print(f"Client {client_id}: Received response from server: {response.decode()}")
        response_dict = json.loads(response.decode())
        print(response_dict)
        status = response_dict.get('status')
    except (socket.timeout, json.JSONDecodeError):
        print(f"Client {client_id}: Error: Failed to receive response from server or decode JSON")
        client_socket.close()
        return

    if status == "ASSIGNED_IP":
        assigned_ip, lease_time = response_dict.get('assigned_ip'), response_dict.get('lease_time')
        print(f"Client {client_id}: Assigned IP address: {assigned_ip}, Lease Time: {lease_time}")
        lease_time = int(lease_time)
        # Sleep for 70% of the lease time
        sltime = lease_time * 0.7
        time.sleep(sltime)
    elif status == "NO_IP_ASSIGNED":
        print(f"Client {client_id}: No IP address assigned. Request IP first.")
    else:
        print(f"Client {client_id}: Unexpected response from server")

    client_socket.close()  # Clean up the socket

# Function to start multiple clients
def start_clients(num_clients):
    threads = []
    for i in range(num_clients):
        thread = threading.Thread(target=start_client, args=(i+1,))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    start_clients(6)
