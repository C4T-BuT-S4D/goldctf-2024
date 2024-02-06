#!/usr/bin/env python3

import random
import sys
import traceback
from enum import Enum
from typing import cast

import rpyc
from checklib import *
from conveyorlib import GoldConveyorService

SERVICE_PORT = 12378
MAX_SAMPLES = 100
MIN_SAMPLES = MAX_SAMPLES // 2
FEATURES = [
    "gold_ozt",
    "silver_ozt",
    "copper_ozt",
    "platinum_ozt",
    "troy_ounces",
    "karat",
    "fineness",
]


# rnd_weight returns random number of ounces for DataConveyor
def rnd_weight() -> float:
    return random.random() * 10


# rnd_deviation returns random deviation for DataConveyor
def rnd_deviation() -> float:
    return random.random() * 0.1


# rnd_nsamples returns random number of samples for DataConveyor
def rnd_nsamples() -> int:
    return random.randint(MIN_SAMPLES, MAX_SAMPLES)


class FlagPlace(Enum):
    DATASET = 1
    MODEL = 2


class Checker(BaseChecker):
    vulns: int = 2
    timeout: int = 15
    uses_attack_data: bool = True

    conn: rpyc.Connection
    service: GoldConveyorService

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)

    def action(self, action, *args, **kwargs):
        try:
            self.connect()
            super(Checker, self).action(action, *args, **kwargs)
            self.disconnect()
        except ConnectionError as err:
            self.cquit(Status.DOWN, "Connection error", f"Connection error: {err}")
        except TimeoutError as err:
            self.cquit(Status.DOWN, "Timeout error", f"Timeout error: {err}")
        except Exception as err:
            if "_get_exception_class" in type(err).__qualname__:
                self.cquit(
                    Status.MUMBLE,
                    "Unexpected remote error",
                    f"Unexpected remote error: {traceback.format_exception(err)}",
                )
            else:
                raise

    def check(self):
        want_weight = rnd_weight()
        want_deviation = rnd_deviation()
        want_nsamples = rnd_nsamples()

        df = self.service.data_conveyor.random_alloy_samples(
            want_weight, want_deviation, want_nsamples
        )

        self.assert_eq(
            len(df),
            want_nsamples,
            "Incorrect DataFrame length after generation",
            Status.MUMBLE,
        )
        self.assert_eq(
            df.shape,
            (want_nsamples, len(FEATURES)),
            "Incorrect DataFrame shape after generation",
            Status.MUMBLE,
        )

        self.cquit(Status.OK)

    def put(self, _flag_id: str, flag: str, vuln: str):
        flag_place = self.parse_vuln(vuln)

        self.cquit(Status.OK, "public", "private")

    def get(self, flag_id: str, flag: str, vuln: str):
        flag_place = self.parse_vuln(vuln)

        assert flag_id == "private"

        self.cquit(Status.OK)

    def connect(self):
        self.conn = cast(
            rpyc.Connection,
            rpyc.connect(
                host=self.host,
                port=SERVICE_PORT,
                config=dict(
                    include_local_traceback=False,
                    include_local_version=False,
                ),
            ),
        )

        self.service = cast(GoldConveyorService, self.conn.root)

    def disconnect(self):
        self.conn.close()

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
