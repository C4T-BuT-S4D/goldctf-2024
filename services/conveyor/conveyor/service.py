import secrets
from dataclasses import dataclass
from typing import cast

import numpy as np
import rpyc
import structlog
from sklearn.model_selection import train_test_split

from .data import DataConveyor


@dataclass
class Dataset:
    x: list[float]
    y: list[float]

    def restricted(self) -> "Dataset":
        return rpyc.restricted(self, ["x", "y"])


@rpyc.service
class PipelineBuilder(rpyc.Service):
    @rpyc.exposed
    def build_dataset(self, x: list[float], y: list[float]) -> Dataset:
        if len(x) != len(y):
            raise ValueError("datasets should be built from x and y of the same size")

        # todo save to storage
        return Dataset(x, y).restricted()

    @rpyc.exposed
    def train_test_split(
        self, dataset: Dataset, test_proportion: float
    ) -> tuple[Dataset, Dataset]:
        if not (test_proportion >= 0 and test_proportion <= 1):
            raise ValueError("test_proportion should be in the range [0.0; 1.0]")

        x_train, x_test, y_train, y_test = train_test_split(
            dataset.x, dataset.y, test_size=test_proportion
        )

        return (
            Dataset(x_train, y_train).restricted(),
            Dataset(x_test, y_test).restricted(),
        )


PUBLIC_ATTRS = set(["data_conveyor"])


class GoldConveyorService(rpyc.Service):
    def __init__(self):
        self.logger = structlog.stdlib.get_logger("gold-conveyor")
        self.rng = np.random.default_rng(secrets.randbits(128))

        # Attributes exposed by the service
        self.data_conveyor = DataConveyor(self.rng).restricted()

    def on_connect(self, conn: rpyc.Connection):
        endpoints = cast(
            tuple[tuple[str, str], tuple[str, str]], conn._config["endpoints"]
        )

        self.logger = self.logger.bind(
            local=f"{endpoints[0][0]}:{endpoints[0][1]}",
            remote=f"{endpoints[1][0]}:{endpoints[1][1]}",
            connid=conn._config["connid"],
        )

        self.logger.info("client connected")

    def on_disconnect(self, conn):
        self.logger.info("client disconnected")

    def _rpyc_getattr(self, name):
        if name in PUBLIC_ATTRS:
            return getattr(self, name)
        raise AttributeError(name)
