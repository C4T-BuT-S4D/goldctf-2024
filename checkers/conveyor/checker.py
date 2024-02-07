#!/usr/bin/env python3

import random
import sys
import traceback
from collections import UserList
from enum import Enum
from functools import partial
from typing import cast

import pandas as pd
import rpyc
from checklib import BaseChecker, Status, cquit
from conveyorlib import (
    AlloyComposition,
    DataConveyor,
    GoldConveyorService,
    Model,
    ModelConveyor,
)

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
PRECISION = 1e-3


# rnd_weight returns random number of ounces for DataConveyor
def rnd_weight() -> float:
    return random.random() * 10


# rnd_deviation returns random deviation for DataConveyor
def rnd_deviation() -> float:
    return random.random() * 0.1


# rnd_nsamples returns random number of samples for DataConveyor
def rnd_nsamples() -> int:
    return random.randint(MIN_SAMPLES, MAX_SAMPLES)


# rnd_features returns a random list of features and a target for model training
def rnd_features() -> tuple[list[str], str]:
    features = random.choices(FEATURES, k=random.randint(2, len(FEATURES) - 1))
    left = list(set(FEATURES).difference(features))
    target = random.choice(left)
    return features, target


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
    model_conveyor: ModelConveyor

    def __init__(self, *args, **kwargs):
        super(Checker, self).__init__(*args, **kwargs)

    def action(self, action, *args, **kwargs):
        try:
            super(Checker, self).action(action, *args, **kwargs)
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

        # Generate DataFrame, like for put
        (want_weight, want_deviation, want_nsamples), df = self._generate_samples()
        self.assert_eq(
            len(df),
            want_nsamples,
            "Incorrect length of generated DataFrame",
            Status.MUMBLE,
        )
        self.assert_eq(
            df.shape,
            (want_nsamples, len(FEATURES)),
            "Incorrect shape of generated DataFrame",
            Status.MUMBLE,
        )
        self.assert_neq(
            str(df.head(1)),
            "",
            "Empty head() of generated DataFrame",
            Status.MUMBLE,
        )
        self.assert_gt(
            want_deviation,
            abs(
                df.iloc[random.randint(0, want_nsamples - 1)]["troy_ounces"]
                - want_weight
            )
            / want_weight,
            "Generated DataFrame weight deviates too much",
            Status.MUMBLE,
        )

        # Additionally test DataFrame weight normalization
        if random.randint(0, 1) == 0:
            df = self.data_conveyor.normalize_sample_weights(df)
            self.assert_gt(
                PRECISION,
                abs(df.iloc[random.randint(0, want_nsamples - 1)]["troy_ounces"] - 1.0),
                "Normalized DataFrame weight deviates too much",
                Status.MUMBLE,
            )

        # Pick DataFrame features/target and split them into train/test datasets
        features, target = rnd_features()
        x, y = df[UserList(features)], df[UserList([target])]
        splits = self.data_conveyor.split_samples(x, y, proportion=0.8)
        self.assert_eq(
            len(splits), 4, "Incorrect number of DataFrames after split", Status.MUMBLE
        )
        x_train, x_test, y_train, y_test = splits
        self.assert_eq(
            len(x_train),
            len(y_train),
            "Train X and Y length mismatch after split",
            Status.MUMBLE,
        )
        self.assert_eq(
            len(x_test),
            len(y_test),
            "Test X and Y length mismatch asfter split",
            Status.MUMBLE,
        )

        # Train model and test it
        model = self._train_model(x_train, y_train)
        test_mode = random.randint(0, 2)
        if test_mode == 0:
            score = model.score(x_test, y_test)
        elif test_mode == 1:
            predict = model.predict(x_test)
            score = self.model_conveyor.mean_absolute_error(y_test, predict)
        else:
            predict = model.predict(x_test)
            score = self.model_conveyor.mean_squared_error(y_test, predict)

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
        self.model_conveyor = self.service.model_conveyor

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

    def _train_model(self, x: pd.DataFrame, y: pd.DataFrame) -> Model:
        if random.randint(0, 1) == 0:
            return self.model_conveyor.fit_linear_regression(x, y)
        else:
            return self.model_conveyor.fit_ridge(x, y)


if __name__ == "__main__":

    c = Checker(sys.argv[2])

    try:
        c.action(sys.argv[1], *sys.argv[3:])
    except c.get_check_finished_exception():
        cquit(Status(c.status), c.public, c.private)
