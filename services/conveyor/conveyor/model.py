import numpy as np
import pandas as pd
from sklearn import linear_model

from . import remote


@remote.safe({"predict", "score"})
class LinearRegression(linear_model.LinearRegression):
    pass


@remote.safe({"fit_linear_regression"})
class ModelConveyor:
    """
    Conveyor for training machine learning models on processed gold samples.
    """

    def __init__(self, rng: np.random.RandomState):
        self.rng = rng

    def fit_linear_regression(
        self, x: pd.DataFrame, y: pd.DataFrame
    ) -> LinearRegression:
        """
        Initialize and fit a basic linear regression model to the given data.
        The resulting model can be used to predict or score a prediction.
        """

        return LinearRegression().fit(x, y)
