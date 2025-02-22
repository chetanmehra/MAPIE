from __future__ import annotations

from typing import Any, Optional, Tuple, Union, Iterable, Dict
from typing_extensions import TypedDict

import pytest
import numpy as np
from sklearn.base import ClassifierMixin
from sklearn.datasets import make_classification
from sklearn.pipeline import make_pipeline, Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.utils.validation import check_is_fitted
from sklearn.dummy import DummyClassifier
from sklearn.naive_bayes import GaussianNB

from mapie.classification import MapieClassifier
from mapie.metrics import classification_coverage_score
from mapie._typing import ArrayLike


METHODS = ["score", "cumulated_score"]
WRONG_METHODS = ["scores", "cumulated", "test", "", 1, 2.5, (1, 2)]
WRONG_INCLUDE_LABELS = ["randomised", "True", "False", "other", 1, 2.5, (1, 2)]
Y_PRED_PROBA_WRONG = [
    np.array(
        [
            [0.8, 0.01, 0.1, 0.05],
            [1.0, 0.1, 0.0, 0.0]
        ]
    ),
    np.array(
        [
            [1.0, 0.0001, 0.0]
        ]
    ),
    np.array(
        [
            [0.8, 0.1, 0.05, 0.05],
            [0.9, 0.01, 0.04, 0.06]
        ]
    ),
    np.array(
        [
            [0.8, 0.1, 0.02, 0.05],
            [0.9, 0.01, 0.03, 0.06]
        ]
    )
]
Params = TypedDict(
    "Params",
    {
        "method": str,
        "cv": Optional[str],
        "random_state": Optional[int]
    }
)
ParamsPredict = TypedDict(
    "ParamsPredict",
    {
        "include_last_label": Union[bool, str],
    }
)

STRATEGIES = {
    "score": (
        Params(
            method="score",
            cv="prefit",
            random_state=None
        ),
        ParamsPredict(
            include_last_label=False
        )
    ),
    "cumulated_score_include": (
        Params(
            method="cumulated_score",
            cv="prefit",
            random_state=42
        ),
        ParamsPredict(
            include_last_label=True
        )
    ),
    "cumulated_score_not_include": (
        Params(
            method="cumulated_score",
            cv="prefit",
            random_state=42
        ),
        ParamsPredict(
            include_last_label=False
        )
    ),
    "cumulated_score_randomized": (
        Params(
            method="cumulated_score",
            cv="prefit",
            random_state=42
        ),
        ParamsPredict(
            include_last_label='randomized'
        )
    ),
    "naive": (
        Params(
            method="naive",
            cv="prefit",
            random_state=42
        ),
        ParamsPredict(
            include_last_label=True
        )
    ),
    "top_k": (
        Params(
            method="top_k",
            cv="prefit",
            random_state=42
        ),
        ParamsPredict(
            include_last_label=True
        )
    ),
}

COVERAGES = {
    "score": 7 / 9,
    "cumulated_score_include": 1,
    "cumulated_score_not_include": 5/9,
    "cumulated_score_randomized": 8/9,
    "naive": 1,
    "top_k": 1
}

y_toy_mapie = {
    "score": [
        [True, False, False],
        [True, False, False],
        [True, False, False],
        [True, True, False],
        [False, True, False],
        [False, True, True],
        [False, False, True],
        [False, False, True],
        [False, False, True],
    ],
    "cumulated_score_include": [
        [True, True, False],
        [True, True, False],
        [True, True, False],
        [True, True, False],
        [True, True, True],
        [False, True, True],
        [False, True, True],
        [False, True, True],
        [False, True, True],
    ],
    "cumulated_score_not_include": [
        [True, False, False],
        [True, False, False],
        [True, False, False],
        [False, True, False],
        [True, True, True],
        [False, True, False],
        [False, False, True],
        [False, False, True],
        [False, False, True],
    ],
    "cumulated_score_randomized": [
        [True, True, False],
        [True, True, False],
        [True, True, False],
        [True, True, False],
        [True, True, False],
        [False, True, True],
        [False, False, True],
        [False, True, True],
        [False, True, True],
    ],
    "naive": [
        [True, False, False],
        [True, False, False],
        [True, True, False],
        [True, True, False],
        [True, True, True],
        [False, True, True],
        [False, True, True],
        [False, False, True],
        [False, False, True],
    ],
    "top_k": [
        [True, True, False],
        [True, True, False],
        [True, True, False],
        [True, True, False],
        [True, True, True],
        [False, True, True],
        [False, True, True],
        [False, True, True],
        [False, True, True],
    ],
}

