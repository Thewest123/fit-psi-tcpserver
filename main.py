#!/usr/bin/env python3

import socket
import threading
import sys
import getopt
import re
from typing import Tuple
from config import SERVER_TIMEOUT

from robot import Robot


def read_message(conn: socket) -> list:

    buffer = b''
    output = []
    while (b'\a\b' not in buffer) or (buffer[-2:] != b'\a\b'):

        data = conn.recv(1000)

        if not data:  # socket closed
            return None

        buffer += data

    line, sep, buffer = buffer.partition(b'\a\b')
    output.append(line.decode())

    # While buffer is not empty
    while buffer:
        line, sep, buffer = buffer.partition(b'\a\b')
        output.append(line.decode())

    return output


def handle_client(sock: socket, conn: socket, addr, clientId: int) -> None:

    robot = Robot(conn, clientId)

    while True:

        try:
            output = read_message(conn)
        except:
            print(f"[WARN] Connection {addr} closed with ERROR")
            conn.close()
            return

        if output is None:
            break

        isError = False
        for msg in output:
            print(f" ∟ [{robot.id}] Recv: {msg}")
            if not robot.process_message(msg):
                isError = True
                break

        if (isError):
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

    clientCount = 0
    try:
        # Wait for connections
        while True:

            # Create connection with client
            conn, addr = sock.accept()
            print(f"[INFO] Recieved a connection from {addr}")

            conn.settimeout(SERVER_TIMEOUT)

            thread = threading.Thread(
                target=handle_client, args=(sock, conn, addr, clientCount))
            thread.start()

            clientCount += 1

    except KeyboardInterrupt:
        sock.close()
        print("[INFO] Stopping the server")


if __name__ == "__main__":

    main()
