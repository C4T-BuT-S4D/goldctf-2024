import argparse
from typing import cast

import rpyc

from conveyor.data import AlloyComposition
from conveyor.service import GoldConveyorService


def main():
    argument_parser = argparse.ArgumentParser(
        prog="conveyor-client",
        description="Example client for the RPYC-powered gold ML dataset/model conveyors.",
    )
    argument_parser.add_argument(
        "host", help="Conveyor service connection target host.", type=str
    )
    argument_parser.add_argument(
        "port", help="Conveyor service connection target port.", type=int
    )

    args = argument_parser.parse_args()
    conn: rpyc.Connection = rpyc.connect(host=args.host, port=args.port)
    service: GoldConveyorService = cast(GoldConveyorService, conn.root)

    df = service.data_conveyor.template_alloy_samples(
        AlloyComposition(gold_fr=0.83, silver_fr=0.05, copper_fr=0.02, platinum_fr=0.1),
        1,
        0.01,
        100,
    )

    print(df.iloc[15:30])