IMAGE_INPUT = [
    {
        'X_calib': np.zeros((3, 1024, 1024, 1)),
        'X_test': np.ones((3, 1024, 1024, 1)),
    },
    {
        'X_calib': np.zeros((3, 512, 512, 3)),
        'X_test': np.ones((3, 512, 512, 3)),
    },
    {
        'X_calib': np.zeros((3, 256, 512)),
        'X_test': np.ones((3, 256, 512)),
    }
]

X_toy = np.arange(9).reshape(-1, 1)
y_toy = np.array([0, 0, 1, 0, 1, 2, 1, 2, 2])

X_WRONG_IMAGE = [
    np.zeros((3, 1024, 1024, 3, 1)),
    np.zeros((3, 512))
]
X_good_image = np.zeros((3, 1024, 1024, 3))
y_toy_image = np.array([0, 0, 1])

n_classes = 4
X, y = make_classification(
    n_samples=500,
    n_features=10,
    n_informative=3,
    n_classes=n_classes,
    random_state=1,
)


class CumulatedScoreClassifier:

    def __init__(self) -> None:
        self.X_calib = np.array([0, 1, 2]).reshape(-1, 1)
        self.y_calib = np.array([0, 1, 2])
        self.y_calib_scores = np.array(
            [[0.750183952461055], [0.029571416154050345], [0.9268006058188594]]
        )
        self.X_test = np.array([3, 4, 5]).reshape(-1, 1)
        self.y_pred_sets = np.array(
            [[True, True, False], [False, True, True], [True, True, False]]
        )
        self.classes_ = self.y_calib

    def fit(self, X: ArrayLike, y: ArrayLike) -> CumulatedScoreClassifier:
        self.fitted_ = True
        return self

    def predict(self, X: ArrayLike) -> ArrayLike:
        return np.array([1, 2, 1])

    def predict_proba(self, X: ArrayLike) -> ArrayLike:
        if np.max(X) <= 2:
            return np.array(
                [[0.4, 0.5, 0.1], [0.2, 0.6, 0.2], [0.6, 0.3, 0.1]]
            )
        else:
            return np.array(
                [[0.2, 0.7, 0.1], [0.1, 0.2, 0.7], [0.3, 0.5, 0.2]]
            )


class ImageClassifier:
    def __init__(self, X_calib: ArrayLike, X_test: ArrayLike) -> None:
        self.X_calib = X_calib
        self.y_calib = np.array([0, 1, 2])
        self.y_calib_scores = np.array(
            [[0.750183952461055], [0.029571416154050345], [0.9268006058188594]]
        )
        self.X_test = X_test
        self.y_pred_sets = np.array(
            [[True, True, False], [False, True, True], [True, True, False]]
        )
        self.classes_ = self.y_calib

    def fit(self, X: ArrayLike, y: ArrayLike) -> ImageClassifier:
        self.fitted_ = True
        return self

    def predict(self, X: ArrayLike) -> ArrayLike:
        return np.array([1, 2, 1])

    def predict_proba(self, X: ArrayLike) -> ArrayLike:
        if np.max(X) == 0:
            return np.array(
                [[0.4, 0.5, 0.1], [0.2, 0.6, 0.2], [0.6, 0.3, 0.1]]
            )
        else:
            return np.array(
                [[0.2, 0.7, 0.1], [0.1, 0.2, 0.7], [0.3, 0.5, 0.2]]
            )


class WrongOutputModel():

    def __init__(self, proba_out: ArrayLike):
        self.trained_ = True
        self.proba_out = proba_out
        self.classes_ = proba_out.shape[1]

    def fit(self, *args: Any) -> None:
        """Dummy fit."""

    def predict_proba(self, *args: Any) -> ArrayLike:
        return self.proba_out

    def predict(self, *args: Any) -> ArrayLike:
        pred = (
            self.proba_out == self.proba_out.max(axis=1)[:, None]
        ).astype(int)
        return pred


def do_nothing(*args: Any) -> None:
    "Mock function that does nothing."
    pass


