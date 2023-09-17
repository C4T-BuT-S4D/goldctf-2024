from checklib import BaseChecker, Status, rnd_string
from contextlib import closing
from websocket import create_connection, WebSocket
import ssl
import base64
from random import randint


class CheckMachine:
    def __init__(self, checker: BaseChecker):
        self.c = checker

    def ws(self):
        return closing(
            create_connection(
                f"wss://{self.c.host}:14141/ws", sslopt={"cert_reqs": ssl.CERT_NONE}
            )
        )

    def send(self, ws: WebSocket, data: bytes) -> bytes:
        for c in data:
            ws.send(b"1" + bytes([c]))
            data = self.recv(ws)
            if data.endswith(b'\r\n> '):
                return data.removeprefix(b'\r\n')
        return self.recv(ws)

    def recv(self, ws: WebSocket) -> bytes:
        while True:
            data = ws.recv()
            if type(data) == str:
                data = data.encode()
            assert type(data) == bytes
            if data[:1] == b"1":
                return base64.b64decode(data[1:])

    def init_connection(self, ws: WebSocket):
        ws.send(b"""{"Arguments": "", "AuthToken": ""}""")
        ws.send_binary(b"""3{columns: 0, rows: 0}""")
        if b"\r\n> " not in self.recv(ws):
            self.recv(ws)

    def escape(self, program: str) -> str:
        return program.replace("\\", "\\\\").replace(" ", "\\ ")

    def get_int_program(self, value: int, depth=2) -> str:
        if depth == 0:
            v = randint(1, 5)
            if v == 1:
                x = randint(-100, 100)
                return f"'{value - x} '{x} +"
            elif v == 2:
                x = randint(-100, 100)
                return f"'{value + x} '{x} -"
            elif v == 3:
                x = randint(-100, 100)
                return f"'{x} '{value} ,"
            elif v == 4:
                name = rnd_string(10)
                return f"'{value} @{name} $$ @{name} ^ ,"
            elif v == 5:
                name = rnd_string(10)
                return f"@{name} '{value} $ @{name} ^ ,"
        elif depth == 1:
            v = randint(1, 3)
            if v == 1:
                return f"@{self.escape(self.get_int_program(value, depth - 1))} ;"
            elif v == 2:
                name = rnd_string(10)
                return f"@{name} @{self.escape(self.get_int_program(value, depth - 1))} $ :{name} ,"
            elif v == 3:
                name = rnd_string(10)
                return f"@{name} @{self.escape(self.get_int_program(value, depth - 1))} $ @{name} # ,"
        elif depth == 2:
            program = self.get_int_program(value, depth - 1)
            x = randint(1, len(program) - 1)
            return f"@{self.escape(program[:x])} @{self.escape(program[x:])} + ;"

        assert False

    def get_string_program(self, s: str) -> str:
        parts = []
        while len(s) > 0:
            x = randint(1, len(s))
            parts.append(s[:x])
            s = s[x:]

        program = ["@"]

        for part in parts:
            v = randint(1, 2)
            if v == 1:
                for c in part:
                    program.append(self.get_int_program(ord(c)))
                    program.append(".")
                    program.append("+")
            elif v == 2:
                part = part[::-1]
                for i in range(len(part) - 1, -1, -1):
                    program.append(f"@{self.escape(part)}")
                    program.append(self.get_int_program(i))
                    program.append("§")
                    program.append(".")
                    program.append("+")

        return " ".join(program)

    def get_filename(self, suffix: str) -> str:
        return f"/files/{suffix}"

    def random_program(self) -> tuple[str, bytes]:
        v = randint(1, 4)
        if v == 1:
            s = rnd_string(32)
            return (
                " ".join(
                    [
                        self.get_int_program(ord("A")),
                        self.get_int_program(0),
                        self.get_int_program(1337),
                        "&",
                        "~",
                        "+",
                        ".",
                        self.get_string_program(s),
                        "+",
                        "`",
                    ]
                ),
                b"B" + s.encode(),
            )
        elif v == 2:
            filename = self.get_filename(rnd_string(32))
            data = rnd_string(32)
            return (
                " ".join(
                    [
                        self.write_to_file_program(filename, data),
                        self.read_from_file_program(filename),
                        ",",
                        "`",
                    ]
                ),
                data.encode(),
            )
        elif v == 3:
            x = [rnd_string(32), rnd_string(32)]
            y = randint(0, 1)
            return (
                " ".join(
                    [
                        self.get_int_program(y),
                        self.get_string_program(x[0]),
                        self.get_string_program(x[1]),
                        "{",
                        "`",
                    ]
                ),
                x[y].encode(),
            )
        elif v == 4:
            s = rnd_string(32)
            return (
                " ".join(
                    [
                        self.get_string_program(s),
                        self.get_int_program(1),
                        self.get_int_program(2),
                        "<",
                        self.get_int_program(3),
                        "+",
                        self.get_int_program(4),
                        "=",
                        self.get_int_program(ord("B")),
                        "+",
                        ".",
                        "+",
                        "@\\n",
                        "+",
                        '"',
                    ]
                ),
                s.encode() + b"C",
            )

        assert False

    def write_to_file_program(self, filename: str, data: str, print_ok=False) -> str:
        return " ".join(
            [
                self.get_string_program(filename),
                self.get_string_program(data),
                "!",
            ]
            + ([self.get_string_program("ok"), ",", "`"] if print_ok else [])
        )

    def read_from_file_program(self, filename: str, print_contents=False) -> str:
        return " ".join(
            [self.get_string_program(filename), "?"] + (["`"] if print_contents else [])
        )

    def run_program(self, ws: WebSocket, program: str) -> bytes:
        self.send(ws, b"@prog @ $\n")
        for i in range(0, len(program), 50):
            self.send(
                ws, f"@prog ^ @{self.escape(program[i:i+50])} + @prog $$\n".encode()
            )
        return self.send(ws, b"@prog ^ ;\n").removesuffix(b"> ").removesuffix(b"\r\n").removeprefix(b"\r\n")

    def test_program(
        self, ws: WebSocket, program: str, expected_output: bytes, status: Status
    ):
        output = self.run_program(ws, program)
        self.c.assert_eq(
            output, expected_output, "Unexpected output of program", status
        )
