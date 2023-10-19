import socket
import sys
import os
import time

HOST = "127.0.0.1"  # The server's hostname ot IP address
PORT = 65433        # Port used by the server
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

    # server_socket.send(file_info.encode())

    with open(file_path, 'rb') as file:
        # Concatenate the file info and content, separated by "!"
        # file_data = file_info.encode() + "!".encode() + file.read()

        # # Send the combined data
        # server_socket.sendall(file_data)
        file_data = f"{file_info}!{file.read().decode()}"
        server_socket.sendall(file_data.encode())
    
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
            print("Sleeping...")
            time.sleep(5)
            send_file(file_path, server_socket)
        # server_socket.send("DONE".encode())
    finally:
        server_socket.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Missing files to send to server.")
    else:
        files = sys.argv[1:]
        main(files)