def test_initialized() -> None:
    """Test that initialization does not crash."""
    MapieClassifier()


def test_default_parameters() -> None:
    """Test default values of input parameters."""
    mapie_clf = MapieClassifier()
    assert mapie_clf.method == "score"
    assert mapie_clf.cv == "prefit"


@pytest.mark.parametrize("strategy", [*STRATEGIES])
def test_valid_estimator(strategy: str) -> None:
    """Test that valid estimators are not corrupted, for all strategies."""
    clf = LogisticRegression().fit(X_toy, y_toy)
    mapie_clf = MapieClassifier(estimator=clf, **STRATEGIES[strategy][0])
    mapie_clf.fit(X_toy, y_toy)
    assert isinstance(mapie_clf.single_estimator_, LogisticRegression)


@pytest.mark.parametrize("method", METHODS)
def test_valid_method(method: str) -> None:
    """Test that valid methods raise no errors."""
    mapie_clf = MapieClassifier(method=method)
    mapie_clf.fit(X_toy, y_toy)
    check_is_fitted(mapie_clf, mapie_clf.fit_attributes)


@pytest.mark.parametrize("cv", [None, "prefit"])
def test_valid_cv(cv: Any) -> None:
    """Test that valid cv raise no errors."""
    model = LogisticRegression(multi_class="multinomial")
    model.fit(X_toy, y_toy)
    mapie_clf = MapieClassifier(estimator=model, cv=cv)
    mapie_clf.fit(X_toy, y_toy)


@pytest.mark.parametrize(
    "include_last_label",
    [-3.14, 1.5, -2, 0, 1, "cv", DummyClassifier(), [1, 2]]
)
def test_invalid_include_last_label(include_last_label: Any) -> None:
    """Test that invalid include_last_label raise errors."""
    mapie_clf = MapieClassifier()
    mapie_clf.fit(X_toy, y_toy)
    with pytest.raises(
        ValueError, match=r".*Invalid include_last_label argument.*"
    ):
        mapie_clf.predict(
            X_toy,
            y_toy,
            include_last_label=include_last_label
        )


@pytest.mark.parametrize("strategy", [*STRATEGIES])
@pytest.mark.parametrize("dataset", [(X, y), (X_toy, y_toy)])
@pytest.mark.parametrize("alpha", [0.2, [0.2, 0.3], (0.2, 0.3)])
def test_predict_output_shape(
    strategy: str, alpha: Any, dataset: Tuple[ArrayLike, ArrayLike]
) -> None:
    """Test predict output shape."""
    args_init, args_predict = STRATEGIES[strategy]
    include_last_label = args_predict['include_last_label']
    mapie_clf = MapieClassifier(**args_init)
    X, y = dataset
    mapie_clf.fit(X, y)
    y_pred, y_ps = mapie_clf.predict(
        X,
        include_last_label=include_last_label,
        alpha=alpha
    )
    n_alpha = len(alpha) if hasattr(alpha, "__len__") else 1
    assert y_pred.shape == (X.shape[0],)
    assert y_ps.shape == (X.shape[0], len(np.unique(y)), n_alpha)


@pytest.mark.parametrize("strategy", [*STRATEGIES])
def test_results_for_same_alpha(strategy: str) -> None:
    """
    Test that predictions and intervals
    are similar with two equal values of alpha.
    """
    args_init, args_predict = STRATEGIES[strategy]
    include_last_label = args_predict['include_last_label']
    mapie_clf = MapieClassifier(**args_init)
    mapie_clf.fit(X, y)
    _, y_ps = mapie_clf.predict(
        X,
        include_last_label=include_last_label,
        alpha=[0.1, 0.1]
    )
    np.testing.assert_allclose(y_ps[:, 0, 0], y_ps[:, 0, 1])
    np.testing.assert_allclose(y_ps[:, 1, 0], y_ps[:, 1, 1])


