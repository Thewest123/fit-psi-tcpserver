from enum import Enum
import socket
from config import *


class State(Enum):
    UNAUTH = 0
    UNAUTH_ID = 1
    UNAUTH_CONFIRM = 2
    AUTHENTICATED = 3


class Robot:

    def __init__(self, conn: socket) -> None:
        self.conn: socket = conn
        self.state: State = State.UNAUTH

        self.name: str = None
        self.key_id: int = None
        self.hash: int = None

        self.prev_x: int = None
        self.prev_y: int = None

    def send_message(self, msg: str) -> None:
        out: str = msg + SUFFIX
        print(" ∟ Sent:", out)
        self.conn.sendall(bytes(out, encoding="utf-8"))

    def process_message(self, msg: str) -> bool:

        # Unauthorized (CLIENT_USERNAME )
        if (self.state == State.UNAUTH):

            self.name = msg

            self.send_message(SERVER_KEY_REQUEST)

            self.state_inc()
            return True

        # Unauthorized (CLIET_KEY_ID)
        if (self.state == State.UNAUTH_ID):

            self.key_id = int(msg)

            try:
                hash = self.create_hash(0)
            except Exception as e:
                print(" ∟ (err)", str(e))
                self.send_message(SERVER_KEY_OUT_OF_RANGE_ERROR)
                return False

            self.send_message(str(hash))

            self.state_inc()
            return True

        # Unauthorized (CLIENT_CONFIRMATION)
        if (self.state == State.UNAUTH_CONFIRM):

            confirm_code: int = int(msg)
            try:
                hash = self.create_hash(1)
            except Exception as e:
                print(" ∟ (err)", str(e))
                self.send_message(SERVER_LOGIN_FAILED)
                return False

            if (hash != confirm_code):
                self.send_message(SERVER_LOGIN_FAILED)
                return False

            self.send_message(SERVER_OK)

            self.state_inc()
            self.send_message(SERVER_MOVE)
            return True
            # No return because we want to continue to the AUTHENTICATED if statement

        if (self.state == State.AUTHENTICATED):
            if (msg.startswith("OK")):
                x: int = int(msg.split(" ")[1])
                y: int = int(msg.split(" ")[2])
                print(f" ∟ Position: ({x},{y})")

                # Initial set of previous position
                if not self.prev_x:
                    prev_x = x

                if not self.prev_y:
                    prev_x = y

                if (x == 0 and y == 0):
                    self.send_message(SERVER_PICK_UP)
                    return True

                self.send_message(SERVER_MOVE)
                return True

            else:
                self.send_message(SERVER_LOGOUT)
                return False

    def create_hash(self, side=0) -> int:
        sum = 0
        for char in self.name:
            sum += ord(char)

        hash = (sum * 1000) % 65536
        hash = (hash + KEY_PAIRS[self.key_id][side]) % 65536

        return int(hash)

    def state_inc(self, inc=1) -> None:
        self.state = State(self.state.value + inc)
        print(" ∟ Changed state to", self.state.name)
