from __future__ import annotations

from statistics import NormalDist

from app.domain.models import (
    AdvisoryItem,
    AdvisoryPanel,
    CalculationBundle,
    Citation,
    ComputedMeasurement,
    DifferentialCard,
    Highlight,
    OverviewMetric,
    ReviewStatus,
)
from app.services.differentials import build_differential_cards
from app.services.evidence import retrieve_evidence
from app.services.registry import load_registry
from app.services.reporting import build_report_text


STANDARD_NORMAL = NormalDist()
EXPECTED_RANGE_Z = 1.645
BORDERLINE_RANGE_Z = 1.282


def gestational_age_to_float(weeks: int, days: int) -> float:
    return weeks + (days / 7.0)


def build_reference_case(gestational_weeks: int = 24, gestational_days: int = 0) -> dict[str, object]:
    form_values = _mean_form_values(gestational_weeks, gestational_days)
    return {
        "title": f"{gestational_weeks}w {gestational_days}d reference case",
        "description": "Loads source-derived mean values that should land near the 50th percentile for every currently implemented parameter.",
        "form_values": form_values,
    }


def _mean_form_values(gestational_weeks: int, gestational_days: int) -> dict[str, str]:
    gestational_age_weeks = gestational_age_to_float(gestational_weeks, gestational_days)
    registry = load_registry()
    form_values: dict[str, str] = {
        "gestational_weeks": str(gestational_weeks),
        "gestational_days": str(gestational_days),
    }
    for field in registry.input_fields:
        mean, _sd = registry.models[field.parameter_id].mean_sd(gestational_age_weeks)
        form_values[field.field_name] = f"{mean:.2f}"
    return form_values


def build_case_presets(gestational_weeks: int = 24, gestational_days: int = 0) -> list[dict[str, object]]:
    baseline = _mean_form_values(gestational_weeks, gestational_days)

    def with_overrides(**overrides: str) -> dict[str, str]:
        values = dict(baseline)
        values.update(overrides)
        return values

    return [
        {
            "title": "Reference",
            "description": "All implemented measurements near the source-derived mean.",
            "tone": "success",
            "form_values": baseline,
        },
        {
            "title": "Mild VM",
            "description": "Atrial diameter in the 10-12.9 mm range with asymmetry.",
            "tone": "warning",
            "form_values": with_overrides(atrial_left="11.20"),
        },
        {
            "title": "Severe VM",
            "description": "Atrial diameter at or above 15 mm for high-priority workup testing.",
            "tone": "danger",
            "form_values": with_overrides(atrial_left="15.50", atrial_right="15.20"),
        },
        {
            "title": "Small PF",
            "description": "Posterior-fossa measurements below expected range.",
            "tone": "warning",
            "form_values": with_overrides(tcd="20.00", vermian_height="9.00", vermian_width="5.80"),
        },
    ]


def _measurement_tone(z_score: float) -> str:
    if z_score <= -EXPECTED_RANGE_Z:
        return "low"
    if z_score >= EXPECTED_RANGE_Z:
        return "high"
    if z_score <= -BORDERLINE_RANGE_Z or z_score >= BORDERLINE_RANGE_Z:
        return "borderline"
    return "normal"


def _interpretation_label(z_score: float) -> str:
    tone = _measurement_tone(z_score)
    if tone == "low":
        return "Below expected range"
    if tone == "high":
        return "Above expected range"
    if tone == "borderline":
        return "Borderline range"
    return "Within expected range"


def _build_overview_metrics(results: list[ComputedMeasurement], differential_count: int) -> list[OverviewMetric]:
    measurement_count = len(results)
    outside_expected = sum(
        1 for result in results if result.percentile < 5.0 or result.percentile > 95.0
    )
    extrapolated_count = sum(1 for result in results if result.extrapolated)

    return [
        OverviewMetric(
            label="Measurements entered",
            value=str(measurement_count),
            caption="Numeric values interpreted in this pass.",
            tone="accent",
        ),
        OverviewMetric(
            label="Outside 5th-95th",
            value=str(outside_expected),
            caption="Values needing closer review." if outside_expected else "No numeric outliers detected.",
            tone="danger" if outside_expected else "success",
        ),
        OverviewMetric(
            label="Concern cards",
            value=str(differential_count),
            caption="Threshold-based advisory prompts." if differential_count else "No rule-based concern cards triggered.",
            tone="warning" if differential_count else "success",
        ),
        OverviewMetric(
            label="Validated range",
            value=f"{measurement_count - extrapolated_count}/{measurement_count}",
            caption=(
                f"{extrapolated_count} extrapolated value{'s' if extrapolated_count != 1 else ''}."
                if extrapolated_count
                else "All results are within each source's stated gestational window."
            ),
            tone="warning" if extrapolated_count else "success",
        ),
    ]