@pytest.mark.parametrize("strategy", [*STRATEGIES])
@pytest.mark.parametrize(
    "alpha", [np.array([0.05, 0.1]), [0.05, 0.1], (0.05, 0.1)]
)
def test_results_for_alpha_as_float_and_arraylike(
    strategy: str, alpha: Any
) -> None:
    """Test that output values do not depend on type of alpha."""
    args_init, args_predict = STRATEGIES[strategy]
    include_last_label = args_predict['include_last_label']
    mapie_clf = MapieClassifier(**args_init)
    mapie_clf.fit(X, y)
    y_pred_float1, y_ps_float1 = mapie_clf.predict(
        X,
        include_last_label=include_last_label,
        alpha=alpha[0]
    )
    y_pred_float2, y_ps_float2 = mapie_clf.predict(
        X,
        include_last_label=include_last_label,
        alpha=alpha[1]
    )
    y_pred_array, y_ps_array = mapie_clf.predict(
        X,
        include_last_label=include_last_label,
        alpha=alpha
    )
    np.testing.assert_allclose(y_pred_float1, y_pred_array)
    np.testing.assert_allclose(y_pred_float2, y_pred_array)
    np.testing.assert_allclose(y_ps_float1[:, :, 0], y_ps_array[:, :, 0])
    np.testing.assert_allclose(y_ps_float2[:, :, 0], y_ps_array[:, :, 1])


@pytest.mark.parametrize("strategy", [*STRATEGIES])
def test_results_single_and_multi_jobs(strategy: str) -> None:
    """
    Test that MapieRegressor gives equal predictions
    regardless of number of parallel jobs.
    """
    args_init, args_predict = STRATEGIES[strategy]
    include_last_label = args_predict['include_last_label']
    mapie_clf_single = MapieClassifier(n_jobs=1, **args_init)
    mapie_clf_multi = MapieClassifier(n_jobs=-1, **args_init)
    mapie_clf_single.fit(X_toy, y_toy)
    mapie_clf_multi.fit(X_toy, y_toy)
    y_pred_single, y_ps_single = mapie_clf_single.predict(
        X_toy,
        include_last_label=include_last_label,
        alpha=0.2
    )
    y_pred_multi, y_ps_multi = mapie_clf_multi.predict(
        X_toy,
        include_last_label=include_last_label,
        alpha=0.2
    )
    np.testing.assert_allclose(y_pred_single, y_pred_multi)
    np.testing.assert_allclose(y_ps_single, y_ps_multi)


@pytest.mark.parametrize("strategy", [*STRATEGIES])
def test_results_with_constant_sample_weights(
    strategy: str
) -> None:
    """
    Test predictions when sample weights are None
    or constant with different values.
    """
    args_init, args_predict = STRATEGIES[strategy]
    include_last_label = args_predict['include_last_label']
    n_samples = len(X_toy)
    mapie_clf0 = MapieClassifier(**args_init)
    mapie_clf1 = MapieClassifier(**args_init)
    mapie_clf2 = MapieClassifier(**args_init)
    mapie_clf0.fit(X_toy, y_toy, sample_weight=None)
    mapie_clf1.fit(X_toy, y_toy, sample_weight=np.ones(shape=n_samples))
    mapie_clf2.fit(X_toy, y_toy, sample_weight=np.ones(shape=n_samples) * 5)
    y_pred0, y_ps0 = mapie_clf0.predict(
        X_toy,
        include_last_label=include_last_label,
        alpha=0.2
    )
    y_pred1, y_ps1 = mapie_clf1.predict(
        X_toy,
        include_last_label=include_last_label,
        alpha=0.2
    )
    y_pred2, y_ps2 = mapie_clf2.predict(
        X_toy,
        include_last_label=include_last_label,
        alpha=0.2
    )
    np.testing.assert_allclose(y_pred0, y_pred1)
    np.testing.assert_allclose(y_pred0, y_pred2)
    np.testing.assert_allclose(y_ps0, y_ps1)
    np.testing.assert_allclose(y_ps0, y_ps2)


@pytest.mark.parametrize(
    "alpha", [[0.2, 0.8], (0.2, 0.8), np.array([0.2, 0.8]), None]
)
def test_valid_prediction(alpha: Any) -> None:
    """Test fit and predict."""
    model = LogisticRegression(multi_class="multinomial")
    model.fit(X_toy, y_toy)
    mapie_clf = MapieClassifier(estimator=model, cv="prefit")
    mapie_clf.fit(X_toy, y_toy)
    mapie_clf.predict(X_toy, alpha=alpha)


