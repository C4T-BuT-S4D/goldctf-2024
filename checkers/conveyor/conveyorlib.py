"""
conveyorlib contains rpyc service type stubs for interacting with the service
"""

from typing import Optional
from uuid import UUID

import pandas as pd


class DataConveyor:
    def random_alloy_samples(
        self, weight_ozt: float, max_deviation: float, samples: int
    ) -> pd.DataFrame: ...


class ModelConveyor:
    pass


class GoldConveyorService:
    account_id: Optional[UUID]
    data_conveyor: DataConveyor
    model_conveyor: ModelConveyor
