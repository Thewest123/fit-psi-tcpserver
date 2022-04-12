from enum import Enum
import socket
from config import *


class State(Enum):
    UNAUTH = 0
    UNAUTH_ID = 1
    UNAUTH_CONFIRM = 2
    AUTHENTICATED = 3


class Direction(Enum):
    NORTH = 0,
    SOUTH = 1,
    EAST = 2,
    WEST = 3


class Robot:

    def __init__(self, conn: socket) -> None:
        self.conn: socket = conn
        self.state: State = State.UNAUTH

        self.name: str = None
        self.key_id: int = None
        self.hash: int = None

        self.prev_x: int = None
        self.prev_y: int = None
        self.direction: Direction = None

    def send_message(self, msg: str) -> None:
        out: str = msg + SUFFIX
        print(" ∟ Sent:", out)
        self.conn.sendall(bytes(out, encoding="utf-8"))

    def get_direction(self, x: int, y: int) -> Direction:
        if (self.prev_x - x > 0):
            return Direction.WEST
        elif (self.prev_x - x < 0):
            return Direction.EAST
        elif (self.prev_y - y > 0):
            return Direction.SOUTH
        elif (self.prev_y - y < 0):
            return Direction.NORTH
        else:
            print("[ERROR] Direction Error")

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

                # Get direction after first 2 messages
                if (self.direction is None and self.prev_x is not None and self.prev_y is not None):
                    self.direction = self.get_direction(x, y)
                    print(" ∟ Got direction: ", self.direction)

                # Initial set of previous position
                if (not self.prev_x):
                    self.prev_x = x
                    print(" ∟ Set prev_x: ", self.prev_x)

                if (not self.prev_y):
                    self.prev_y = y
                    print(" ∟ Set prev_y: ", self.prev_y)

                # # Change directions if previous coors are same (we're stuck behind an obstacle)
                # if (self.prev_x == x and self.prev_y == y):

                #     # Top-right quadrant
                #     if (x > 0 and y > 0):
                #         if (self.direction == Direction.)
                #         self.send_message(SERVER_TURN_RIGHT)

                if (x == 0 and y == 0):
                    self.send_message(SERVER_PICK_UP)
                    return True

                # Top right quadrant
                if (x > 0 and y > 0 and self.direction == Direction.EAST):
                    self.direction = Direction.SOUTH
                    print(" ∟ Set direction: ", self.direction)
                    self.send_message(SERVER_TURN_RIGHT)

                if (x > 0 and y > 0 and self.direction == Direction.NORTH):
                    self.direction = Direction.WEST
                    print(" ∟ Set direction: ", self.direction)
                    self.send_message(SERVER_TURN_LEFT)

                # Top left quadrant
                if (x < 0 and y > 0 and self.direction == Direction.WEST):
                    self.direction = Direction.SOUTH
                    print(" ∟ Set direction: ", self.direction)
                    self.send_message(SERVER_TURN_LEFT)

                if (x < 0 and y > 0 and self.direction == Direction.NORTH):
                    self.direction = Direction.EAST
                    print(" ∟ Set direction: ", self.direction)
                    self.send_message(SERVER_TURN_RIGHT)

                # Bottom right quadrant
                if (x > 0 and y < 0 and self.direction == Direction.EAST):
                    self.direction = Direction.NORTH
                    print(" ∟ Set direction: ", self.direction)
                    self.send_message(SERVER_TURN_LEFT)

                if (x > 0 and y < 0 and self.direction == Direction.SOUTH):
                    self.direction = Direction.WEST
                    print(" ∟ Set direction: ", self.direction)
                    self.send_message(SERVER_TURN_RIGHT)

                # Bottom left quadrant
                if (x < 0 and y < 0 and self.direction == Direction.WEST):
                    self.direction = Direction.NORTH
                    print(" ∟ Set direction: ", self.direction)
                    self.send_message(SERVER_TURN_RIGHT)

                if (x < 0 and y < 0 and self.direction == Direction.SOUTH):
                    self.direction = Direction.EAST
                    print(" ∟ Set direction: ", self.direction)
                    self.send_message(SERVER_TURN_LEFT)

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
