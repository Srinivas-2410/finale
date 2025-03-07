import socket
import time

def client(client_name, start_number):
    host = "127.0.0.1"
    port = 5001
    current_number = start_number

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))

        while True:
            response = client_socket.recv(1024).decode()  # Receive signal from server

            if response == "GO":
                message = f"{client_name}:{current_number}"
                client_socket.sendall(message.encode())
                print(f"{client_name} sent: {current_number}")
                current_number += 2
                time.sleep(1)  # Delay to prevent spamming

            elif response == "WAIT":
                time.sleep(0.1)  # Keep listening but don’t send anything

if __name__ == "__main__":
    import threading
    threading.Thread(target=client, args=("Client1", 1)).start()  # Client 1 starts at 1
    threading.Thread(target=client, args=("Client2", 2)).start()  # Client 2 starts at 2
