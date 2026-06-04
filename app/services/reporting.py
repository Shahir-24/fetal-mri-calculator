from __future__ import annotations

from app.domain.models import CalculationBundle


def _ordinal(value: float) -> str:
    rounded = int(round(value))
    if 10 <= rounded % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(rounded % 10, "th")
    return f"{rounded}{suffix}"


def build_report_text(bundle: CalculationBundle) -> str:
    lines = [f"Gestational age: {bundle.gestational_age_label}"]
    current_group = None
    for result in bundle.results:
        if result.group != current_group:
            lines.append("")
            lines.append(f"{result.group}:")
            current_group = result.group
        extrapolated = " [extrapolated]" if result.extrapolated else ""
        lines.append(
            f"{result.display_label}: {result.value:.2f} {result.unit} "
            f"(expected 5th-95th percentile {result.expected_low:.2f}-{result.expected_high:.2f} {result.unit}; "
            f"Z {result.z_score:+.2f}, {_ordinal(result.percentile)} percentile, {result.interpretation.lower()})"
            f"{extrapolated}"
        )
    if any(result.extrapolated for result in bundle.results):
        lines.append("")
        lines.append("Note: at least one value is outside the validated gestational-age range and is shown as extrapolated.")
    return "\n".join(lines)
