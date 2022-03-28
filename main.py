#!/usr/bin/env python3

import socket
import string
import threading

from robot import Robot


def read_message(conn: socket) -> string:

    buffer = b''
    while b'\a\b' not in buffer:

        data = conn.recv(64)

        if not data:  # socket closed
            return None

        buffer += data

    line, sep, buffer = buffer.partition(b'\a\b')
    return line.decode()


def handle_client(sock: socket, conn: socket, addr) -> None:

    robot = Robot(conn)

    while True:

        msg = read_message(conn)
        if msg is None:
            break

        print(f"Message to process: {msg}")
        if not robot.process_message(msg):
            break

    print(f"[INFO] Connection {addr} closed")
    conn.close()


def main():

    # hostname = socket.gethostname()
    # host = socket.gethostbyname(hostname)
    port = 6969

    try:
        # Create IPv4 socket stream
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', port))

    except socket.error as e:
        print(f"[ERROR] Can't bind to port {port} ({str(e)})")
        return

    # Start listening on host:port
    sock.listen()

    print(f"[INFO] Listening on {sock.getsockname()}")

    try:
        # Wait for connections
        while True:

            # Create connection with client
            conn, addr = sock.accept()
            print(f"[INFO] Recieved a connection from {addr}")

            conn.settimeout(1)

            thread = threading.Thread(
                target=handle_client, args=(sock, conn, addr))
            thread.start()

    except KeyboardInterrupt:
        sock.close()
        print("[INFO] Stopping the server")


if __name__ == "__main__":

    main()