def _build_highlights(
    gestational_weeks: int,
    gestational_days: int,
    results: list[ComputedMeasurement],
    differential_cards: list[DifferentialCard],
) -> list[Highlight]:
    gestational_age_label = f"{gestational_weeks}w {gestational_days}d"
    highlights: list[Highlight] = []

    if differential_cards:
        lead_card = differential_cards[0]
        highlights.append(
            Highlight(
                title=lead_card.title,
                body=(
                    f"{len(differential_cards)} advisory concern card{'s' if len(differential_cards) != 1 else ''} "
                    "were generated from the currently entered thresholds. The first card is shown as the most likely flagged pattern, not as a definitive diagnosis."
                ),
                tone="warning",
            )
        )

    notable_results = [
        result
        for result in results
        if result.tone != "normal" or result.extrapolated
    ]
    notable_results.sort(
        key=lambda result: (abs(result.z_score), result.extrapolated),
        reverse=True,
    )

    for result in notable_results[:3]:
        extrapolated_note = (
            f" Source validated range: {result.validated_range.label}."
            if result.extrapolated
            else ""
        )
        highlights.append(
            Highlight(
                title=result.display_label,
                body=(
                    f"{result.value:.2f} {result.unit} is {result.interpretation.lower()} at {gestational_age_label} "
                    f"(expected 5th-95th percentile range {result.expected_low:.2f}-{result.expected_high:.2f} {result.unit}; "
                    f"observed {result.percentile:.1f}th percentile).{extrapolated_note}"
                ),
                tone="danger" if result.tone in {"low", "high"} else "warning",
            )
        )

    if not highlights:
        highlights.append(
            Highlight(
                title="Overall impression",
                body=(
                    f"All {len(results)} entered measurements fall within the expected 5th-95th percentile range "
                    f"for the currently implemented source models at {gestational_age_label}."
                ),
                tone="success",
            )
        )

    return highlights


def _build_warnings(results: list[ComputedMeasurement]) -> list[str]:
    warnings: list[str] = []
    extrapolated_count = sum(1 for result in results if result.extrapolated)
    if extrapolated_count:
        warnings.append(
            f"{extrapolated_count} value{'s are' if extrapolated_count != 1 else ' is'} outside the validated gestational-age range of the published source and shown as extrapolated."
        )
    if any(abs(result.z_score) >= 3.0 for result in results):
        warnings.append(
            "At least one measurement is more than 3 standard deviations from the mean. Consider confirming plane selection and caliper placement."
        )
    return warnings


def _guideline_citations() -> dict[str, Citation]:
    return {
        "isuog_targeted_neuro": Citation(
            short_label="ISUOG CNS 2021",
            title="ISUOG Practice Guidelines (updated): sonographic examination of the fetal central nervous system. Part 2: performance of targeted neurosonography.",
            url="https://www.isuog.org/static/b91bae06-731b-4a2d-8bbcbb2f0d886af4/ISUOG-Practice-Guidelines-CNS-part-2-targeted-neurosonography.pdf",
        ),
        "isuog_vm_leaflet": Citation(
            short_label="ISUOG VM Leaflet",
            title="ISUOG Patient Information Series: Ventriculomegaly.",
            url="https://www.isuog.org/resource/ventriculomegaly--isuog-patient-information-series-draft-ra-25-09_final-pdf.html",
        ),
        "isuog_acc_leaflet": Citation(
            short_label="ISUOG ACC Leaflet",
            title="ISUOG Patient Information Series: Agenesis of the corpus callosum.",
            url="https://www.isuog.org/clinical-resources/patient-information-series/patient-information-pregnancy-conditions/brain/agenesis-of-the-corpus-callosum.html",
        ),
        "isuog_dw_leaflet": Citation(
            short_label="ISUOG Dandy-Walker",
            title="ISUOG Patient Information Series: Dandy Walker Complex.",
            url="https://www.isuog.org/clinical-resources/patient-information-series/patient-information-pregnancy-conditions/brain/dandy-walker-complex.html",
        ),
        "smfm_vm": Citation(
            short_label="SMFM 2018",
            title="Society for Maternal-Fetal Medicine Consult Series #45: Mild fetal ventriculomegaly: diagnosis, evaluation, and management.",
            url="https://publications.smfm.org/publications/256-society-for-maternal-fetal-medicine-consult-series-45/",
        ),
    }


