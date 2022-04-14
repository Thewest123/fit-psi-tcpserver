#!/usr/bin/env python3

import socket
import threading
import sys
import getopt
from typing import Tuple

from robot import Robot


def read_message(conn: socket) -> str:

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

        try:
            msg = read_message(conn)
        except:
            print(f"[WARN] Connection {addr} closed with ERROR")
            conn.close()
            return

        if msg is None:
            break

        print(f" ∟ Recv: {msg}")
        if not robot.process_message(msg):
            break

    print(f"[INFO] Connection {addr} closed with success")
    conn.close()
    return


def parse_args(argv) -> Tuple[str, int]:
    host = ''
    port = 0

    # Parse command line arguments
    try:
        opts, args = getopt.getopt(
            argv, "ha:p:", ["help", "address=", "port="])
    except getopt.GetoptError:
        print(
            f"{__file__} [-a IP_ADDRESS] [--address IP_ADDRESS] [-p PORT] [--port PORT]")
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print(
                f"{sys.argv[0]} [-a IP_ADDRESS] [--address IP_ADDRESS] [-p PORT] [--port PORT]")
            sys.exit()
        elif opt in ("-a", "--address"):
            host = arg
        elif opt in ("-p", "--port"):
            port = int(arg)

    return (host, port)


def main():

    # hostname = socket.gethostname()
    # host = socket.gethostbyname(hostname)
    host, port = parse_args(sys.argv[1:])

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
