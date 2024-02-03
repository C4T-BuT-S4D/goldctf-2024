import secrets
import traceback
from base64 import b85decode, b85encode
from typing import Optional, cast
from uuid import UUID, uuid4

import numpy as np
import rpyc
import structlog

from . import config, remote, storage
from .data import DataConveyor
from .model import ModelConveyor

UNEXPECTED_ERROR = Exception("unexpected error has occurred, please retry later")
INVALID_ACCESS_KEY_ERROR = ValueError("invalid access key provided")


@remote.safe({"data_conveyor", "model_conveyor", "create_account", "authenticate"})
class GoldConveyorService(rpyc.Service):
    def __init__(self, repository: storage.Repository):
        self.logger = structlog.stdlib.get_logger("gold-conveyor")
        self.rng = np.random.RandomState(secrets.randbits(30))
        self.repository = repository
        self.account_id: Optional[UUID] = None  # set when client has authenticated

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

    def create_account(self) -> str:
        """
        Create new account and return an access key which can be used for authentication.

        This connection will be immediatelly authenticated as the created account.
        """

        access_key = secrets.token_bytes(config.ACCESS_KEY_BYTES)
        account_id = uuid4()

        try:
            result = self.repository.save_account_creds(account_id, access_key)
        except Exception as err:
            self.logger.error(
                "unexpectedly failed to save account credentials to repository",
                error=str(err),
                stacktrace=traceback.format_exc(),
            )
            raise UNEXPECTED_ERROR

        if not result:
            raise Exception("credential generation has failed, please retry")

        self.account_id = account_id

        return GoldConveyorService.__encode_access_key(access_key)

    def authenticate(self, access_key: str):
        """
        Authenticate using the provided access key.
        """

        try:
            access_key_bytes = GoldConveyorService.__decode_access_key(access_key)
        except ValueError:
            raise INVALID_ACCESS_KEY_ERROR

        try:
            result = self.repository.authenticate_by_creds(access_key_bytes)
        except Exception as err:
            self.logger.error(
                "unexpectedly failed to authenticate client",
                error=str(err),
                stacktrace=traceback.format_exc(),
            )
            raise UNEXPECTED_ERROR

        if result is None:
            raise INVALID_ACCESS_KEY_ERROR

        self.account_id = result

    @staticmethod
    def __encode_access_key(access_key: bytes) -> str:
        return b85encode(access_key).decode()

    @staticmethod
    def __decode_access_key(access_key: str) -> bytes:
        return b85decode(access_key)
