"""Regression tests for the Risk-Fusion missing-component semantics (FIX 1).

The unified risk score is a weighted average of *available* components:

    Fused = sum(w_i * v_i) / sum(w_i)   over components where v_i is not None

Regression guarantees:
- When NO component is available -> (None, None) (never fabricates a score).
- When DCI (a longitudinal index) is unavailable (None), the remaining
  components are renormalised proportionally so the available weights still
  sum to 1, WITHOUT substituting a default value for DCI.
- When every component is available, the result matches the configured-weight
  formula.
- The score is always clamped to [0, 1].
- Configured weights in the JSON are never mutated.
"""

import pytest

from backend.services.risk_fusion_service import RiskFusionService

# Configured weights (from DietRiskNet_RiskFusion_Config.json).
W = {
    "DCI": 0.25,
    "NIS": 0.25,
    "Diabetes": 0.2,
    "Obesity": 0.15,
    "Hypertension": 0.1,
    "Deficiency": 0.05,
}


@pytest.fixture(scope="module")
def fusion():
    return RiskFusionService()


def test_all_components_available_matches_formula(fusion):
    dci, nis = 0.8, 0.3
    dia, ob, hyp, def_ = 0.2, 0.3, 0.1, 0.2
    score, level = fusion.fuse(dci, nis, dia, ob, hyp, def_)
    expected = (
        W["DCI"] * (1.0 - dci)
        + W["NIS"] * nis
        + W["Diabetes"] * dia
        + W["Obesity"] * ob
        + W["Hypertension"] * hyp
        + W["Deficiency"] * def_
    )
    assert score == pytest.approx(expected, abs=1e-9)
    assert 0.0 <= score <= 1.0
    assert level in {"Low", "Moderate", "High", "Critical"}


def test_no_components_returns_none(fusion):
    score, level = fusion.fuse(None, None, None, None, None, None)
    assert score is None
    assert level is None


def test_missing_dci_renormalises_without_fabricating(fusion):
    """DCI=None must not be silently replaced; remaining weights renormalise."""
    nis, dia, ob, hyp, def_ = 0.3, 0.2, 0.3, 0.1, 0.2
    score, _ = fusion.fuse(None, nis, dia, ob, hyp, def_)

    avail_w = W["NIS"] + W["Diabetes"] + W["Obesity"] + W["Hypertension"] + W["Deficiency"]
    expected = (W["NIS"] * nis + W["Diabetes"] * dia + W["Obesity"] * ob
                + W["Hypertension"] * hyp + W["Deficiency"] * def_) / avail_w
    assert score == pytest.approx(expected, abs=1e-9)


def test_missing_dci_is_not_treated_as_perfect_health(fusion):
    """A missing DCI must not drag the fused score down as if consistency were 1.0."""
    high_risk = fusion.fuse(None, 0.9, 0.8, 0.8, 0.8, 0.8)
    # If DCI were fabricated as 1.0 (perfect health), the score would be lower.
    assert high_risk[0] is not None
    assert high_risk[0] > 0.7


def test_missing_nis_only(fusion):
    dci = 0.8
    dia, ob, hyp, def_ = 0.2, 0.3, 0.1, 0.2
    score, _ = fusion.fuse(dci, None, dia, ob, hyp, def_)
    avail_w = W["DCI"] + W["Diabetes"] + W["Obesity"] + W["Hypertension"] + W["Deficiency"]
    expected = (W["DCI"] * (1.0 - dci) + W["Diabetes"] * dia + W["Obesity"] * ob
                + W["Hypertension"] * hyp + W["Deficiency"] * def_) / avail_w
    assert score == pytest.approx(expected, abs=1e-9)


def test_score_clamped_to_unit_interval(fusion):
    score, level = fusion.fuse(1.0, 5.0, 1.5, 1.5, 1.5, 1.5)
    assert score <= 1.0
    assert level == "Critical"
    score_low, level_low = fusion.fuse(1.0, -2.0, -0.5, -0.5, -0.5, -0.5)
    assert score_low >= 0.0


def test_config_weights_unchanged(fusion):
    """The service must never mutate the loaded configured weights."""
    before = dict(fusion.config.get("weights", {}))
    fusion.fuse(None, 0.3, 0.2, 0.3, 0.1, 0.2)
    after = dict(fusion.config.get("weights", {}))
    assert before == after


def _fused_level(fusion, score):
    """Return only the severity level for a given fused score.

    Passing a single non-None component (NIS) drives the fused score exactly
    to that value: the missing real weights renormalise, so the NIS
    component's weight cancels. NIS has weight 0.25 = 1/4 (a power of two),
    so ``0.25 * score / 0.25 == score`` exactly in IEEE-754 floats — the
    at-boundary scores (0.25 / 0.50 / 0.75) land precisely on the thresholds.
    This exercises the REAL RiskFusionService.fuse() for a precise score
    without re-implementing the production classification algorithm.
    """
    _, level = fusion.fuse(None, score, None, None, None, None)
    return level


class TestRiskFusionSeverityBoundaries:
    """Verify the deployed severity labels at and just above each boundary.

    Canonical behavior (risk_fusion_service.py): score <= 0.25 Low;
    0.25 < score <= 0.50 Moderate; 0.50 < score <= 0.75 High; > 0.75 Critical.
    """

    def test_low_boundary(self, fusion):
        assert _fused_level(fusion, 0.25) == "Low"
        assert _fused_level(fusion, 0.2501) == "Moderate"

    def test_moderate_boundary(self, fusion):
        assert _fused_level(fusion, 0.50) == "Moderate"
        assert _fused_level(fusion, 0.5001) == "High"

    def test_high_boundary(self, fusion):
        assert _fused_level(fusion, 0.75) == "High"
        assert _fused_level(fusion, 0.7501) == "Critical"

    def test_representative_interior_values(self, fusion):
        assert _fused_level(fusion, 0.0) == "Low"
        assert _fused_level(fusion, 0.30) == "Moderate"
        assert _fused_level(fusion, 0.60) == "High"
        assert _fused_level(fusion, 0.90) == "Critical"
