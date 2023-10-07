import socket
import sys
import os

HOST = "127.0.0.1"  # The server's hostname ot IP address
PORT = 65432        # Port used by the server
SIZE = 1024
FORMAT = "utf-8"

def send_file(file_path, server_socket):

    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        return

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    file_info = f"{file_name}!{file_size}"
    print(f"Sending info: {file_info}")

    server_socket.send(file_info.encode())

    check_exists = server_socket.recv(SIZE).decode()
    if check_exists == "duplicate found":
        print(f"Skipping file {file_name} since it already exists.")
        return
    else:
        print(check_exists)

    with open(file_path, 'rb') as file:
        while True:
            data = file.read(SIZE)
            if not data:
                break
            server_socket.sendall(data)
    
    response = server_socket.recv(SIZE).decode()
    if response != "":
        print(f"Server: {response}")
        return


def main(files):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Creating a socket object

    try:
        server_socket.connect((HOST, PORT))
        print("Connected!")
    except ConnectionRefusedError:
        print("Server does not seem to be running.")
        return
    
    try:
        for file_path in files:
            send_file(file_path, server_socket)
    finally:
        server_socket.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Missing files to send to server.")
    else:
        files = sys.argv[1:]
        main(files)