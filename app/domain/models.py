from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Citation:
    short_label: str
    title: str
    url: str
    note: str = ""


@dataclass(frozen=True)
class ValidatedRange:
    min_weeks: float
    max_weeks: float

    def contains(self, gestational_age_weeks: float) -> bool:
        return self.min_weeks <= gestational_age_weeks <= self.max_weeks

    @property
    def label(self) -> str:
        return f"{self.min_weeks:.1f}-{self.max_weeks:.1f} weeks"


@dataclass(frozen=True)
class InputField:
    field_name: str
    parameter_id: str
    label: str
    group: str
    unit: str
    help_text: str = ""


@dataclass(frozen=True)
class ParameterDefinition:
    parameter_id: str
    label: str
    unit: str
    group: str
    citation: Citation
    validated_range: ValidatedRange
    model_name: str


@dataclass(frozen=True)
class ComputedMeasurement:
    field_name: str
    parameter_id: str
    display_label: str
    group: str
    unit: str
    value: float
    mean: float
    sd: float
    expected_low: float
    expected_high: float
    z_score: float
    percentile: float
    interpretation: str
    tone: str
    extrapolated: bool
    citation: Citation
    validated_range: ValidatedRange


@dataclass(frozen=True)
class OverviewMetric:
    label: str
    value: str
    caption: str
    tone: str = "neutral"


@dataclass(frozen=True)
class Highlight:
    title: str
    body: str
    tone: str = "neutral"


@dataclass(frozen=True)
class AdvisoryItem:
    title: str
    body: str
    tone: str = "neutral"


@dataclass(frozen=True)
class AdvisoryPanel:
    title: str
    summary: str
    tone: str
    items: list[AdvisoryItem]
    citations: list[Citation]


@dataclass(frozen=True)
class ReviewStatus:
    title: str
    body: str
    tone: str


@dataclass(frozen=True)
class EvidenceHit:
    title: str
    source_label: str
    url: str
    summary: str
    matched_terms: list[str]
    relevance_score: int


@dataclass(frozen=True)
class DifferentialCard:
    card_id: str
    priority: int
    title: str
    trigger_summary: str
    clinical_summary: str
    diagnoses: list[str]
    likelihood_ranges: list[str]
    next_steps: list[str]
    limitations: list[str]
    citations: list[Citation]


@dataclass(frozen=True)
class CalculationBundle:
    gestational_age_weeks: float
    gestational_weeks: int
    gestational_days: int
    results: list[ComputedMeasurement]
    review_status: ReviewStatus
    overview_metrics: list[OverviewMetric]
    highlights: list[Highlight]
    advisory_panels: list[AdvisoryPanel]
    evidence_hits: list[EvidenceHit]
    counseling_note_text: str
    differential_cards: list[DifferentialCard]
    report_text: str
    warnings: list[str]

    @property
    def gestational_age_label(self) -> str:
        return f"{self.gestational_weeks}w {self.gestational_days}d"
