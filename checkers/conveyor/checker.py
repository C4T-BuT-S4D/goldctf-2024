#!/usr/bin/env python3

import random
import sys
import traceback
from enum import Enum
from functools import partial
from typing import cast

import pandas as pd
import rpyc
from checklib import BaseChecker, Status, cquit
from conveyorlib import AlloyComposition, DataConveyor, GoldConveyorService

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
ALLOYS = [
    AlloyComposition(gold_fr=0.75, silver_fr=0.125, copper_fr=0.125, platinum_fr=0),
    AlloyComposition(gold_fr=0.75, silver_fr=0, copper_fr=0.25, platinum_fr=0),
    AlloyComposition(gold_fr=0.75, silver_fr=0.025, copper_fr=0.225, platinum_fr=0),
    AlloyComposition(gold_fr=0.75, silver_fr=0.05, copper_fr=0.2, platinum_fr=0),
    AlloyComposition(gold_fr=0.75, silver_fr=0, copper_fr=0, platinum_fr=0.25),
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
    data_conveyor: DataConveyor

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
            self._disconnect()
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
        self._connect()
        (want_weight, want_deviation, want_nsamples), df = self._generate_samples()

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

        self._disconnect()
        self.cquit(Status.OK)

    def put(self, _flag_id: str, flag: str, vuln: str):
        flag_place = self._parse_vuln(vuln)

        self._connect()
        self._disconnect()
        self.cquit(Status.OK, "public", "private")

    def get(self, flag_id: str, flag: str, vuln: str):
        flag_place = self._parse_vuln(vuln)
        assert flag_id == "private"

        self._connect()
        self._disconnect()
        self.cquit(Status.OK)

    def _connect(self):
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
        self.data_conveyor = self.service.data_conveyor

    def _disconnect(self):
        self.conn.close()

    def _parse_vuln(self, vuln: str) -> FlagPlace:  # type: ignore
        if vuln == "1":
            return FlagPlace.DATASET
        elif vuln == "2":
            return FlagPlace.MODEL
        else:
            c.cquit(Status.ERROR, "Checker error", f"Got unexpected vuln value {vuln}")

    def _generate_samples(
        self,
    ) -> tuple[tuple[float, float, int], pd.DataFrame]:
        want_weight = rnd_weight()
        want_deviation = rnd_deviation()
        want_nsamples = rnd_nsamples()
        params = (want_weight, want_deviation, want_nsamples)

        generators = [
            self.data_conveyor.random_alloy_samples,
            partial(self.data_conveyor.template_alloy_samples, random.choice(ALLOYS)),
        ]

        generators.append(
            lambda w, d, n: self.data_conveyor.concat_samples(
                generators[0](w, d, n // 2), generators[1](w, d, n - n // 2)
            )
        )

        return params, random.choice(generators)(
            want_weight, want_deviation, want_nsamples
        )


if __name__ == "__main__":

    c = Checker(sys.argv[2])

    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)
