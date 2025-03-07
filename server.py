import socket
import threading
import time

host = "0.0.0.0"
port = 5001
lock = threading.Lock()
turn = 1  # 1 -> Client1, 2 -> Client2

def handle_client(conn, addr, client_id):
    global turn
    with conn:
        while True:
            try:
                while True:
                    with lock:
                        if turn == client_id:
                            conn.sendall(b"GO")  # Allow client to send
                            data = conn.recv(1024).decode()  # Receive message
                            if not data:
                                return

                            client_name, number = data.split(":")
                            print(f"{client_name} sent: {number}")

                            turn = 2 if client_id == 1 else 1  # Switch turn
                        else:
                            conn.sendall(b"WAIT")  # Tell client to wait

                    time.sleep(0.1)  # Prevent CPU overload

            except (ConnectionResetError, BrokenPipeError):
                print(f"Client {client_id} ({addr}) disconnected.")
                break

def server():
    global turn
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen(2)
        print(f"Server listening on {host}:{port}")

        conn1, addr1 = server_socket.accept()
        print(f"Client1 {addr1} connected.")
        threading.Thread(target=handle_client, args=(conn1, addr1, 1)).start()

        conn2, addr2 = server_socket.accept()
        print(f"Client2 {addr2} connected.")
        threading.Thread(target=handle_client, args=(conn2, addr2, 2)).start()

if __name__ == "__main__":
    server()

