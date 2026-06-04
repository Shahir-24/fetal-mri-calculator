from __future__ import annotations

from dataclasses import dataclass

from scipy.interpolate import PchipInterpolator


@dataclass(frozen=True)
class QuadraticLinearModel:
    mean_intercept: float
    mean_linear: float
    mean_quadratic: float
    sd_intercept: float
    sd_linear: float

    def mean_sd(self, gestational_age_weeks: float) -> tuple[float, float]:
        mean = (
            self.mean_intercept
            + (self.mean_linear * gestational_age_weeks)
            + (self.mean_quadratic * gestational_age_weeks * gestational_age_weeks)
        )
        sd = self.sd_intercept + (self.sd_linear * gestational_age_weeks)
        return mean, max(sd, 1e-6)


class QuadraticMeanPchipSigmaModel:
    def __init__(
        self,
        mean_intercept: float,
        mean_linear: float,
        mean_quadratic: float,
        sigma_points: list[dict[str, float]],
    ) -> None:
        self.mean_intercept = mean_intercept
        self.mean_linear = mean_linear
        self.mean_quadratic = mean_quadratic
        x_values = [point["ga"] for point in sigma_points]
        y_values = [point["sigma"] for point in sigma_points]
        self._sigma_curve = PchipInterpolator(x_values, y_values, extrapolate=True)

    def mean_sd(self, gestational_age_weeks: float) -> tuple[float, float]:
        mean = (
            self.mean_intercept
            + (self.mean_linear * gestational_age_weeks)
            + (self.mean_quadratic * gestational_age_weeks * gestational_age_weeks)
        )
        sd = float(self._sigma_curve(gestational_age_weeks))
        return mean, max(sd, 1e-6)

