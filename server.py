import socket
import time

def write_to_file(data):
    with open('received_letters.txt', 'a') as file:  # Open in append mode
        file.write(f"{data}\n")

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('127.0.0.1', 64321))
server_socket.listen(1)
print("Server is listening for connections...")

while True:
    client_socket, client_address = server_socket.accept()
    print(f"Connection established with {client_address}")

    client_connected = True
    last_heartbeat_received_time = time.time()

    while client_connected:
        try:
            client_socket.settimeout(5)  # Reduce timeout for more frequent checks

            data = client_socket.recv(1024).decode()

            if data:
                if data == 'heartbeat':
                    last_heartbeat_received_time = time.time()
                    client_socket.send(b'heartbeat_ack')
                else:
                    print(f"Data received: {data}")
                    write_to_file(data)
                    client_socket.send(b"order done")  # Send "order done" acknowledgment

            if time.time() - last_heartbeat_received_time > 10:
                print(f"Heartbeat not received. Client {client_address} may have disconnected.")
                client_connected = False

        except socket.timeout:
            if time.time() - last_heartbeat_received_time > 10:
                print(f"Heartbeat not received for too long. Client {client_address} may have disconnected.")
                client_connected = False

        except socket.error as e:
            print(f"Socket error with {client_address}: {e}")
            client_connected = False

    client_socket.close()

server_socket.close()
