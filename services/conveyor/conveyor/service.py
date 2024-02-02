import secrets
from typing import cast

import numpy as np
import rpyc
import structlog

from . import remote
from .data import DataConveyor
from .model import ModelConveyor


@remote.safe({"data_conveyor", "model_conveyor"})
class GoldConveyorService(rpyc.Service):
    def __init__(self):
        self.logger = structlog.stdlib.get_logger("gold-conveyor")
        self.rng = np.random.RandomState(secrets.randbits(30))

        # Attributes exposed by the service
        self.data_conveyor = DataConveyor(self.rng)
        self.model_conveyor = ModelConveyor(self.rng)

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
