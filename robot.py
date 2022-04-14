from enum import Enum
import socket
import threading
import re

from config import *


class State(Enum):
    UNAUTH = 0
    UNAUTH_ID = 1
    UNAUTH_CONFIRM = 2
    AUTHENTICATED = 3
    WAIT_FOR_TURN = 4
    RECHARGING = 5


class Direction(Enum):
    NORTH = 0
    SOUTH = 1
    EAST = 2
    WEST = 3
    UNKNOWN = 4


class Robot:

    def __init__(self, conn: socket, clientId: int) -> None:
        self.conn: socket = conn
        self.state: State = State.UNAUTH
        self.after_recharge_state: State = None

        self.name: str = None
        self.key_id: int = None
        self.hash: int = None

        self.prev_x: int = None
        self.prev_y: int = None
        self.direction: Direction = Direction.UNKNOWN

        self.id: int = clientId

    def send_message(self, msg: str) -> None:
        out: str = msg + SUFFIX
        print(f" ∟ [{self.id}] Sent:", out)
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
            return Direction.UNKNOWN

    def set_direction(self, direction: Direction) -> None:
        self.direction = direction
        print(f" ∟ [{self.id}] Set direction: ", self.direction)
        self.state = State.WAIT_FOR_TURN

    def set_prevs(self, x: int, y: int) -> None:
        self.prev_x = x
        self.prev_y = y
        print(f" ∟ [{self.id}] Set prev ({self.prev_x},{self.prev_y})")

    def process_message(self, msg: str) -> bool:

        if (msg.startswith("RECHARGING")):
            self.after_recharge_state = self.state
            self.state = State.RECHARGING
            self.conn.settimeout(SERVER_TIMEOUT_RECHARGING)
            print(f" ∟ [{self.id}] Recharging started")
            return True

        if (self.state == State.RECHARGING):
            if (msg.startswith("FULL POWER")):
                self.state = self.after_recharge_state
                self.conn.settimeout(SERVER_TIMEOUT)
                print(f" ∟ [{self.id}] Full power")
                return True
            else:
                self.send_message(SERVER_LOGIC_ERROR)
                return False

        # Unauthorized (CLIENT_USERNAME )
        if (self.state == State.UNAUTH):

            if (len(msg) > CLIENT_USERNAME_LENGTH):
                print(len(msg))
                self.send_message(SERVER_SYNTAX_ERROR)
                return False

            self.name = msg

            self.send_message(SERVER_KEY_REQUEST)

            self.state_inc()
            return True

        # Unauthorized (CLIET_KEY_ID)
        if (self.state == State.UNAUTH_ID):

            if (' ' in msg):
                self.send_message(SERVER_SYNTAX_ERROR)
                return False

            if (len(msg) > 5):
                self.send_message(SERVER_SYNTAX_ERROR)
                return False

            try:
                self.key_id = int(msg)
            except:
                self.send_message(SERVER_SYNTAX_ERROR)
                return False

            try:
                hash = self.create_hash(0)
            except Exception as e:
                print(f" ∟ [{self.id}] (err)", str(e))
                self.send_message(SERVER_KEY_OUT_OF_RANGE_ERROR)
                return False

            self.send_message(str(hash))

            self.state_inc()
            return True

        # Unauthorized (CLIENT_CONFIRMATION)
        if (self.state == State.UNAUTH_CONFIRM):

            if (' ' in msg):
                self.send_message(SERVER_SYNTAX_ERROR)
                return False

            if (len(msg) > 5):
                self.send_message(SERVER_SYNTAX_ERROR)
                return False

            try:
                confirm_code: int = int(msg)
            except:
                self.send_message(SERVER_SYNTAX_ERROR)
                return False

            try:
                hash = self.create_hash(1)
            except Exception as e:
                print(f" ∟ [{self.id}] (err)", str(e))
                self.send_message(SERVER_LOGIN_FAILED)
                return False

            if (hash != confirm_code):
                self.send_message(SERVER_LOGIN_FAILED)
                return False

            self.send_message(SERVER_OK)

            self.state_inc()
            self.send_message(SERVER_MOVE)
            return True

        if (self.state == State.WAIT_FOR_TURN):
            if (msg.startswith("OK")):

                if (not re.match(r"^OK -?\d+ -?\d+$", msg)):
                    self.send_message(SERVER_SYNTAX_ERROR)
                    return False

                try:
                    x: int = int(msg.split(" ")[1])
                    y: int = int(msg.split(" ")[2])
                except:
                    self.send_message(SERVER_SYNTAX_ERROR)
                    return False

                print(f" ∟ [{self.id}] Turn OK")

                self.state = State.AUTHENTICATED
                self.send_message(SERVER_MOVE)
                return True

            else:
                self.send_message(SERVER_LOGOUT)
                print(f" ∟ [{self.id}] Turn FAIL")
                return False

        if (self.state == State.AUTHENTICATED):
            if (msg.startswith("OK")):

                if (not re.match(r"^OK -?\d+ -?\d+$", msg)):
                    self.send_message(SERVER_SYNTAX_ERROR)
                    return False

                try:
                    x: int = int(msg.split(" ")[1])
                    y: int = int(msg.split(" ")[2])
                except:
                    self.send_message(SERVER_SYNTAX_ERROR)
                    return False

                print(f" ∟ [{self.id}] Position: ({x},{y})")

                if (x == 0 and y == 0):
                    self.send_message(SERVER_PICK_UP)
                    return True

                # Get direction after first 2 messages
                if (self.direction is Direction.UNKNOWN and self.prev_x is not None and self.prev_y is not None):
                    self.direction = self.get_direction(x, y)
                    print(f" ∟ [{self.id}] Got direction: ", self.direction)

                # Initial set of previous position
                if (not self.prev_x):
                    self.set_prevs(x, self.prev_y)

                if (not self.prev_y):
                    self.set_prevs(self.prev_x, y)

                # Change directions if previous coords are same (we're stuck behind an obstacle)
                if (self.prev_x == x and self.prev_y == y):

                    if(self.direction == Direction.NORTH):
                        if (x < 0):
                            self.set_direction(Direction.EAST)
                            self.send_message(SERVER_TURN_RIGHT)
                        else:
                            self.set_direction(Direction.WEST)
                            self.send_message(SERVER_TURN_LEFT)
                        return True

                    elif(self.direction == Direction.SOUTH):
                        if (x < 0):
                            self.set_direction(Direction.EAST)
                            self.send_message(SERVER_TURN_LEFT)
                        else:
                            self.set_direction(Direction.WEST)
                            self.send_message(SERVER_TURN_RIGHT)
                        return True

                    elif(self.direction == Direction.EAST):
                        if (y > 0):
                            self.set_direction(Direction.SOUTH)
                            self.send_message(SERVER_TURN_RIGHT)
                        else:
                            self.set_direction(Direction.NORTH)
                            self.send_message(SERVER_TURN_LEFT)
                        return True

                    elif(self.direction == Direction.WEST):
                        if (y > 0):
                            self.set_direction(Direction.SOUTH)
                            self.send_message(SERVER_TURN_LEFT)
                        else:
                            self.set_direction(Direction.NORTH)
                            self.send_message(SERVER_TURN_RIGHT)
                        return True

                    elif(self.direction == Direction.UNKNOWN):
                        self.send_message(SERVER_TURN_LEFT)
                        self.state = State.WAIT_FOR_TURN
                        return True

                # Top right quadrant
                if (x > 0 and y > 0 and self.direction == Direction.EAST):
                    self.set_direction(Direction.SOUTH)
                    self.send_message(SERVER_TURN_RIGHT)
                    return True

                if (x > 0 and y > 0 and self.direction == Direction.NORTH):
                    self.set_direction(Direction.WEST)
                    self.send_message(SERVER_TURN_LEFT)
                    return True

                # Top left quadrant
                if (x < 0 and y > 0 and self.direction == Direction.WEST):
                    self.set_direction(Direction.SOUTH)
                    self.send_message(SERVER_TURN_LEFT)
                    return True

                if (x < 0 and y > 0 and self.direction == Direction.NORTH):
                    self.set_direction(Direction.EAST)
                    self.send_message(SERVER_TURN_RIGHT)
                    return True

                # Bottom right quadrant
                if (x > 0 and y < 0 and self.direction == Direction.EAST):
                    self.set_direction(Direction.NORTH)
                    self.send_message(SERVER_TURN_LEFT)
                    return True

                if (x > 0 and y < 0 and self.direction == Direction.SOUTH):
                    self.set_direction(Direction.WEST)
                    self.send_message(SERVER_TURN_RIGHT)
                    return True

                # Bottom left quadrant
                if (x < 0 and y < 0 and self.direction == Direction.WEST):
                    self.set_direction(Direction.NORTH)
                    self.send_message(SERVER_TURN_RIGHT)
                    return True

                if (x < 0 and y < 0 and self.direction == Direction.SOUTH):
                    self.set_direction(Direction.EAST)
                    self.send_message(SERVER_TURN_LEFT)
                    return True

                if (x == 0 or y == 0):
                    if (x == 0):
                        if (y > 0):
                            if (self.direction == Direction.NORTH):
                                self.set_direction(Direction.WEST)
                                self.send_message(SERVER_TURN_LEFT)
                                return True
                            elif (self.direction == Direction.WEST):
                                self.set_direction(Direction.SOUTH)
                                self.send_message(SERVER_TURN_LEFT)
                                return True
                            elif (self.direction == Direction.EAST):
                                self.set_direction(Direction.SOUTH)
                                self.send_message(SERVER_TURN_RIGHT)
                                return True
                            elif (self.direction == Direction.SOUTH):
                                self.set_prevs(x, y)
                                self.send_message(SERVER_MOVE)
                                return True
                        elif (y < 0):
                            if (self.direction == Direction.NORTH):
                                self.set_prevs(x, y)
                                self.send_message(SERVER_MOVE)
                                return True
                            elif (self.direction == Direction.WEST):
                                self.set_direction(Direction.NORTH)
                                self.send_message(SERVER_TURN_RIGHT)
                                return True
                            elif (self.direction == Direction.EAST):
                                self.set_direction(Direction.NORTH)
                                self.send_message(SERVER_TURN_LEFT)
                                return True
                            elif (self.direction == Direction.SOUTH):
                                self.set_direction(Direction.WEST)
                                self.send_message(SERVER_TURN_LEFT)
                                return True
                    elif (y == 0):
                        if (x > 0):
                            if (self.direction == Direction.NORTH):
                                self.set_direction(Direction.WEST)
                                self.send_message(SERVER_TURN_LEFT)
                                return True
                            elif (self.direction == Direction.WEST):
                                self.set_prevs(x, y)
                                self.send_message(SERVER_MOVE)
                                return True
                            elif (self.direction == Direction.EAST):
                                self.set_direction(Direction.NORTH)
                                self.send_message(SERVER_TURN_LEFT)
                                return True
                            elif (self.direction == Direction.SOUTH):
                                self.set_direction(Direction.WEST)
                                self.send_message(SERVER_TURN_RIGHT)
                                return True
                        elif (x < 0):
                            if (self.direction == Direction.NORTH):
                                self.set_direction(Direction.EAST)
                                self.send_message(SERVER_TURN_RIGHT)
                                return True
                            elif (self.direction == Direction.WEST):
                                self.set_direction(Direction.NORTH)
                                self.send_message(SERVER_TURN_RIGHT)
                                return True
                            elif (self.direction == Direction.EAST):
                                self.set_prevs(x, y)
                                self.send_message(SERVER_MOVE)
                                return True
                                return True
                            elif (self.direction == Direction.SOUTH):
                                self.set_direction(Direction.EAST)
                                self.send_message(SERVER_TURN_LEFT)
                                return True

                self.set_prevs(x, y)
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
        print(f" ∟ [{self.id}] Changed state to", self.state.name)
