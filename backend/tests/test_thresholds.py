"""Tests for threshold-based classification.

Verifies:
- Every boundary value maps to exactly one level.
- Every possible score produces a deterministic result.
- Validation catches every configuration error.
- The catch-all level always serves as the default.
"""

import json
import os
import tempfile

import pytest
from backend.services.classification import ThresholdConfig, Threshold


# ── DCI (higher_is_better=True) ──────────────────────────────────────────────

DCI_DATA = {
    "levels": [
        {"value": 0.85, "label": "High Consistency"},
        {"value": 0.70, "label": "Moderate Consistency"},
        {"value": 0.50, "label": "Low Consistency"},
        {"label": "Very Low Consistency"},
    ],
}
DCI_CONFIG = ThresholdConfig.from_dict(DCI_DATA, higher_is_better=True, name="DCI")


class TestDCIClassification:
    @pytest.mark.parametrize("score,expected", [
        (1.00, "High Consistency"),
        (0.85, "High Consistency"),
        (0.84, "Moderate Consistency"),
        (0.70, "Moderate Consistency"),
        (0.69, "Low Consistency"),
        (0.50, "Low Consistency"),
        (0.49, "Very Low Consistency"),
        (0.00, "Very Low Consistency"),
        (-1.0, "Very Low Consistency"),
    ])
    def test_boundary_values(self, score, expected):
        assert DCI_CONFIG.classify(score) == expected

    def test_every_point_maps_to_exactly_one_level(self):
        valid = {"High Consistency", "Moderate Consistency",
                 "Low Consistency", "Very Low Consistency"}
        for i in range(1001):
            score = i / 1000.0
            result = DCI_CONFIG.classify(score)
            assert result in valid, f"DCI {score} → '{result}'"

    def test_classify_never_raises_for_valid_config(self):
        for score in [float("-inf"), -5.0, 0.0, 0.5, 1.0, 2.0, float("inf")]:
            DCI_CONFIG.classify(score)  # must never raise


# ── NIS (higher_is_better=False) ─────────────────────────────────────────────

NIS_DATA = {
    "levels": [
        {"value": 0.20, "label": "Balanced Diet"},
        {"value": 0.40, "label": "Mild Imbalance"},
        {"value": 0.60, "label": "Moderate Imbalance"},
        {"value": 0.80, "label": "High Imbalance"},
        {"label": "Severe Imbalance"},
    ],
}
NIS_CONFIG = ThresholdConfig.from_dict(NIS_DATA, higher_is_better=False, name="NIS")


class TestNISClassification:
    @pytest.mark.parametrize("score,expected", [
        (0.00, "Balanced Diet"),
        (0.19, "Balanced Diet"),
        (0.20, "Mild Imbalance"),
        (0.39, "Mild Imbalance"),
        (0.40, "Moderate Imbalance"),
        (0.59, "Moderate Imbalance"),
        (0.60, "High Imbalance"),
        (0.79, "High Imbalance"),
        (0.80, "Severe Imbalance"),
        (999.0, "Severe Imbalance"),
    ])
    def test_boundary_values(self, score, expected):
        assert NIS_CONFIG.classify(score) == expected

    def test_every_point_maps_to_exactly_one_level(self):
        valid = {"Balanced Diet", "Mild Imbalance", "Moderate Imbalance",
                 "High Imbalance", "Severe Imbalance"}
        for i in range(0, 5000):
            score = i / 100.0
            result = NIS_CONFIG.classify(score)
            assert result in valid, f"NIS {score} → '{result}'"

    def test_classify_never_raises_for_valid_config(self):
        for score in [float("-inf"), -5.0, 0.0, 0.5, 1.0, 999.0, float("inf")]:
            NIS_CONFIG.classify(score)  # must never raise


# ── from_file ────────────────────────────────────────────────────────────────

