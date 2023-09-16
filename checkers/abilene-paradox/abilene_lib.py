from checklib import BaseChecker, Status
from contextlib import closing
from websocket import create_connection, WebSocket
import ssl
import base64
import time


class CheckMachine:
    def __init__(self, checker: BaseChecker):
        self.c = checker

    def ws(self):
        return closing(
            create_connection(
                f"wss://{self.c.host}:14141/ws", sslopt={"cert_reqs": ssl.CERT_NONE}
            )
        )

    def send(self, ws: WebSocket, data: bytes):
        time.sleep(0.5)
        ws.send(b'1' + data)
        self.recv(ws)

    def recv(self, ws: WebSocket) -> bytes:
        while True:
            data = ws.recv()
            if data[0] == '1':
                return base64.b64decode(data[1:].encode()).removesuffix(b'\r\n> ')

    def init_connection(self, ws: WebSocket):
        ws.send('''{"Arguments": "", "AuthToken": ""}''')
        ws.send_binary(b'''3{columns: 0, rows: 0}''')
        time.sleep(0.5)
        self.recv(ws)

    def random_program(self) -> tuple[bytes, bytes]:
        return b"'1 '2 + `", b'3'

    def test_program(self, ws: WebSocket, program: bytes, expected_output: bytes, status: Status):
        self.send(ws, program + b"\n")
        output = self.recv(ws)
        self.c.assert_eq(output, expected_output, 'Unexpected output of program', status)