def _review_status(results: list[ComputedMeasurement], differential_cards: list[DifferentialCard]) -> ReviewStatus:
    if any(card.card_id == "severe_ventriculomegaly" for card in differential_cards):
        return ReviewStatus(
            title="High-priority anomaly workup",
            body="Quantitative findings support a high-priority fetal CNS review with multidisciplinary counseling and broad etiologic evaluation.",
            tone="danger",
        )
    if differential_cards:
        return ReviewStatus(
            title="Focused counseling and workup recommended",
            body="At least one threshold-based pattern was flagged. Use the workflow panels below to guide image review, family counseling, and follow-up planning.",
            tone="warning",
        )
    if any(result.extrapolated or abs(result.z_score) >= 2.0 for result in results):
        return ReviewStatus(
            title="Focused measurement confirmation",
            body="The measurements do not trigger a major pattern, but at least one value deserves a closer plane and caliper check before finalizing the impression.",
            tone="warning",
        )
    return ReviewStatus(
        title="Reassuring quantitative review",
        body="The entered numeric measurements are within expected range for the current source set. Final counseling still depends on qualitative MRI findings and any associated anomalies.",
        tone="success",
    )


def _build_suggested_measurements_panel(results: list[ComputedMeasurement]) -> AdvisoryPanel:
    citations = _guideline_citations()
    entered_fields = {result.field_name for result in results}
    items: list[AdvisoryItem] = []

    if "atrial_left" in entered_fields and "atrial_right" not in entered_fields:
        items.append(
            AdvisoryItem(
                title="Add the contralateral atrial measurement",
                body="Ventricular enlargement may be unilateral, so both atria are worth documenting when one side is abnormal or borderline.",
                tone="warning",
            )
        )
    if "atrial_right" in entered_fields and "atrial_left" not in entered_fields:
        items.append(
            AdvisoryItem(
                title="Add the opposite atrial measurement",
                body="A paired atrial measurement helps separate isolated asymmetry from bilateral ventriculomegaly.",
                tone="warning",
            )
        )
    if (
        {"skull_bpd", "brain_bpd"} & entered_fields
        and not {"skull_ofd", "brain_ofd"} <= entered_fields
    ):
        items.append(
            AdvisoryItem(
                title="Complete the orthogonal skull and brain diameters",
                body="Adding OFD and fronto-occipital measurements improves confidence in global head-growth and brain-growth interpretation.",
                tone="accent",
            )
        )
    if {"tcd", "vermian_height", "vermian_width"} & entered_fields and not {"tcd", "vermian_height", "vermian_width"} <= entered_fields:
        items.append(
            AdvisoryItem(
                title="Complete the posterior-fossa trio",
                body="A combined TCD and vermian set is more useful than a single posterior-fossa number when posterior structures look small or atypical.",
                tone="accent",
            )
        )
    if {"atrial_left", "atrial_right"} & entered_fields and "corpus_callosum_length" not in entered_fields:
        items.append(
            AdvisoryItem(
                title="Add corpus callosum length if available",
                body="Callosal review is commonly part of the ventriculomegaly workup because callosal anomalies can change prognosis and counseling.",
                tone="warning",
            )
        )

    if not items:
        items.append(
            AdvisoryItem(
                title="Coverage is strong for the implemented numeric set",
                body="No obvious high-yield missing measurement stands out within the currently supported parameters.",
                tone="success",
            )
        )

    return AdvisoryPanel(
        title="Suggested next measurements",
        summary="These prompts focus on the supported fields that usually add the most value to the current dataset.",
        tone="accent",
        items=items,
        citations=[citations["isuog_targeted_neuro"], citations["smfm_vm"]],
    )


