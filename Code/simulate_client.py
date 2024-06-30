import socket

def connect_to_server(host, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((host, port))
        print(f"Connected to server at {host}:{port}")
    except socket.error as e:
        print(f"Failed to connect: {e}")
        return None
    return client_socket

def send_message(client_socket, message):
    try:
        client_socket.sendall(message.encode())
        print(f"Sent: {message}")
    except socket.error as e:
        print(f"Failed to send message: {e}")

def receive_response(client_socket):
    try:
        response = client_socket.recv(1024)
        print(f"Received: {response.decode()}")
    except socket.error as e:
        print(f"Failed to receive response: {e}")

def main():
    host = "192.168.129.17"
    port = 8081

    client_socket = connect_to_server(host, port)
    if not client_socket:
        return

    while True:
        message = input("Enter message to send (or 'exit' to quit): ")
        if message.lower() == 'exit':
            break
        send_message(client_socket, message)
        #receive_response(client_socket)

    client_socket.close()
    print("Connection closed")

if __name__ == "__main__":
    main()
