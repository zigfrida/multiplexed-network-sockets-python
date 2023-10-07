import socket
import signal
import sys
import os

HOST = "127.0.0.1"
PORT = 65432
SIZE = 1024
FORMAT = "utf-8"

server_socket = None

def signal_handler(sig, frame):
    print("\nUser Interruption. Shutting down server.")
    if server_socket: 
        server_socket.close()
    exit(0)


def handle_client(conn):
    while True:
        file_info = conn.recv(SIZE).decode()
        if not file_info:
            break
        print(f"File info: {file_info}")

        file_name, file_size_str = file_info.split('!') # File name and file size are delimited using !
        file_size = int(file_size_str)
        file_path = os.path.join(storage_directory, file_name)

        if os.path.exists(file_path): # If file already exists send message back to client
            print(f"Skipping file {file_name} since it already exists.")
            conn.send("duplicate found".encode())
            continue
        else:
            conn.send(f"File: {file_name} does not exit. Saving it....".encode())

        with open(file_path, "wb") as file:
            received_bytes = 0
            while received_bytes < file_size:
                data = conn.recv(SIZE)
                if not data:
                    break
                file.write(data)
                received_bytes += len(data)

        print(f"File: {file_name} has been saved.")
        conn.send(f"File: {file_name} has been saved.".encode())
    
    conn.close()


def main(): 
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Creating a socket object

    try: 
        server_socket.bind((HOST, PORT)) # Associates the socket with specific network interface and port number
        server_socket.listen()  # Enables server to accept connections. Makes the server a "listening" socket
        print(f"Server listening on {HOST}:{PORT}")

        signal.signal(signal.SIGINT, signal_handler)

    except OSError as e:
        print(f"Error: {e}. Server may already be running.")

    try:
        while True:
            conn, addr = server_socket.accept()
            print(f"Connected by {addr}")

            handle_client(conn)
            conn.close()
    except KeyboardInterrupt:
        print("\nServer interrupted by user")
        server_socket.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Missing storage directory.")
    else:
        storage_directory = sys.argv[1]
        print(f"Storage directory: {storage_directory}")

        if not os.path.exists(storage_directory):
            os.makedirs(storage_directory)
            print("Storage directory created!")
        
        main()