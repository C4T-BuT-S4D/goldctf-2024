from typing import Annotated, cast

import numpy as np
import pandas as pd
import pandera as pa
import pandera.typing as pt
import pydantic
import rpyc

from . import config


class AlloyComposition(pydantic.BaseModel):
    gold_fr: Annotated[float, pydantic.Field(ge=0, le=1)]
    silver_fr: Annotated[float, pydantic.Field(ge=0, le=1)]
    copper_fr: Annotated[float, pydantic.Field(ge=0, le=1)]
    platinum_fr: Annotated[float, pydantic.Field(ge=0, le=1)]

    @pydantic.model_validator(mode="after")
    def check_fraction(self):
        fr = self.gold_fr + self.silver_fr + self.copper_fr + self.platinum_fr
        if abs(fr - 1.0) > config.PRECISION:
            raise ValueError("alloy composition fractions should add up to 1")
        return self

    def restricted(self) -> "AlloyComposition":
        """
        Return rpyc-restricted version of the dataclass,
        safe to be sent to a remote endpoint.
        """

        return cast(
            AlloyComposition,
            rpyc.restricted(
                self,
                ["gold_fr", "silver_fr", "copper_fr", "platinum_fr"],
            ),
        )

    @classmethod
    def localized(cls, remote: "AlloyComposition") -> "AlloyComposition":
        """
        Recreate AlloyComposition dataclass instance from non-trusted instance,
        revalidating it in the process.
        """

        return cls(
            gold_fr=remote.gold_fr,
            silver_fr=remote.silver_fr,
            copper_fr=remote.copper_fr,
            platinum_fr=remote.platinum_fr,
        )


class Schema(pa.DataFrameModel):
    gold_ozt: pt.Series[float] = pa.Field(ge=0)
    silver_ozt: pt.Series[float] = pa.Field(ge=0)
    copper_ozt: pt.Series[float] = pa.Field(ge=0)
    platinum_ozt: pt.Series[float] = pa.Field(ge=0)
    troy_ounces: pt.Series[float] = pa.Field(ge=0)
    karat: pt.Series[float] = pa.Field(ge=0, le=24)
    fineness: pt.Series[float] = pa.Field(ge=0, le=1000)


class DataConveyor:
    """
    Conveyor for working with samples of gold,
    preparing them for later use with models.
    """

    def __init__(self, rng: np.random.Generator):
        self.rng = rng

    def template_alloy_samples(
        self,
        template: AlloyComposition,
        weight_ozt: float,
        max_deviation: float,
        samples: int,
    ) -> pd.DataFrame:
        """
        Selects a number of gold samples fitting the specified alloy template,
        with alloy composition and weight deviating no more than is requested.

        A pandas DataFrame is returned, containing the selected samples.
        """

        if weight_ozt < 0:
            raise ValueError("sample weight should be non-negative")
        elif max_deviation < 0 or max_deviation > 1:
            raise ValueError("max deviation should be a fraction")
        elif samples < 0 or samples > config.MAX_SAMPLES:
            raise ValueError(
                f"a non-negative number of samples less than {config.MAX_SAMPLES} should be specified"
            )

        validated_template = AlloyComposition.localized(template)

        df = pd.DataFrame(
            columns=[
                "gold_ozt",
                "silver_ozt",
                "copper_ozt",
                "platinum_ozt",
                "troy_ounces",
                "karat",
                "fineness",
            ]
        )

        # Array of generated weights deviating no more than max_deviation
        # from the dezired weight in troy ounces.
        weights = weight_ozt * (
            1 - (2 * max_deviation * self.rng.random(samples)) + max_deviation
        )

        # TODO optimize generation using template alloy by replacing operations
        # on each sample with operations on an array of samples.
        for i in range(samples):
            sample_alloy_fr = self.__randomize_alloy(validated_template, max_deviation)
            sample_karat = round(sample_alloy_fr[0] * 24, config.KARAT_DIGITS)
            sample_fineness = round(sample_alloy_fr[0] * 1000, config.FINENESS_DIGITS)
            sample_weight = weights[i]
            sample_alloy_ozt = sample_alloy_fr * sample_weight

            df.loc[i] = [  # type: ignore # setitem typing is broken for loc
                sample_alloy_ozt[0],
                sample_alloy_ozt[1],
                sample_alloy_ozt[2],
                sample_alloy_ozt[3],
                sample_weight,
                sample_karat,
                sample_fineness,
            ]

        # Perform basic sanity check after dataframe construction.
        Schema.validate(df)

        return df

    def random_alloy_samples(
        self, weight_ozt: float, max_deviation: float, samples: int
    ) -> pd.DataFrame:
        """
        Selects a number of random gold samples with weight deviating no more than is requested.

        A pandas DataFrame is returned, containing the selected samples.
        """
        pass

    def __randomize_alloy(
        self, template: AlloyComposition, max_deviation: float
    ) -> np.ndarray:
        fractions = np.array(
            [
                template.gold_fr,
                template.silver_fr,
                template.copper_fr,
                template.platinum_fr,
            ],
            dtype=np.float64,
        )

        # Since this private method accepts only validated compositions,
        # originally, the fractions sum to 1.
        # They are reduced by some amount so that each fraction differs no more than by max_deviation.
        fractions *= 1 - max_deviation * self.rng.random(len(fractions))

        # The resulting shortage must be then redistributed between the present alloy parts.
        shortage = 1 - np.sum(fractions)
        shortage_distribution = self.rng.random(len(fractions), dtype=np.float64)
        shortage_distribution *= fractions > config.PRECISION
        shortage_distribution /= np.sum(shortage_distribution)
        fractions += shortage * shortage_distribution

        return fractions

    def restricted(self) -> "DataConveyor":
        """
        Return rpyc-restricted version of the conveyor,
        containing only the publicly exposed endpoints safe for remote use.
        """

        return cast(
            DataConveyor,
            rpyc.restricted(
                self,
                ["template_alloy_samples", "random_alloy_samples"],
            ),
        )
