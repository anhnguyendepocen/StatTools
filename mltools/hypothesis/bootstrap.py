"""Bootstrap hypothesis test implementations."""

import numbers
from functools import partial

import numpy as np

from .base import HypothesisTest, HypothesisTestResult

# Number of bootstrap samples to generate unless otherwise specified
_DEFAULT_MONTE_CARLO_SIZE = 1000


class BootstrapTest(HypothesisTest):
    """Generic bootstrap hypothesis test."""

    # Empirical distribution of test statistics of bootstrap data
    dist = None

    def __init__(self, x, statistic, *args, **kwargs):
        """Initialize BootstrapTest object.

        Parameters
        ----------
        x: array-like
            At most 2-dimensional sample data array.
        statistic: callable
            The test statistic, a function of the data.
        args: sequence
            Additional positional arguments to pass to the test statistic
            function.
        kwargs: dict
            Additional keyword arguments to pass to the test statistic function.
        """
        # Validate input
        if not callable(statistic):
            raise TypeError("Parameter 'statistic' must be callable")
        if np.ndim(x) > 2:
            raise ValueError("Parameter 'x' must be at most 2-dimensional.")

        self.x = np.asarray(x)
        self.size = self.x.size[0]
        self.statistic = partial(statistic, *args, **kwargs)

    def test(self, b=None, alpha=0.05, tail="two-sided", seed=None,
             sampling_procedure=None, *args, **kwargs):
        """Perform the bootstrap test.

        Parameters
        ----------
        b: int, optional
            Number of bootstrap samples to generate.
        alpha: float, optional
            Significance level (i.e., probability of a Type I error) for the
            test.
        tail: "left", "right", or "two-sided" (default)
            Specifies the kind of test to perform (i.e., one-tailed or
            two-tailed).
        seed: int, optional
            Seed for NumPy's random number generator. Only used if using Monte
            Carlo sampling to approximate the test statistic distribution.
        sampling_procedure: callable, optional
            Function for generating bootstrap samples. If this is not specified,
            bootstrap samples are generated by sampling with replacement from
            the original data.
        argss: sequence
            Positional arguments to pass to `sampling_procedure`.
        kwargss: dict
            Keyword arguments to pass to `sampling_procedure`.

        Returns
        -------
        res: HypothesisTestResult
            A named tuple with "statistic", "p_value", "lower", and "upper"
            fields. The "statistic" field stores the observed test statistic.
            The "p_value" field stores the test's p-value for the given
            significance level alpha. The "lower" and "upper" fields store the
            test's upper and lower alpha-percentile interval bounds.
        """
        if b is None:
            b = _DEFAULT_MONTE_CARLO_SIZE
        elif not isinstance(b, numbers.Integral) or b <= 0:
            raise ValueError("Parameter 'b' must be a positive integer.")
        else:
            b = int(b)

        if seed is not None:
            np.random.seed(seed)

        self.dist = np.zeros(b)
        for i in range(b):
            if sampling_procedure is None:
                # Non-parametric bootstrap
                indices = np.random.choice(self.size, self.size, replace=True)
                if np.ndim(self.x) > 1:
                    x_boot = self.x[indices, :]
                else:
                    x_boot = self.x[indices]
            else:
                x_boot = sampling_procedure(self.x, *args, **kwargs)
            self.dist[i] = self.statistic(x_boot)

        # Observed value of the test statistic
        statistic = self.statistic(self.x)

        # Compute the p-value and the percentile interval bounds
        if tail == "two-sided":
            p_value = np.sum(np.abs(self.dist) >= np.abs(statistic)) / b
            lower = np.percentile(self.dist, q=100 * alpha / 2)
            upper = np.percentile(self.dist, q=100 * (1 - alpha / 2))
        elif tail == "left":
            p_value = np.sum(self.dist <= statistic) / b
            lower = -np.inf
            upper = np.percentile(self.dist, q=100 * alpha)
        elif tail == "right":
            p_value = np.sum(self.dist >= statistic) / b
            lower = np.percentile(self.dist, q=100 * (1 - alpha))
            upper = np.inf
        else:
            raise ValueError(f"Unsupported value for parameter 'tail': {tail}")

        return HypothesisTestResult(statistic=statistic, p_value=p_value,
                                    lower=lower, upper=upper)
