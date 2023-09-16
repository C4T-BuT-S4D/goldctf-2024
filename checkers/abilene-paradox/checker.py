#!/usr/bin/env python3

import sys
import requests

from checklib import BaseChecker, Status, cquit
from abilene_lib import CheckMachine


class Checker(BaseChecker):
    vulns: int = 1
    timeout: int = 15
    uses_attack_data: bool = True

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)
        self.mch = CheckMachine(self)

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
        except requests.exceptions.ConnectionError:
            self.cquit(Status.DOWN, 'Connection error', 'Got requests connection error')

    def check(self):
        with self.mch.ws() as ws:
            self.mch.init_connection(ws)
            program, expected_output = self.mch.random_program()
            self.mch.test_program(ws, program, expected_output, status=Status.MUMBLE)

        self.cquit(Status.OK)

    def put(self, flag_id: str, flag: str, vuln: str):
        self.cquit(Status.OK, 'public', 'private')

    def get(self, flag_id: str, flag: str, vuln: str):
        self.cquit(Status.OK)


if __name__ == '__main__':
    c = Checker(sys.argv[2])

    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)
