# Synchronized Client-Server Communication System

## 1. Overview

This technical documentation describes a synchronized client-server communication system built with Python sockets, containerized with Docker, and deployable on Kubernetes. The system implements a turn-based protocol where clients communicate with a central server in an orderly, coordinated manner.

## 2. System Architecture

The system follows a client-server architecture pattern with the following components:

- **Server**: Coordinates communication between clients using a turn-based approach
- **Clients**: Connect to the server and exchange data according to server instructions
- **Docker Containers**: Encapsulate both server and client components
- **Kubernetes Deployments**: Manage the container lifecycle and networking

## 3. Technical Components

### 3.1 Server Implementation (`server.py`)

The server component manages client connections and coordinates the turn-based communication:

```python
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
```

**Technical Specifications:**
1. **Socket Configuration**: TCP socket bound to all interfaces (`0.0.0.0`) on port `5001`
2. **Concurrency Model**: Thread-based with one thread per client
3. **Synchronization**: Uses a threading lock to manage the global `turn` variable
4. **Client Management**: Supports exactly two simultaneous clients
5. **Memory Management**: Uses Python's context managers (`with` statements) for resource cleanup
6. **Error Handling**: Catches connection and pipe errors from disconnecting clients

### 3.2 Client Implementation (`client.py`)

The client component connects to the server and responds to the turn-based signals:

```python
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
                time.sleep(0.1)  # Keep listening but don't send anything

if __name__ == "__main__":
    import threading
    threading.Thread(target=client, args=("Client1", 1)).start()  # Client 1 starts at 1
    threading.Thread(target=client, args=("Client2", 2)).start()  # Client 2 starts at 2
```

**Technical Specifications:**
1. **Socket Configuration**: TCP socket connecting to `127.0.0.1:5001` (in local development)
2. **Concurrency Model**: Creates two client threads in a single process
3. **Protocol Handling**: Implements response to both "GO" and "WAIT" signals
4. **Data Formatting**: Formats messages as `{client_name}:{number}`
5. **Flow Control**: Implements a 1-second delay between messages to prevent flooding
6. **Memory Management**: Uses Python's context managers for resource cleanup

### 3.3 Docker Configuration for Server (`Dockerfile.server`)

```dockerfile
# Use the official Python image
FROM python:3.12

# Set the working directory
WORKDIR /app

# Copy the server script into the container
COPY server.py .

# Expose the port the server will listen on
EXPOSE 5001

# Command to run the server
CMD ["python3", "server.py"]
```

**Technical Specifications:**
1. **Base Image**: Python 3.12 official Docker image
2. **Working Directory**: `/app`
3. **Artifacts**: Single `server.py` file copied to container
4. **Network**: Exposes TCP port 5001
5. **Execution**: Uses CMD to specify the runtime command

### 3.4 Docker Configuration for Client (`Dockerfile.client`)

```dockerfile
# Use the official Python image
FROM python:3.12

# Set the working directory
WORKDIR /app

# Copy the client script into the container
COPY client.py .

EXPOSE 5001
# Command to run the client
ENTRYPOINT ["python3", "client.py"]
```

**Technical Specifications:**
1. **Base Image**: Python 3.12 official Docker image
2. **Working Directory**: `/app`
3. **Artifacts**: Single `client.py` file copied to container
4. **Network**: Exposes TCP port 5001
5. **Execution**: Uses ENTRYPOINT for fixed execution path

### 3.5 Kubernetes Server Deployment (`server-deployment.yaml`)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: server-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: server
  template:
    metadata:
      labels:
        app: server
    spec:
      containers:
        - name: server
          image: server-image:latest
          imagePullPolicy: Never
          ports:
            - containerPort: 5001
---
apiVersion: v1
kind: Service
metadata:
  name: server-service
spec:
  selector:
    app: server
  ports:
    - protocol: TCP
      port: 5001
      targetPort: 5001
  type: NodePort
```

**Technical Specifications:**
1. **API Version**: apps/v1
2. **Deployment Configuration**: 
   - Name: server-deployment
   - Replicas: 1 (critical for turn coordination)
   - Selector: app=server
3. **Container Configuration**:
   - Image: server-image:latest
   - Image Pull Policy: Never (uses local image)
   - Port: 5001
4. **Service Configuration**:
   - Type: NodePort
   - Port Mapping: 5001:5001 TCP
   - Selector: app=server

### 3.6 Kubernetes Client Deployment (`client-deployment.yaml`)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: client-deployment
spec:
  replicas: 2
  selector:
    matchLabels:
      app: client
  template:
    metadata:
      labels:
        app: client
    spec:
      containers:
        - name: client
          image: client-image:latest
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 5001
---
apiVersion: v1
kind: Service
metadata:
  name: client-service
spec:
  selector:
    app: client
  ports:
    - protocol: TCP
      port: 5001
      targetPort: 5001
  type: NodePort
```

**Technical Specifications:**
1. **API Version**: apps/v1
2. **Deployment Configuration**: 
   - Name: client-deployment
   - Replicas: 2 (creates two client pods)
   - Selector: app=client
3. **Container Configuration**:
   - Image: client-image:latest
   - Image Pull Policy: IfNotPresent
   - Port: 5001
4. **Service Configuration**:
   - Type: NodePort
   - Port Mapping: 5001:5001 TCP
   - Selector: app=client

## 4. Protocol Specification

### 4.1 Server-to-Client Protocol
- `GO`: Signal indicating the client is allowed to transmit
- `WAIT`: Signal indicating the client should wait

### 4.2 Client-to-Server Protocol
- Format: `{client_name}:{number}`
- Examples: `Client1:1`, `Client2:2`, `Client1:3`, etc.

### 4.3 Turn Management
1. Server initializes turn to Client1 (turn=1)
2. Server sends "GO" to the client whose ID matches the current turn
3. Client receives "GO", sends data, and waits for next instruction
4. Server receives data, processes it, and switches turn to other client
5. Server sends "WAIT" to clients not matching the current turn

## 5. System Deployment

### 5.1 Building Docker Images

```bash
# Build the server image
docker build -t server-image:latest -f Dockerfile.server .

# Build the client image
docker build -t client-image:latest -f Dockerfile.client .
```

### 5.2 Deploying to Kubernetes

```bash
# Deploy the server first
kubectl apply -f server-deployment.yaml

# Verify server is running
kubectl get pods -l app=server
kubectl get services server-service

# Deploy the client
kubectl apply -f client-deployment.yaml

# Verify clients are running
kubectl get pods -l app=client
```

### 5.3 Monitoring System Operation

```bash
# View server logs
kubectl logs -f deployment/server-deployment

# View client logs (specify pod name)
kubectl logs -f <client-pod-name>
```

## 6. Technical Considerations

### 6.1 Network Configuration
When deploying to Kubernetes, the client's host configuration must be changed from "127.0.0.1" to "server-service" to properly resolve the server's network address within the cluster.

### 6.2 Scalability Limitations
- The current server implementation is designed for exactly two clients
- The turn mechanism uses a binary toggle (1 or 2) that doesn't support additional clients
- Multiple server instances will cause coordination issues due to independent turn tracking

### 6.3 Performance Characteristics
- The 0.1-second sleep in both client and server prevents CPU saturation during wait cycles
- The 1-second delay between client messages controls message flow rate
- Thread-per-client model has limited scalability for large numbers of connections

