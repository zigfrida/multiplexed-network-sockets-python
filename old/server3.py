import socket
import select
import sys
import os

HOST = "127.0.0.1"
PORT = 65432
SIZE = 1024
FORMAT = "utf-8"

def handle_client(conn):
    while True:
        ready, _, _ = select.select([conn], [], [], 1)
        if not ready:
            continue

        file_info = conn.recv(SIZE).decode()
        if not file_info:
            print("No file info")
            break  # No more data to receive

        if file_info == "DONE":
            print("Client has finished sending files.")
            break

        print(f"File info: {file_info}")

        file_name, file_size_str = file_info.split('!')
        file_size = int(file_size_str)
        file_path = os.path.join(storage_directory, file_name)

        if os.path.exists(file_path):
            print(f"Skipping file {file_name} since it already exists.")
            conn.send("duplicate found".encode())
            continue
        else:
            conn.send(f"File: {file_name} does not exist. Saving it....".encode())

        with open(file_path, "wb") as file:
            received_bytes = 0
            while received_bytes < file_size:
                ready, _, _ = select.select([conn], [], [], 1)
                if not ready:
                    continue
                data = conn.recv(SIZE)
                if not data:
                    break
                file.write(data)
                received_bytes += len(data)

        print(f"File: {file_name} has been saved.")
        conn.send(f"File: {file_name} has been saved.".encode())

    conn.close()


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"[LISTEN] Server listening on {HOST}:{PORT}")

    inputs = [server_socket]
    outputs = []
    message_queues = {}

    while inputs:
        readable, writable, exceptional = select.select(inputs, outputs, inputs)
        for s in readable:
            if s is server_socket:
                conn, addr = s.accept()
                conn.setblocking(0)
                inputs.append(conn)
                message_queues[conn] = []
                print(f"[NEW CONNECTION] Connected by {addr}")
            else:
                handle_client(s)
                inputs.remove(s)
                if s in outputs:
                    outputs.remove(s)
                s.close()
                del message_queues[s]

        for s in writable:
            if message_queues[s]:
                next_msg = message_queues[s].pop(0)
                s.send(next_msg)
            else:
                outputs.remove(s)

        for s in exceptional:
            inputs.remove(s)
            if s in outputs:
                outputs.remove(s)
            s.close()
            del message_queues[s]

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
