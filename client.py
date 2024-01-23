import socket
import time

# Server configuration
server_ip = '127.0.0.1'
server_port = 64321
heartbeat_interval = 5  # seconds

def read_next_order():
    try:
        with open('orders_data.txt', 'r') as file:
            orders = file.readlines()
            if orders:
                last_order = orders[-1].strip()
                # Assuming the format is "OrderID:LetterData"
                parts = last_order.split(':')
                if len(parts) >= 2:
                    return parts[1]  # Return only the letter part
                else:
                    print("Error: Order format is incorrect")
                    return None
            return None
    except FileNotFoundError:
        print("Orders file not found.")
        return None

def delete_last_order():
    try:
        with open('orders_data.txt', 'r+') as file:
            orders = file.readlines()
            file.seek(0)  # Go back to the start of the file
            file.writelines(orders[:-1])  # Rewrite all but the last order
            file.truncate()  # Truncate the file to the new size
    except Exception as e:
        print(f"Error deleting the last order: {e}")

def connect_to_server():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_ip, server_port))
        return client_socket
    except socket.error as e:
        print(f"Error connecting to server: {e}")
        return None

def main():
    client_socket = connect_to_server()  # Attempt to connect to server initially
    last_heartbeat_time = 0
    current_order = read_next_order()  # Initialize with the first order

    while True:
        if not client_socket:
            print("Attempting to reconnect to server...")
            client_socket = connect_to_server()
            if not client_socket:
                time.sleep(1)  # Wait a bit before retrying if unable to connect
                continue

        if time.time() - last_heartbeat_time >= heartbeat_interval:
            try:
                client_socket.send(b'heartbeat')
                last_heartbeat_time = time.time()
            except socket.error:
                print("Failed to send heartbeat.")
                client_socket.close()
                client_socket = None  # Mark as not connected
                continue

        if current_order:
            try:
                client_socket.send(current_order.encode('utf-8'))
            except socket.error:
                print("Failed to send data.")
                client_socket.close()
                client_socket = None  # Mark as not connected
                continue

        try:
            client_socket.settimeout(1)  # Non-blocking receive
            response = client_socket.recv(1024).decode()
            if response == 'order done':
                print(f"Server acknowledged {current_order}. Sending next order.")
                delete_last_order()  # Delete the last order
                current_order = read_next_order()  # Read the next order and prepare to send it
        except socket.timeout:
            pass  # It's okay if there's no response within timeout
        except socket.error:
            print("Error receiving data.")
            client_socket.close()
            client_socket = None  # Mark as not connected

        time.sleep(1)  # Main loop pause

main()
