from enum import Enum
import socket
import string


class State(Enum):
    UNAUTH = 0
    UNAUTH_ID = 1
    UNAUTH_CONFIRM = 2
    AUTHENTICATED = 3


class Robot:

    def __init__(self, conn: socket) -> None:
        self.conn = conn
        self.state = State.UNAUTH

        self.name = None
        self.key_id = None
        self.hash = None

    def process_message(self, msg: string) -> bool:

        # Unauthorized (CLIENT_USERNAME )
        if (self.state == State.UNAUTH):

            self.name = msg

            self.conn.sendall(b"107 KEY REQUEST\a\b")

            self.state_inc()
            return True

        # Unauthorized (CLIET_KEY_ID)
        if (self.state == State.UNAUTH_ID):

            self.key_id = int(msg)

            hash = self.create_hash(0)
            print("Hash: ", str(hash))
            self.conn.sendall(bytes(str(hash) + "\a\b", encoding="utf-8"))

            self.state_inc()
            return True

        # Unauthorized (CLIENT_CONFIRMATION)
        if (self.state == State.UNAUTH_CONFIRM):

            confirm_code = int(msg)
            hash = self.create_hash(1)

            if (hash != confirm_code):
                send_string = "300 LOGIN FAILED\a\b"
                self.conn.sendall(str.encode(send_string))
                return False

            send_string = "200 OK\a\b"
            self.conn.sendall(str.encode(send_string))

            self.state_inc()
            # return True

        if (self.state == State.AUTHENTICATED):
            send_string = "102 MOVE\a\b"
            self.conn.sendall(str.encode(send_string))

    def create_hash(self, side=0) -> int:
        key_pairs = [
            (23019, 32037),
            (32037,	29295),
            (18789,	13603),
            (16443,	29533),
            (18189,	21952),
        ]

        sum = 0
        for char in self.name:
            sum += ord(char)

        hash = (sum * 1000) % 65536
        hash = (hash + key_pairs[self.key_id][side]) % 65536

        return int(hash)

    def state_inc(self, inc=1) -> None:
        self.state = State(self.state.value + inc)
        print(self.state)