def _build_questions_panel(results: list[ComputedMeasurement], differential_cards: list[DifferentialCard]) -> AdvisoryPanel:
    citations = _guideline_citations()
    by_field = {result.field_name: result for result in results}
    items: list[AdvisoryItem] = [
        AdvisoryItem(
            title="Is the pattern isolated?",
            body="Before finalizing prognosis, confirm whether the CNS finding remains isolated after detailed brain, spine, and extra-CNS review.",
            tone="warning" if differential_cards else "accent",
        ),
        AdvisoryItem(
            title="Is the cortical pattern appropriate for gestational age?",
            body="Targeted neurosonography guidance emphasizes gestational-age-appropriate sulcation and cortical assessment as part of second-line CNS review.",
            tone="accent",
        ),
        AdvisoryItem(
            title="Has progression or stability been documented?",
            body="Serial imaging can change counseling substantially, especially for ventriculomegaly and posterior-fossa patterns.",
            tone="accent",
        ),
    ]

    if "atrial_left" in by_field or "atrial_right" in by_field:
        items.extend(
            [
                AdvisoryItem(
                    title="Confirm unilateral vs bilateral ventricular involvement",
                    body="Both lateral ventricles should be assessed because asymmetry and bilateral enlargement carry different diagnostic implications.",
                    tone="warning",
                ),
                AdvisoryItem(
                    title="Review CSP, corpus callosum, third ventricle, spine, and fetal heart/anatomy",
                    body="These are high-yield associated assessments in ventriculomegaly workup and often drive family counseling more than the atrial size alone.",
                    tone="warning",
                ),
            ]
        )

    if "corpus_callosum_length" in by_field and by_field["corpus_callosum_length"].percentile < 5:
        items.append(
            AdvisoryItem(
                title="Directly inspect genu, body, splenium, CSP, and third ventricle",
                body="Short length alone is not diagnostic; qualitative midsagittal morphology and indirect callosal signs remain essential.",
                tone="warning",
            )
        )

    if any(field in by_field for field in ("tcd", "vermian_height", "vermian_width")):
        items.append(
            AdvisoryItem(
                title="Differentiate Blake pouch delay from broader posterior-fossa malformation",
                body="Posterior-fossa counseling depends on whether the pattern reflects a benign developmental delay or a vermian/cerebellar malformation with associated anomalies.",
                tone="warning" if any(card.card_id in {"small_tcd", "small_vermis"} for card in differential_cards) else "accent",
            )
        )

    return AdvisoryPanel(
        title="Questions before final impression",
        summary="These checks mirror what expert neurosonography guidance and counseling literature usually want answered before prognosis is discussed.",
        tone="warning" if differential_cards else "accent",
        items=items,
        citations=[citations["isuog_targeted_neuro"], citations["isuog_vm_leaflet"], citations["isuog_acc_leaflet"]],
    )


def _build_tests_panel(differential_cards: list[DifferentialCard]) -> AdvisoryPanel:
    citations = _guideline_citations()
    card_ids = {card.card_id for card in differential_cards}
    items: list[AdvisoryItem] = [
        AdvisoryItem(
            title="Detailed neurosonography or expert fetal CNS review",
            body="Use targeted multiplanar review to clarify whether the MRI biometrics correspond to an isolated variant or a broader malformation pattern.",
            tone="accent",
        )
    ]

    if card_ids & {"mild_ventriculomegaly", "moderate_ventriculomegaly", "severe_ventriculomegaly", "ventricular_asymmetry"}:
        items.extend(
            [
                AdvisoryItem(
                    title="Offer chromosomal microarray",
                    body="SMFM recommends diagnostic testing with microarray when ventriculomegaly is detected because prognosis depends strongly on the underlying cause.",
                    tone="warning",
                ),
                AdvisoryItem(
                    title="Discuss CMV and toxoplasmosis testing",
                    body="Infectious screening is commonly recommended even without a known exposure history when ventriculomegaly is present.",
                    tone="warning",
                ),
                AdvisoryItem(
                    title="Plan interval imaging",
                    body="Follow-up studies help determine whether ventricular size remains stable, improves, or progresses during pregnancy.",
                    tone="warning",
                ),
            ]
        )

    if card_ids & {"small_tcd", "small_vermis", "short_corpus_callosum"}:
        items.extend(
            [
                AdvisoryItem(
                    title="Consider genetics referral",
                    body="Posterior-fossa and callosal anomalies are often discussed with genetics because chromosomal and monogenic causes can change recurrence counseling.",
                    tone="warning",
                ),
                AdvisoryItem(
                    title="Use fetal MRI to refine morphology when needed",
                    body="MRI can help resolve posterior-fossa and callosal anatomy when targeted sonography or the current MRI question remains incomplete.",
                    tone="accent",
                ),
            ]
        )

    if card_ids & {"severe_ventriculomegaly", "small_tcd", "small_vermis", "short_corpus_callosum"}:
        items.append(
            AdvisoryItem(
                title="Prepare pediatric specialty follow-up",
                body="Pediatric neurology, neurosurgery, and delivery-site planning become more relevant as the chance of a complex anomaly pattern increases.",
                tone="warning",
            )
        )

    return AdvisoryPanel(
        title="Tests and referrals commonly discussed",
        summary="This is not a one-click order set; it is a radiologist-facing memory aid for the common next steps that often matter to families.",
        tone="warning" if differential_cards else "accent",
        items=items,
        citations=[
            citations["smfm_vm"],
            citations["isuog_vm_leaflet"],
            citations["isuog_acc_leaflet"],
            citations["isuog_dw_leaflet"],
        ],
    )


