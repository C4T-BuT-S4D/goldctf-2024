import numpy as np
import numpy.typing as npt
from sklearn import linear_model, metrics

from . import config, remote


@remote.safe({"predict", "score"})
class LinearRegression(linear_model.LinearRegression):
    pass


@remote.safe({"predict", "score"})
class RidgeRegression(linear_model.Ridge):
    pass


@remote.safe(
    {"fit_linear_regression", "fit_ridge", "mean_absolute_error", "mean_squared_error"}
)
class ModelConveyor:
    """
    Conveyor for training machine learning models on processed gold samples.
    """

    def __init__(self, rng: np.random.RandomState):
        self.rng = rng

    def fit_linear_regression(
        self, x: npt.ArrayLike, y: npt.ArrayLike
    ) -> LinearRegression:
        """
        Initialize and fit a basic linear regression model to the given data.
        The resulting model can be used to predict or score a prediction.
        """

        return LinearRegression().fit(x, y)

    def fit_ridge(
        self, x: npt.ArrayLike, y: npt.ArrayLike, alpha: float = 1.0
    ) -> RidgeRegression:
        """
        Initialize and fit a Ridge regression model to the given data with the specified alpha.
        The resulting model can be used to predict or score a prediction.
        """

        # Sanity check to avoid bad alpha values.
        # Technically, ridge supports alpha = 0, but it isn't recommended.
        if alpha <= config.PRECISION:
            raise ValueError(f"alpha must be greater than {config.PRECISION}")

        return RidgeRegression(alpha=alpha, random_state=self.rng).fit(np.array(x), y)

    def mean_absolute_error(
        self, y_true: npt.ArrayLike, y_pred: npt.ArrayLike
    ) -> float:
        """
        Calculates the MAE for regression prediction results.
        """

        return float(metrics.mean_absolute_error(y_true, y_pred))

    def mean_squared_error(self, y_true: npt.ArrayLike, y_pred: npt.ArrayLike) -> float:
        """
        Calculates the MSE for regression prediction results.
        """

        return float(metrics.mean_squared_error(y_true, y_pred))
