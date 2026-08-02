"""Regression tests for XGBoost feature-order safety (FIX 2).

``DiseasePredictionService._prepare_df`` must return the inference DataFrame
with columns in EXACTLY ``model.feature_names_in_`` order.  XGBoost's
``inplace_predict`` (used by ``predict_proba``) does NOT reorder by name and
raises on a mismatch, so a defensive reorder + explicit missing-feature error
is required for reliability.

Regression guarantees:
- Input columns in any order are reordered to the trained order.
- A missing required feature raises a clear ValueError (fails safely) rather
  than silently substituting a wrong column.
- An end-to-end smoke prediction on the real diabetes model returns a float in
  [0, 1] when the model file is present.
"""

import os

import pandas as pd
import pytest

from backend.config import settings
from backend.services.prediction_service import DiseasePredictionService


class _FakeModel:
    """Minimal stand-in exposing only ``feature_names_in_``."""

    def __init__(self, features):
        self.feature_names_in_ = features


@pytest.fixture
def predictor():
    return DiseasePredictionService()


def test_prepare_df_reorders_columns_to_model_order(predictor):
    model = _FakeModel(["age", "bmi", "glucose", "gender"])
    df = pd.DataFrame([{"glucose": 100.0, "age": 45, "gender": "Male", "bmi": 26.8}])
    out = predictor._prepare_df(df, model, "fake")
    assert list(out.columns) == model.feature_names_in_
    assert out.iloc[0]["glucose"] == 100.0
    assert out.iloc[0]["gender"] == "Male"


def test_prepare_df_preserves_values_across_reorder(predictor):
    model = _FakeModel(["a", "b", "c"])
    df = pd.DataFrame([{"c": 3, "a": 1, "b": 2}])
    out = predictor._prepare_df(df, model, "fake")
    assert out.iloc[0].tolist() == [1, 2, 3]


def test_prepare_df_raises_on_missing_feature(predictor):
    model = _FakeModel(["age", "bmi", "glucose", "gender", "smoking_history"])
    df = pd.DataFrame([{"age": 45, "bmi": 26.8, "glucose": 100.0, "gender": "Male"}])
    with pytest.raises(ValueError, match="missing required features"):
        predictor._prepare_df(df, model, "fake")


def test_prepare_df_raises_on_extra_columns_irrelevant(predictor):
    """Extra columns beyond the model's features must not break the reorder."""
    model = _FakeModel(["age", "bmi"])
    df = pd.DataFrame([{"bmi": 26.8, "age": 45, "notes": "unused"}])
    out = predictor._prepare_df(df, model, "fake")
    assert list(out.columns) == ["age", "bmi"]


@pytest.mark.skipif(
    not os.path.exists(settings.DIABETES_MODEL_PATH),
    reason="real XGBoost model not present",
)
def test_real_diabetes_model_smoke(predictor):
    """End-to-end: real model inference survives the feature-order path."""
    predictor.load_models()
    try:
        risk = predictor.predict_diabetes(age=45, gender="Male", bmi=26.8, existing_conditions=["hypertension"])
        assert isinstance(risk, float)
        assert 0.0 <= risk <= 1.0
    finally:
        predictor.unload()
