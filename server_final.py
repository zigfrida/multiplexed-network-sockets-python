import socket
import select
import sys
import os
import queue
import signal

HOST = "127.0.0.1"
PORT = 65433
SIZE = 2048
FORMAT = "utf-8"

server_socket = None
inputs = []
running = True

def signal_handler(sig, frame):
    global running
    print("\nUser Interruption. Shutting down server.")
    running = False
    for s in inputs:
        if s is not server_socket:
            s.close()
    if server_socket:
        server_socket.close()
    sys.exit(0)


def main():
    global running
    signal.signal(signal.SIGINT, signal_handler)

    print("[STARTING] server is starting...")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.settimeout(None)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"[LISTEN] Server is listening on {HOST}:{PORT}")

    inputs = [server_socket]
    outputs = []
    message_queues = {}

    while running:
        try:
            readable, writable, exceptional = select.select(inputs, outputs, inputs)
            for s in readable:
                if s is server_socket:
                    conn, addr = s.accept()
                    conn.setblocking(0)
                    inputs.append(conn)
                    message_queues[conn] = queue.Queue()
                    print(f"[NEW CONNECTION] Connected by {addr}")
                    print(f"[ACTIVE CONNECTIONS] {len(inputs) - 1}")
                else:
                    data = s.recv(SIZE)
                    
                    # data = b''
                    # while True:
                    #     part = s.recv(SIZE)
                    #     data += part
                    #     if len(part) < SIZE:
                    #         break
                    

                    if not data:
                        # No more data, close the connection
                        print(f"[CLOSED CONNECTION] No more data. Connection Closed.")
                        if s in outputs:
                            outputs.remove(s)
                        inputs.remove(s)
                        print(f"[ACTIVE CONNECTIONS] {len(inputs) - 1}")
                        s.close()
                        del message_queues[s]
                    else:
                        # Process the received data
                        if b"!" in data:
                            file_name, file_size_str, content = data.split(b"!", 2)
                            print(f"File name {file_name}")
                            file_size = int(file_size_str)
                            print(f"File size {file_size}")
                            file_name = file_name.decode()
                            file_path = os.path.join(storage_directory, file_name)

                            already_exist = os.path.exists(file_path)

                            with open(file_path, "wb") as file:
                                file.write(content)  # Write the received content

                            if already_exist:
                                message_queues[s].put(f"File {file_name} already exists. Content replaced!".encode())
                            else:
                                message_queues[s].put(f"File: {file_name} has been saved.".encode())

                            if s not in outputs:
                                outputs.append(s)


            for s in writable:
                try:
                    next_msg = message_queues[s].get_nowait()
                except queue.Empty:
                    outputs.remove(s)
                else:
                    print(f"[SEND] {next_msg.decode()}")
                    s.send(next_msg)

            for s in exceptional:
                inputs.remove(s)
                if s in outputs:
                    outputs.remove(s)
                s.close()
                del message_queues[s]
                print(f"[ACTIVE CONNECTIONS] {len(inputs) - 1}")

        except KeyboardInterrupt:
            running = False
        except Exception as e:
            print(f"An error occurred: {e}")
            running = False

    for s in inputs:
        if s is not server_socket:
            s.close()
    server_socket.close()
    sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Missing storage directory.")
    else:
        storage_directory = sys.argv[1]
        # print(f"Storage directory: {storage_directory}")

        if not os.path.exists(storage_directory):
            os.makedirs(storage_directory)
            print("Storage directory created!")

        main()
