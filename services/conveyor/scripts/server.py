import logging
import sys
from typing import Annotated

import rpyc
import structlog
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

import conveyor


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="conveyor_")

    debug: Annotated[bool, Field()] = False
    listen_port: Annotated[int, Field()]


def main():
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.EventRenamer("message"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    logger = structlog.stdlib.get_logger("main")

    try:
        settings = Settings.model_validate({})
    except ValidationError as err:
        for error in err.errors():
            logger.critical(
                f'validating field {".".join(map(str, error["loc"]))}: {error["msg"]}'
            )
        exit(1)

    logger.error("starting conveyor service", port=settings.listen_port)

    rpyc_logger = structlog.stdlib.get_logger("rpyc")
    rpyc_logger.setLevel(logging.WARN)

    t = rpyc.ThreadedServer(
        conveyor.service.GoldConveyorService,
        port=settings.listen_port,
        logger=rpyc_logger,
        protocol_config=dict(
            allow_safe_attrs=True,
            allow_exposed_attrs=False,
            include_local_traceback=settings.debug,
            include_local_version=settings.debug,
            allow_pickle=False,
        ),
    )
    t.start()
