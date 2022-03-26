import socket
from threading import Thread


def handleClient(soc, conn, addr):
    # TODO
    print(str(soc))
    print(str(conn))
    print(str(addr))
    conn.close()


def main():

    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    port = 6969

    try:
        # Create IPv4 socket stream
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.bind((host, port))

    except socket.error as e:
        print(f"[ERROR] Can't bind to {host}:{port} ({str(e)})")
        return

    # Start listening on host:port
    soc.listen()

    print(f"[INFO] Listening on {host}:{port}")

    try:
        # Wait for connections
        while True:

            # Create connection with client
            conn, addr = soc.accept()
            print('Got connection from', addr)

            conn.settimeout(1)

            thread = Thread(target=handleClient, args=(soc, conn, addr))
            thread.start()

    except KeyboardInterrupt:
        soc.close()
        print("[INFO] Stopping the server")


if __name__ == "__main__":

    main()
