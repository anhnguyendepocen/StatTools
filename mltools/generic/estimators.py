"""Defines abstract base classes for classifiers and regressors."""

import abc

import numpy as np

from .fittable import Fittable
from ..utils import validate_data


class Classifier(Fittable, metaclass=abc.ABCMeta):
    """Abstract base class for classifiers.

    Properties
    ----------
    classes : numpy.ndarray
        List of distinct class labels. These will usually be determined during
        model fitting.
    """

    classes: np.ndarray = None

    def _preprocess_classes(self, y):
        """Extract distinct classes from a response variable vector.

        This also converts the response variable vector to numeric indices
        pointing to the corresponding class in the `classes` attribute.

        Parameters
        ----------
        y : array-like
            Categorical response variable vector.

        Returns
        -------
        indices : numpy.ndarray
            Indices pointing to the class of each item in `y`.
        """
        self.classes, indices = np.unique(y, return_inverse=True)
        return indices

    @abc.abstractmethod
    def predict(self, *args, **kwargs):
        """Predict class labels from input feature data."""
        pass


class BinaryClassifier(Classifier):
    """Abstract base class for binary classifiers.

    In this case, the `classes` attribute will be a list of the form [C0, C1],
    where C0 and C1 are the distinct class labels.
    """

    def _preprocess_classes(self, y):
        """Extract distinct classes from a target vector, ensuring that there
        are at most 2 classes.

        Parameters
        ----------
        y : array-like
            Categorical response variable vector.

        Returns
        -------
        indices : numpy.ndarray
            Indices pointing to the class of each item in `y`.
        """
        indices = super(BinaryClassifier, self)._preprocess_classes(y)
        if len(self.classes) != 2:
            raise ValueError(f"This model is a binary classifier;"
                             f"found {len(self.classes)} distinct classes")
        return indices

    @abc.abstractmethod
    def predict_prob(self, *args, **kwargs):
        """Return probability P(y=C1|x) that the data belongs to class C1."""
        pass

    def predict(self, x, cutoff=0.5, *args, **kwargs):
        """Classify input samples according to their probability estimates.

        Parameters
        ----------
        x : array-like
            Explanatory variable.
        cutoff : float in [0, 1], optional
            If P(y=C1|x)>cutoff, then x is classified as class C1, otherwise C0.
        args : sequence, optional
            Positional arguments to pass to `predict_prob`.
        kwargs : dict, optional
            Keyword arguments to pass to `predict_prob`.

        Returns
        -------
        Vector of predicted class labels.
        """
        prob = self.predict_prob(x, *args, **kwargs)
        return self.classes[list(map(int, np.less(cutoff, prob)))]


class Regressor(Fittable, metaclass=abc.ABCMeta):
    """Abstract base class for regressors."""

    @abc.abstractmethod
    def predict(self, *args, **kwargs):
        """Predict numeric values from input feature data."""
        pass

    def mse(self, x, y, *args, **kwargs):
        """Compute the mean squared error of the model for given values of the
        explanatory and response variables.

        Parameters
        ----------
        x : array-like, shape (n, p)
            Explanatory variables.
        y : array-like, shape (n,)
            Response variable.
        args : sequence, optional
            Positional arguments to pass to this regressor's predict() method.
        kwargs : dict, optional
            Keyword arguments to pass to this regressor's predict() method.

        Returns
        -------
        mse : float
            The mean squared prediction error.
        """
        # Validate input
        x, y = validate_data(x, y, max_ndim=(None, 1), equal_lengths=True)
        y_hat = self.predict(x, *args, **kwargs)
        return np.mean((y - y_hat) ** 2)
