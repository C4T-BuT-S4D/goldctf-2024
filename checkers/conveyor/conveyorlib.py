"""
conveyorlib contains rpyc service type stubs for interacting with the service
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

import pandas as pd


@dataclass
class AlloyComposition:
    ALLOWED = set(["gold_fr", "silver_fr", "copper_fr", "platinum_fr"])

    gold_fr: float
    silver_fr: float
    copper_fr: float
    platinum_fr: float

    def _rpyc_getattr(self, name):
        if name in AlloyComposition.ALLOWED:
            return getattr(self, name)
        raise AttributeError("access denied")


class DataConveyor:
    def random_alloy_samples(
        self, weight_ozt: float, max_deviation: float, samples: int
    ) -> pd.DataFrame: ...

    def template_alloy_samples(
        self,
        template: AlloyComposition,
        weight_ozt: float,
        max_deviation: float,
        samples: int,
    ) -> pd.DataFrame: ...

    def concat_samples(self, *dfs: pd.DataFrame) -> pd.DataFrame: ...

    def normalize_sample_weights(self, df: pd.DataFrame) -> pd.DataFrame: ...


class ModelConveyor:
    pass


class GoldConveyorService:
    account_id: Optional[UUID]
    data_conveyor: DataConveyor
    model_conveyor: ModelConveyor