@pytest.mark.parametrize("strategy", [*STRATEGIES])
def test_toy_dataset_predictions(strategy: str) -> None:
    """Test prediction sets estimated by MapieClassifier on a toy dataset"""
    args_init, args_predict = STRATEGIES[strategy]
    include_last_label = args_predict['include_last_label']
    clf = GaussianNB().fit(X_toy, y_toy)
    mapie_clf = MapieClassifier(estimator=clf, **args_init)
    mapie_clf.fit(X_toy, y_toy)
    _, y_ps = mapie_clf.predict(
        X_toy,
        include_last_label=include_last_label,
        alpha=0.2
    )
    np.testing.assert_allclose(
        classification_coverage_score(y_toy, y_ps[:, :, 0]),
        COVERAGES[strategy],
    )
    np.testing.assert_allclose(y_ps[:, :, 0], y_toy_mapie[strategy])


def test_cumulated_scores() -> None:
    """Test cumulated score method on a tiny dataset."""
    alpha = [0.65]
    quantile = [0.750183952461055]
    # fit
    cumclf = CumulatedScoreClassifier()
    cumclf.fit(cumclf.X_calib, cumclf.y_calib)
    mapie_clf = MapieClassifier(
        cumclf,
        method="cumulated_score",
        cv="prefit",
        random_state=42
    )
    mapie_clf.fit(cumclf.X_calib, cumclf.y_calib)
    np.testing.assert_allclose(
        mapie_clf.conformity_scores_, cumclf.y_calib_scores
    )
    # predict
    _, y_ps = mapie_clf.predict(
        cumclf.X_test,
        include_last_label=True,
        alpha=alpha
    )
    np.testing.assert_allclose(mapie_clf.quantiles_, quantile)
    np.testing.assert_allclose(y_ps[:, :, 0], cumclf.y_pred_sets)


@pytest.mark.parametrize("X", IMAGE_INPUT)
def test_image_cumulated_scores(X: Dict[str, ArrayLike]) -> None:
    """Test image as input for cumulated_score method."""
    alpha = [0.65]
    quantile = [0.750183952461055]
    # fit
    X_calib = X['X_calib']
    X_test = X['X_test']
    cumclf = ImageClassifier(X_calib, X_test)
    cumclf.fit(cumclf.X_calib, cumclf.y_calib)
    mapie = MapieClassifier(
        cumclf,
        method="cumulated_score",
        cv="prefit",
        random_state=42
    )
    mapie.fit(cumclf.X_calib, cumclf.y_calib, image_input=True)
    np.testing.assert_allclose(mapie.conformity_scores_, cumclf.y_calib_scores)
    # predict
    _, y_ps = mapie.predict(
        cumclf.X_test,
        include_last_label=True,
        alpha=alpha
    )
    np.testing.assert_allclose(mapie.quantiles_, quantile)
    np.testing.assert_allclose(y_ps[:, :, 0], cumclf.y_pred_sets)


@pytest.mark.parametrize("y_pred_proba", Y_PRED_PROBA_WRONG)
def test_sum_proba_to_one_fit(y_pred_proba: ArrayLike) -> None:
    """
    Test if when the output probabilities of the model do not
    sum to one, return an error in the fit method.
    """
    wrong_model = WrongOutputModel(y_pred_proba)
    mapie_clf = MapieClassifier(wrong_model)
    with pytest.raises(
        AssertionError, match=r".*The sum of the scores is not equal to one.*"
    ):
        mapie_clf.fit(X_toy, y_toy)


@pytest.mark.parametrize("y_pred_proba", Y_PRED_PROBA_WRONG)
@pytest.mark.parametrize("alpha", [0.2, [0.2, 0.3], (0.2, 0.3)])
def test_sum_proba_to_one_predict(
    y_pred_proba: ArrayLike,
    alpha: Union[float, Iterable[float]]
) -> None:
    """
    Test if when the output probabilities of the model do not
    sum to one, return an error in the predict method.
    """
    wrong_model = WrongOutputModel(y_pred_proba)
    mapie_clf = MapieClassifier()
    mapie_clf.fit(X_toy, y_toy)
    mapie_clf.single_estimator_ = wrong_model
    with pytest.raises(
        AssertionError, match=r".*The sum of the scores is not equal to one.*"
    ):
        mapie_clf.predict(X_toy, alpha=alpha)


