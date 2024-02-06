#!/usr/bin/env python3

import sys

import rpyc
from checklib import *

SERVICE_PORT = 12378

from enum import Enum


class FlagPlace(Enum):
    DATASET = 1
    MODEL = 2


class Checker(BaseChecker):
    vulns: int = 2
    timeout: int = 15
    uses_attack_data: bool = True

    conn: rpyc.Connection

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except ConnectionError:
            self.cquit(Status.DOWN, "Connection error", "Got connection error")
        except TimeoutError:
            self.cquit(Status.DOWN, "Timeout error", "Got timeout error")

    def check(self):
        self.connect()
        self.cquit(Status.OK)

    def put(self, _flag_id: str, flag: str, vuln: str):
        flag_place = self.parse_vuln(vuln)

        self.connect()
        self.cquit(Status.OK, "public", "private")

    def get(self, flag_id: str, flag: str, vuln: str):
        flag_place = self.parse_vuln(vuln)

        self.connect()
        assert flag_id == "private"

        self.cquit(Status.OK)

    def connect(self):
        self.conn = rpyc.connect(
            host=self.host,
            port=SERVICE_PORT,
            config=dict(
                include_local_traceback=False,
                include_local_version=False,
            ),
        )

    def parse_vuln(self, vuln: str) -> FlagPlace:
        if vuln == "1":
            return FlagPlace.DATASET
        elif vuln == "2":
            return FlagPlace.MODEL
        else:
            c.cquit(Status.ERROR, "Checker error", f"Got unexpected vuln value {vuln}")


if __name__ == "__main__":
    c = Checker(sys.argv[2])

    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)
