from app.model import risk_band


def test_risk_band_thresholds():
    assert risk_band(0.05) == "low"
    assert risk_band(0.2) == "medium"
    assert risk_band(0.49) == "medium"
    assert risk_band(0.5) == "high"