class TestFromFile:
    def test_existing_file_loads(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(NIS_DATA, f)
            path = f.name
        try:
            config = ThresholdConfig.from_file(
                path, higher_is_better=False, name="NIS"
            )
            assert config.classify(0.10) == "Balanced Diet"
        finally:
            os.unlink(path)

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            ThresholdConfig.from_file("/nonexistent/path.json", True, "test")


# ── Edge cases ───────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_nan_classifies_as_default(self):
        assert DCI_CONFIG.classify(float("nan")) == "Very Low Consistency"
        assert NIS_CONFIG.classify(float("nan")) == "Severe Imbalance"

    def test_positive_infinity_higher_is_better(self):
        assert DCI_CONFIG.classify(float("inf")) == "High Consistency"

    def test_negative_infinity_lower_is_better(self):
        assert NIS_CONFIG.classify(float("-inf")) == "Balanced Diet"

    def test_threshold_dataclass_is_frozen(self):
        t = Threshold(label="Test", value=0.5)
        with pytest.raises(Exception):
            t.label = "Changed"  # FrozenInstanceError


# ── Validation: structure ────────────────────────────────────────────────────

class TestValidationStructure:
    def test_empty_levels_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            ThresholdConfig.from_dict({"levels": []}, True, "test")

    def test_empty_label_raises(self):
        with pytest.raises(ValueError, match="non-empty string"):
            ThresholdConfig.from_dict(
                {"levels": [{"value": 1.0, "label": ""},
                            {"label": "Catch"}]},
                True, "test",
            )

    def test_non_string_label_raises(self):
        with pytest.raises(ValueError, match="non-empty string"):
            ThresholdConfig.from_dict(
                {"levels": [{"value": 1.0, "label": 123},
                            {"label": "Catch"}]},
                True, "test",
            )

    def test_duplicate_labels_raises(self):
        with pytest.raises(ValueError, match="duplicate level label"):
            ThresholdConfig.from_dict(
                {"levels": [
                    {"value": 0.70, "label": "Same"},
                    {"value": 0.50, "label": "Same"},
                    {"label": "Default"},
                ]}, True, "test",
            )

    def test_duplicate_threshold_values_raises(self):
        with pytest.raises(ValueError, match="duplicate threshold value"):
            ThresholdConfig.from_dict(
                {"levels": [
                    {"value": 0.50, "label": "A"},
                    {"value": 0.50, "label": "B"},
                    {"label": "Default"},
                ]}, True, "test",
            )


# ── Validation: value type checking ──────────────────────────────────────────

class TestValueTypeChecking:
    def test_non_numeric_value_raises(self):
        with pytest.raises(ValueError, match="must be a number"):
            ThresholdConfig.from_dict(
                {"levels": [
                    {"value": "high", "label": "X"},
                    {"label": "Catch"},
                ]}, True, "test",
            )

    def test_string_value_raises(self):
        with pytest.raises(ValueError, match="must be a number"):
            ThresholdConfig.from_dict(
                {"levels": [
                    {"value": "0.85abc", "label": "X"},
                    {"label": "Catch"},
                ]}, True, "test",
            )

    def test_list_value_raises(self):
        with pytest.raises(ValueError, match="must be a number"):
            ThresholdConfig.from_dict(
                {"levels": [
                    {"value": [1, 2], "label": "X"},
                    {"label": "Catch"},
                ]}, True, "test",
            )

    def test_boolean_value_raises(self):
        with pytest.raises(ValueError, match="must be a number"):
            ThresholdConfig.from_dict(
                {"levels": [
                    {"value": True, "label": "X"},
                    {"label": "Catch"},
                ]}, True, "test",
            )


# ── Validation: catch-all ────────────────────────────────────────────────────

class TestValidationCatchAll:
    def test_missing_catch_all_raises(self):
        with pytest.raises(ValueError, match="missing catch-all"):
            ThresholdConfig.from_dict(
                {"levels": [{"value": 0.50, "label": "A"}]}, True, "test",
            )

    def test_multiple_catch_all_raises(self):
        with pytest.raises(ValueError, match="at most one"):
            ThresholdConfig.from_dict(
                {"levels": [{"label": "A"}, {"label": "B"}]}, True, "test",
            )

    def test_catch_all_not_last_raises(self):
        with pytest.raises(ValueError, match="must be the last"):
            ThresholdConfig.from_dict(
                {"levels": [
                    {"value": 0.70, "label": "A"},
                    {"label": "Caught"},
                    {"value": 0.50, "label": "B"},
                ]}, True, "test",
            )


# ── Validation: ordering ─────────────────────────────────────────────────────

class TestValidationOrdering:
    def test_non_descending_higher_is_better_raises(self):
        with pytest.raises(ValueError, match="strictly descending"):
            ThresholdConfig.from_dict(
                {"levels": [
                    {"value": 0.70, "label": "A"},
                    {"value": 0.85, "label": "B"},
                    {"label": "C"},
                ]}, True, "test",
            )

    def test_non_ascending_lower_is_better_raises(self):
        with pytest.raises(ValueError, match="strictly ascending"):
            ThresholdConfig.from_dict(
                {"levels": [
                    {"value": 0.40, "label": "A"},
                    {"value": 0.20, "label": "B"},
                    {"label": "C"},
                ]}, False, "test",
            )

    def test_equal_consecutive_values_raises(self):
        with pytest.raises(ValueError):
            ThresholdConfig.from_dict(
                {"levels": [
                    {"value": 0.50, "label": "A"},
                    {"value": 0.50, "label": "B"},
                    {"label": "C"},
                ]}, True, "test",
            )


# ── Valid configs pass ───────────────────────────────────────────────────────

class TestValidConfigs:
    def test_dci_passes(self):
        ThresholdConfig.from_dict(DCI_DATA, True, "DCI")

    def test_nis_passes(self):
        ThresholdConfig.from_dict(NIS_DATA, False, "NIS")

    def test_single_threshold_passes(self):
        ThresholdConfig.from_dict(
            {"levels": [
                {"value": 0.50, "label": "Above"},
                {"label": "Below"},
            ]}, True, "single",
        )
