from app.services.calculator import build_case_presets, build_reference_case, calculate_bundle, gestational_age_to_float
from app.services.registry import load_registry


def test_gestational_age_to_float() -> None:
    assert gestational_age_to_float(24, 3) == 24 + (3 / 7)


def test_kyriakopoulou_skull_bpd_mean_matches_formula() -> None:
    registry = load_registry()
    model = registry.models["skull_bpd"]
    mean, sd = model.mean_sd(24.0)
    assert round(mean, 5) == 60.32808
    assert round(sd, 5) == 2.98227


def test_mean_measurement_returns_near_50th_percentile() -> None:
    bundle = calculate_bundle(24, 0, {"skull_bpd": 60.32808})
    result = bundle.results[0]
    assert abs(result.percentile - 50.0) < 0.01
    assert result.interpretation == "Within expected range"


def test_corpus_callosum_curve_is_usable() -> None:
    registry = load_registry()
    model = registry.models["corpus_callosum_length"]
    mean, sd = model.mean_sd(28.0)
    assert abs(mean - 34.8) < 0.5
    assert sd > 0


def test_mild_ventriculomegaly_card_triggers() -> None:
    bundle = calculate_bundle(24, 0, {"atrial_left": 11.2})
    card_ids = [card.card_id for card in bundle.differential_cards]
    assert "mild_ventriculomegaly" in card_ids
    assert bundle.review_status.title == "Focused counseling and workup recommended"
    assert any(panel.title == "Parent counseling snapshot" for panel in bundle.advisory_panels)
    assert any(hit.source_label == "SMFM 2018" for hit in bundle.evidence_hits)
    assert "mild ventriculomegaly" in bundle.counseling_note_text.lower()


def test_reference_case_prefills_measurements() -> None:
    reference_case = build_reference_case(24, 0)
    assert reference_case["form_values"]["gestational_weeks"] == "24"
    assert reference_case["form_values"]["gestational_days"] == "0"
    assert "skull_bpd" in reference_case["form_values"]


def test_case_presets_include_common_workflow_examples() -> None:
    presets = build_case_presets(24, 0)
    titles = {preset["title"] for preset in presets}
    assert {"Reference", "Mild VM", "Severe VM", "Small PF"} <= titles


def test_asymmetry_card_triggers() -> None:
    bundle = calculate_bundle(24, 0, {"atrial_left": 7.0, "atrial_right": 10.0})
    card_ids = [card.card_id for card in bundle.differential_cards]
    assert "ventricular_asymmetry" in card_ids


def test_normal_case_builds_reassuring_workflow_panels() -> None:
    bundle = calculate_bundle(24, 0, {"skull_bpd": 60.32808})
    assert bundle.review_status.tone == "success"
    assert any(panel.title == "Suggested next measurements" for panel in bundle.advisory_panels)
    assert "within expected range" in bundle.counseling_note_text.lower()