@pytest.mark.parametrize(
    "estimator", [LogisticRegression(), make_pipeline(LogisticRegression())]
)
def test_classifier_without_classes_attribute(
    estimator: ClassifierMixin
) -> None:
    """
    Test that prefitted classifier without 'classes_ 'attribute raises error.
    """
    estimator.fit(X_toy, y_toy)
    if isinstance(estimator, Pipeline):
        delattr(estimator[-1], "classes_")
    else:
        delattr(estimator, "classes_")
    mapie = MapieClassifier(estimator=estimator, cv="prefit")
    with pytest.raises(
        AttributeError, match=r".*does not contain 'classes_'.*"
    ):
        mapie.fit(X_toy, y_toy)


@pytest.mark.parametrize("X_wrong_image", X_WRONG_IMAGE)
def test_wrong_image_shape_fit(X_wrong_image: ArrayLike) -> None:
    """
    Test that ValueError is raised if image has not 3 or 4 dimensions in fit.
    """
    cumclf = ImageClassifier(X_wrong_image, y_toy_image)
    cumclf.fit(cumclf.X_calib, cumclf.y_calib)
    mapie = MapieClassifier(
        cumclf,
        method="cumulated_score",
        cv="prefit",
        random_state=42
    )
    with pytest.raises(ValueError, match=r"Invalid X.*"):
        mapie.fit(cumclf.X_calib, cumclf.y_calib, image_input=True)


@pytest.mark.parametrize("X_wrong_image", X_WRONG_IMAGE)
def test_wrong_image_shape_predict(X_wrong_image: ArrayLike) -> None:
    """
    Test that ValueError is raised if image has not
    3 or 4 dimensions in predict.
    """
    cumclf = ImageClassifier(X_good_image, y_toy_image)
    cumclf.fit(cumclf.X_calib, cumclf.y_calib)
    mapie = MapieClassifier(
        cumclf,
        method="cumulated_score",
        cv="prefit",
        random_state=42
    )
    mapie.fit(cumclf.X_calib, cumclf.y_calib, image_input=True,)
    with pytest.raises(ValueError, match=r"Invalid X.*"):
        mapie.predict(X_wrong_image)


def test_undefined_model() -> None:
    """
    Test ValueError is raised if no model is specified with image input.
    """
    mapie = MapieClassifier()
    with pytest.raises(ValueError, match=r"LogisticRegression's input.*"):
        mapie.fit(X_good_image, y_toy_image, image_input=True,)


@pytest.mark.parametrize("method", WRONG_METHODS)
def test_method_error_in_fit(monkeypatch: Any, method: str) -> None:
    """Test else condition for the method in .fit"""
    monkeypatch.setattr(
        MapieClassifier, "_check_parameters", do_nothing
    )
    mapie_clf = MapieClassifier(method=method)
    with pytest.raises(ValueError, match=r".*Invalid method.*"):
        mapie_clf.fit(X_toy, y_toy)


@pytest.mark.parametrize("method", WRONG_METHODS)
@pytest.mark.parametrize("alpha", [0.2, [0.2, 0.3], (0.2, 0.3)])
def test_method_error_in_predict(method: Any, alpha: float) -> None:
    """Test else condition for the method in .predict"""
    mapie_clf = MapieClassifier(method='score')
    mapie_clf.fit(X_toy, y_toy)
    mapie_clf.method = method
    with pytest.raises(ValueError, match=r".*Invalid method.*"):
        mapie_clf.predict(X_toy, alpha=alpha)


@pytest.mark.parametrize("include_labels", WRONG_INCLUDE_LABELS)
@pytest.mark.parametrize("alpha", [0.2, [0.2, 0.3], (0.2, 0.3)])
def test_include_label_error_in_predict(
    monkeypatch: Any, include_labels: Union[bool, str], alpha: float
) -> None:
    """Test else condition for include_label parameter in .predict"""
    monkeypatch.setattr(
        MapieClassifier,
        "_check_include_last_label",
        do_nothing
    )
    mapie_clf = MapieClassifier(method='cumulated_score')
    mapie_clf.fit(X_toy, y_toy)
    with pytest.raises(ValueError, match=r".*Invalid include.*"):
        mapie_clf.predict(
            X_toy, alpha=alpha,
            include_last_label=include_labels
        )