def _build_parent_snapshot_panel(differential_cards: list[DifferentialCard]) -> AdvisoryPanel:
    citations = _guideline_citations()
    card_ids = {card.card_id for card in differential_cards}
    items: list[AdvisoryItem] = [
        AdvisoryItem(
            title="Explain the measured structure in plain language",
            body="Parents usually understand counseling better when you first describe which brain structure looks different and whether the issue is size, symmetry, or morphology.",
            tone="accent",
        ),
        AdvisoryItem(
            title="Separate today's pattern flag from a final diagnosis",
            body="Use language such as 'the measurements raise concern for...' rather than presenting the calculator output as a confirmed diagnosis.",
            tone="warning" if differential_cards else "accent",
        ),
    ]

    if "mild_ventriculomegaly" in card_ids:
        items.append(
            AdvisoryItem(
                title="Mild ventriculomegaly counseling angle",
                body="If the workup remains isolated, counseling is generally favorable, but parents still need to hear that associated anomalies, infection, or genetic findings would change the outlook.",
                tone="success",
            )
        )
    if "moderate_ventriculomegaly" in card_ids:
        items.append(
            AdvisoryItem(
                title="Moderate ventriculomegaly counseling angle",
                body="Families can be told that isolated cases are often favorable, while also being warned that neurodevelopmental risk is higher than in the 10-12 mm group.",
                tone="warning",
            )
        )
    if "severe_ventriculomegaly" in card_ids:
        items.append(
            AdvisoryItem(
                title="Severe ventriculomegaly counseling angle",
                body="Counseling should emphasize uncertainty, the higher likelihood of underlying pathology, and the need for multidisciplinary follow-up rather than a single numeric prognosis.",
                tone="danger",
            )
        )
    if "short_corpus_callosum" in card_ids:
        items.append(
            AdvisoryItem(
                title="Callosal counseling angle",
                body="Length alone does not predict function. Parents generally need to hear that callosal outcome is broad and depends on full morphology, associated findings, and genetics.",
                tone="warning",
            )
        )
    if card_ids & {"small_tcd", "small_vermis"}:
        items.append(
            AdvisoryItem(
                title="Posterior-fossa counseling angle",
                body="Posterior-fossa prognosis depends on the exact entity. Some developmental-delay patterns can do very well, while cerebellar malformations and syndromic cases are more concerning.",
                tone="warning",
            )
        )

    if len(items) == 2:
        items.append(
            AdvisoryItem(
                title="Normal-range counseling angle",
                body="When all entered biometrics are within expected range, parents may still need to hear that this tool does not capture every qualitative brain finding seen on MRI.",
                tone="success",
            )
        )

    return AdvisoryPanel(
        title="Parent counseling snapshot",
        summary="These talking points are meant to help frame the discussion; they should be adapted to the full imaging context and the family's questions.",
        tone="warning" if differential_cards else "success",
        items=items,
        citations=[
            citations["smfm_vm"],
            citations["isuog_vm_leaflet"],
            citations["isuog_acc_leaflet"],
            citations["isuog_dw_leaflet"],
        ],
    )


def _build_advisory_panels(results: list[ComputedMeasurement], differential_cards: list[DifferentialCard]) -> list[AdvisoryPanel]:
    return [
        _build_suggested_measurements_panel(results),
        _build_questions_panel(results, differential_cards),
        _build_tests_panel(differential_cards),
        _build_parent_snapshot_panel(differential_cards),
    ]


