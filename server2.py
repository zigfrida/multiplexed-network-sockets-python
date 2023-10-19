import socket
import select
import sys
import os
import queue
import signal

HOST = "127.0.0.1"
PORT = 65433
SIZE = 1024
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

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"[LISTEN] Server listening on {HOST}:{PORT}")

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
                else:
                    data = s.recv(SIZE)
                    if not data:
                        # No more data, close the connection
                        print(f"[CLOSED] No more data. Connection Closed.")
                        if s in outputs:
                            outputs.remove(s)
                        inputs.remove(s)
                        s.close()
                        del message_queues[s]
                    else:
                        # Process the received data
                        if b"!" in data:
                            # file_info, content = data.split(b"!", 1)
                            file_name, file_size_str, content = data.split(b"!", 2)
                            # print(f"File info: {file_info}")
                            # file_name, file_size_str = file_info.decode().split('!')
                            file_size = int(file_size_str)
                            file_name = file_name.decode()
                            file_path = os.path.join(storage_directory, file_name)

                            already_exist = os.path.exists(file_path)

                            with open(file_path, "wb") as file:
                                file.write(content)  # Write the received content

                            if already_exist:
                                print(f"Skipping file {file_name} since it already exists.")
                                message_queues[s].put(f"File {file_name} already exists. Content replaced!".encode())
                            else:
                                print(f"File: {file_name} has been saved.")
                                message_queues[s].put(f"File: {file_name} has been saved.".encode())

                            if s not in outputs:
                                outputs.append(s)

                    # else:
                    #     print(f"[CLOSED] No more data. Connection Closed.")
                    #     if s in outputs:
                    #         outputs.remove(s)
                    #     inputs.remove(s)
                    #     s.close()
                    #     del message_queues[s]


            for s in writable:
                try:
                    next_msg = message_queues[s].get_nowait()
                except queue.Empty:
                    outputs.remove(s)
                else:
                    print("[SEND] Pending message, writing to socket.")
                    s.send(next_msg)

            for s in exceptional:
                inputs.remove(s)
                if s in outputs:
                    outputs.remove(s)
                s.close()
                del message_queues[s]

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
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
        print(f"Storage directory: {storage_directory}")

        if not os.path.exists(storage_directory):
            os.makedirs(storage_directory)
            print("Storage directory created!")

        main()