def _build_counseling_note(
    gestational_weeks: int,
    gestational_days: int,
    review_status: ReviewStatus,
    differential_cards: list[DifferentialCard],
) -> str:
    lines = [
        f"Counseling frame for {gestational_weeks}w {gestational_days}d:",
        review_status.body,
    ]

    if differential_cards:
        lead_card = differential_cards[0]
        lines.append(
            f"The leading measurement-based pattern today is {lead_card.title.replace('Most likely flagged pattern: ', '')}."
        )
        if lead_card.likelihood_ranges:
            lines.append(f"Literature-based counseling point: {lead_card.likelihood_ranges[0]}")
        lines.append(
            "Parents should be told that prognosis and recurrence counseling depend most on whether the pattern is isolated and on the results of neurosonography, MRI review, genetic testing, and infectious evaluation."
        )
    else:
        lines.append(
            "All entered biometrics are within expected range for the implemented source set. Families can still be reminded that quantitative biometry does not replace full qualitative MRI interpretation."
        )

    lines.append(
        "Suggested discussion themes: what structure is affected, whether the finding appears isolated, what additional tests are being recommended, and what changes in management or follow-up would alter counseling."
    )
    return "\n".join(lines)


def _evidence_search_terms(
    results: list[ComputedMeasurement],
    differential_cards: list[DifferentialCard],
    advisory_panels: list[AdvisoryPanel],
) -> list[str]:
    terms = ["targeted neurosonography", "parent counseling"]
    terms.extend(card.card_id.replace("_", " ") for card in differential_cards)
    terms.extend(result.parameter_id.replace("_", " ") for result in results)
    terms.extend(result.group.lower() for result in results)
    terms.extend(item.title.lower() for panel in advisory_panels for item in panel.items)
    return terms


def calculate_bundle(
    gestational_weeks: int,
    gestational_days: int,
    measurements: dict[str, float],
) -> CalculationBundle:
    registry = load_registry()
    gestational_age_weeks = gestational_age_to_float(gestational_weeks, gestational_days)

    results: list[ComputedMeasurement] = []
    for field in registry.input_fields:
        if field.field_name not in measurements:
            continue
        definition = registry.parameters[field.parameter_id]
        model = registry.models[field.parameter_id]
        value = measurements[field.field_name]
        mean, sd = model.mean_sd(gestational_age_weeks)
        z_score = (value - mean) / sd
        percentile = STANDARD_NORMAL.cdf(z_score) * 100.0
        expected_low = mean - (EXPECTED_RANGE_Z * sd)
        expected_high = mean + (EXPECTED_RANGE_Z * sd)
        results.append(
            ComputedMeasurement(
                field_name=field.field_name,
                parameter_id=field.parameter_id,
                display_label=field.label,
                group=field.group,
                unit=field.unit,
                value=value,
                mean=mean,
                sd=sd,
                expected_low=expected_low,
                expected_high=expected_high,
                z_score=z_score,
                percentile=percentile,
                interpretation=_interpretation_label(z_score),
                tone=_measurement_tone(z_score),
                extrapolated=not definition.validated_range.contains(gestational_age_weeks),
                citation=definition.citation,
                validated_range=definition.validated_range,
            )
        )

    differential_cards = build_differential_cards(results)
    review_status = _review_status(results, differential_cards)
    overview_metrics = _build_overview_metrics(results, len(differential_cards))
    highlights = _build_highlights(
        gestational_weeks,
        gestational_days,
        results,
        differential_cards,
    )
    advisory_panels = _build_advisory_panels(results, differential_cards)
    evidence_hits = retrieve_evidence(
        _evidence_search_terms(results, differential_cards, advisory_panels)
    )
    bundle = CalculationBundle(
        gestational_age_weeks=gestational_age_weeks,
        gestational_weeks=gestational_weeks,
        gestational_days=gestational_days,
        results=results,
        review_status=review_status,
        overview_metrics=overview_metrics,
        highlights=highlights,
        advisory_panels=advisory_panels,
        evidence_hits=evidence_hits,
        counseling_note_text="",
        differential_cards=differential_cards,
        report_text="",
        warnings=_build_warnings(results),
    )
    return CalculationBundle(
        gestational_age_weeks=bundle.gestational_age_weeks,
        gestational_weeks=bundle.gestational_weeks,
        gestational_days=bundle.gestational_days,
        results=bundle.results,
        review_status=bundle.review_status,
        overview_metrics=bundle.overview_metrics,
        highlights=bundle.highlights,
        advisory_panels=bundle.advisory_panels,
        evidence_hits=bundle.evidence_hits,
        counseling_note_text=_build_counseling_note(
            bundle.gestational_weeks,
            bundle.gestational_days,
            bundle.review_status,
            bundle.differential_cards,
        ),
        differential_cards=bundle.differential_cards,
        report_text=build_report_text(bundle),
        warnings=bundle.warnings,
    )
