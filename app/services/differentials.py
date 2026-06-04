from __future__ import annotations

from app.domain.models import Citation, ComputedMeasurement, DifferentialCard


def _result_map(results: list[ComputedMeasurement]) -> dict[str, ComputedMeasurement]:
    return {result.field_name: result for result in results}


def _sort_cards(cards: list[DifferentialCard]) -> list[DifferentialCard]:
    return sorted(cards, key=lambda card: card.priority)


def build_differential_cards(results: list[ComputedMeasurement]) -> list[DifferentialCard]:
    by_field = _result_map(results)
    cards: list[DifferentialCard] = []

    atrial_values = [
        result.value
        for key in ("atrial_left", "atrial_right")
        if (result := by_field.get(key)) is not None
    ]
    if atrial_values:
        max_atrial = max(atrial_values)
        if 10 <= max_atrial < 13:
            cards.append(
                DifferentialCard(
                    card_id="mild_ventriculomegaly",
                    priority=10,
                    title="Most likely flagged pattern: mild ventriculomegaly",
                    trigger_summary="Maximum atrial diameter is between 10 mm and 12.9 mm.",
                    clinical_summary="This measurement pattern meets the standard threshold for mild ventriculomegaly and often has a favorable outcome when truly isolated after complete imaging, genetic, and infectious evaluation.",
                    diagnoses=[
                        "Isolated / idiopathic mild ventriculomegaly",
                        "Associated CNS anomaly including corpus callosum abnormality",
                        "Chromosomal or monogenic disorder",
                        "Congenital infection such as CMV",
                    ],
                    likelihood_ranges=[
                        "If truly isolated, SMFM reports a greater than 90% likelihood of normal neurodevelopment.",
                        "A systematic review estimated neurological abnormality around 12-14% for isolated mild-to-moderate ventriculomegaly after normal chromosome and infection evaluation.",
                        "This app does not estimate patient-specific cause probabilities from biometry alone.",
                    ],
                    next_steps=[
                        "Recommend detailed neurosonography and fetal MRI review for associated findings.",
                        "Offer chromosomal microarray and infection screening per SMFM guidance.",
                        "Recommend interval follow-up to assess stability or progression.",
                    ],
                    limitations=[
                        "Outcome data apply to apparently isolated cases after a complete workup.",
                        "Biometry alone cannot determine whether ventriculomegaly is isolated or secondary.",
                    ],
                    citations=[
                        Citation(
                            short_label="SMFM 2018",
                            title="Society for Maternal-Fetal Medicine Consult Series #45: Mild fetal ventriculomegaly: diagnosis, evaluation, and management.",
                            url="https://publications.smfm.org/publications/256-society-for-maternal-fetal-medicine-consult-series-45/",
                        ),
                        Citation(
                            short_label="Melchiorre 2009",
                            title="Prognosis of isolated mild to moderate fetal cerebral ventriculomegaly: a systematic review.",
                            url="https://pubmed.ncbi.nlm.nih.gov/20298149/",
                        ),
                    ],
                )
            )
        elif 13 <= max_atrial < 15:
            cards.append(
                DifferentialCard(
                    card_id="moderate_ventriculomegaly",
                    priority=9,
                    title="Most likely flagged pattern: moderate ventriculomegaly",
                    trigger_summary="Maximum atrial diameter is between 13 mm and 14.9 mm.",
                    clinical_summary="This falls in the moderate ventriculomegaly range, where the likelihood of associated pathology and neurodevelopmental risk is higher than in the 10-12 mm group.",
                    diagnoses=[
                        "Moderate ventriculomegaly with possible associated CNS anomaly",
                        "Aqueductal stenosis or obstructive hydrocephalus",
                        "Chromosomal or monogenic disorder",
                        "Congenital infection",
                    ],
                    likelihood_ranges=[
                        "If truly isolated, SMFM reports a 75-93% likelihood of normal neurodevelopment in the 13-15 mm group.",
                        "A systematic review estimated neurological abnormality around 12-14% for isolated mild-to-moderate ventriculomegaly after normal chromosome and infection evaluation.",
                        "This app does not estimate patient-specific cause probabilities from biometry alone.",
                    ],
                    next_steps=[
                        "Recommend detailed fetal MRI and targeted neurosonography.",
                        "Offer chromosomal microarray and infection screening.",
                        "Recommend follow-up imaging to look for progression or additional findings.",
                    ],
                    limitations=[
                        "Association and outcome ranges come from apparently isolated cohorts and may not apply once additional anomalies are present.",
                        "Degree of dilation alone does not identify the underlying cause.",
                    ],
                    citations=[
                        Citation(
                            short_label="SMFM 2018",
                            title="Society for Maternal-Fetal Medicine Consult Series #45: Mild fetal ventriculomegaly: diagnosis, evaluation, and management.",
                            url="https://publications.smfm.org/publications/256-society-for-maternal-fetal-medicine-consult-series-45/",
                        ),
                        Citation(
                            short_label="Melchiorre 2009",
                            title="Prognosis of isolated mild to moderate fetal cerebral ventriculomegaly: a systematic review.",
                            url="https://pubmed.ncbi.nlm.nih.gov/20298149/",
                        ),
                    ],
                )
            )
        if max_atrial >= 15:
            cards.append(
                DifferentialCard(
                    card_id="severe_ventriculomegaly",
                    priority=1,
                    title="Most likely flagged pattern: severe ventriculomegaly",
                    trigger_summary="Maximum atrial diameter is 15 mm or greater.",
                    clinical_summary="This meets the severe ventriculomegaly threshold and usually warrants broad structural, genetic, infectious, and multidisciplinary evaluation.",
                    diagnoses=[
                        "Obstructive hydrocephalus including aqueductal stenosis",
                        "Associated CNS malformation",
                        "Chromosomal or monogenic disorder",
                        "Congenital infection",
                    ],
                    likelihood_ranges=[
                        "A recent systematic review found normal neurodevelopment in about 42% of apparently isolated severe cases continued in pregnancy.",
                        "The same literature shows substantially worse outcomes than in mild or moderate ventriculomegaly, but exact prognosis depends heavily on associated findings and postnatal course.",
                        "This app does not estimate patient-specific cause probabilities from biometry alone.",
                    ],
                    next_steps=[
                        "Recommend detailed fetal MRI and neurosonography.",
                        "Offer chromosomal microarray and infectious workup.",
                        "Recommend multidisciplinary fetal neurology and neonatology review.",
                    ],
                    limitations=[
                        "Published percentages are cohort-level estimates, not individualized predictions.",
                        "Severity alone does not distinguish primary hydrocephalus from secondary or syndromic causes.",
                    ],
                    citations=[
                        Citation(
                            short_label="Carta 2018",
                            title="Outcome of fetuses with prenatal diagnosis of isolated severe bilateral ventriculomegaly: A systematic review and meta-analysis.",
                            url="https://openaccess.sgul.ac.uk/id/eprint/109965/",
                        ),
                        Citation(
                            short_label="Ali 2024",
                            title="Perinatal and neurodevelopmental outcomes of fetal isolated ventriculomegaly: a systematic review and meta-analysis.",
                            url="https://tp.amegroups.org/article/view/123875/html",
                        ),
                    ],
                )
            )

    left = by_field.get("atrial_left")
    right = by_field.get("atrial_right")
    if left is not None and right is not None and abs(left.value - right.value) > 2:
        cards.append(
            DifferentialCard(
                card_id="ventricular_asymmetry",
                priority=20,
                title="Ventricular asymmetry pattern",
                trigger_summary="Left and right atrial diameters differ by more than 2 mm.",
                clinical_summary="Asymmetry may be a benign variant, but it can also precede ventriculomegaly or accompany other CNS abnormalities.",
                diagnoses=[
                    "Isolated / benign asymmetry",
                    "Early or evolving ventriculomegaly",
                    "Associated CNS anomaly",
                    "Genetic or infectious contributor",
                ],
                likelihood_ranges=[
                    "Robust pooled percentages for cause are not available from the current source set.",
                    "The app therefore treats asymmetry as a review trigger rather than a probabilistic diagnosis.",
                ],
                next_steps=[
                    "Recommend detailed neurosonography and MRI review for associated anomalies.",
                    "Consider interval follow-up to assess progression.",
                ],
                limitations=[
                    "Published definitions and outcome estimates vary considerably.",
                    "This trigger does not distinguish benign asymmetry from early pathology.",
                ],
                citations=[
                    Citation(
                        short_label="Barzilay 2017",
                        title="Fetal Brain Anomalies Associated with Ventriculomegaly or Asymmetry: An MRI-Based Study.",
                        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC7963819/",
                    ),
                    Citation(
                        short_label="Meyer 2018",
                        title="Neurodevelopmental outcome of fetal isolated ventricular asymmetry without dilation.",
                        url="https://obgyn.onlinelibrary.wiley.com/doi/full/10.1002/uog.19065",
                    ),
                ],
            )
        )

    if (tcd := by_field.get("tcd")) is not None and tcd.percentile < 5:
        cards.append(
            DifferentialCard(
                card_id="small_tcd",
                priority=30,
                title="Small cerebellar size pattern",
                trigger_summary="Transverse cerebellar diameter is below the 5th percentile for gestational age.",
                clinical_summary="A low TCD raises concern for cerebellar hypoplasia or a broader posterior-fossa process, but the differential remains wide without qualitative imaging review.",
                diagnoses=[
                    "Cerebellar hypoplasia",
                    "Posterior-fossa malformation",
                    "Chromosomal or monogenic disorder",
                    "Congenital infection",
                ],
                likelihood_ranges=[
                    "The current literature supports a broad differential but does not provide stable cause percentages from biometry alone.",
                    "This app uses low TCD as a trigger for focused posterior-fossa review rather than an etiologic probability estimate.",
                ],
                next_steps=[
                    "Recommend detailed posterior-fossa review on MRI.",
                    "Consider genetic counseling, chromosomal microarray, and infection screening.",
                ],
                limitations=[
                    "A low TCD is not specific to a single diagnosis.",
                    "Associated findings strongly influence interpretation.",
                ],
                citations=[
                    Citation(
                        short_label="Aldinger 2016",
                        title="The genetics of cerebellar malformations.",
                        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5035570/",
                    ),
                    Citation(
                        short_label="Manganaro 2021",
                        title="Biometric assessments of the posterior fossa by fetal MRI: A systematic review.",
                        url="https://pubmed.ncbi.nlm.nih.gov/33251640/",
                    ),
                ],
            )
        )

    vermian_results = [by_field.get("vermian_height"), by_field.get("vermian_width")]
    low_vermis = [result for result in vermian_results if result is not None and result.percentile < 5]
    if low_vermis:
        cards.append(
            DifferentialCard(
                card_id="small_vermis",
                priority=31,
                title="Small vermian size pattern",
                trigger_summary="At least one vermian dimension is below the 5th percentile.",
                clinical_summary="Small vermian measurements raise concern for vermian hypoplasia or a Dandy-Walker spectrum abnormality, although the final interpretation depends strongly on qualitative imaging findings.",
                diagnoses=[
                    "Isolated vermian hypoplasia",
                    "Dandy-Walker spectrum",
                    "Blake pouch cyst with apparent vermian distortion",
                    "Chromosomal or genetic syndrome",
                ],
                likelihood_ranges=[
                    "Systematic review data support frequent associated anomalies across posterior-fossa malformations, but the current numeric dataset does not support stable patient-specific percentages.",
                    "This app therefore frames small vermian biometry as a focused review trigger rather than a numeric diagnosis probability.",
                ],
                next_steps=[
                    "Recommend multiplanar review of vermian morphology and posterior-fossa anatomy.",
                    "Consider genetic counseling and targeted infectious workup when clinically indicated.",
                ],
                limitations=[
                    "Biometry alone cannot reliably separate all posterior-fossa entities.",
                    "Angular and qualitative findings remain important and are not yet implemented in this version.",
                ],
                citations=[
                    Citation(
                        short_label="D'Antonio 2016",
                        title="Systematic review and meta-analysis of isolated posterior fossa malformations on prenatal ultrasound imaging (part 1): nomenclature, diagnostic accuracy and associated anomalies.",
                        url="https://pubmed.ncbi.nlm.nih.gov/25970099/",
                    ),
                    Citation(
                        short_label="Poretti 2014",
                        title="Cerebellar hypoplasia: differential diagnosis and diagnostic approach.",
                        url="https://pubmed.ncbi.nlm.nih.gov/24839100/",
                    ),
                ],
            )
        )

    if (callosum := by_field.get("corpus_callosum_length")) is not None and callosum.percentile < 5:
        cards.append(
            DifferentialCard(
                card_id="short_corpus_callosum",
                priority=40,
                title="Short corpus callosum pattern",
                trigger_summary="Corpus callosum length falls below the 5th percentile.",
                clinical_summary="A short corpus callosum can reflect callosal hypoplasia, dysgenesis, or broader developmental pathology, but length alone is not enough to diagnose agenesis or predict outcome.",
                diagnoses=[
                    "Callosal hypoplasia or dysgenesis",
                    "Agenesis spectrum abnormality",
                    "Genetic syndrome or chromosomal disorder",
                    "Associated CNS malformation",
                ],
                likelihood_ranges=[
                    "Outcome percentages published for isolated agenesis of the corpus callosum do not transfer directly to an isolated short-length measurement.",
                    "This app therefore avoids assigning a numeric diagnosis probability from callosal length alone.",
                ],
                next_steps=[
                    "Recommend careful midsagittal review for associated commissural abnormalities.",
                    "Consider chromosomal microarray and additional genetic workup if the morphology is abnormal.",
                ],
                limitations=[
                    "Length alone cannot determine full callosal morphology.",
                    "Non-visualization and rostrum assessment remain deferred in this numeric-only version.",
                ],
                citations=[
                    Citation(
                        short_label="Santo 2012",
                        title="Counseling in fetal medicine: agenesis of the corpus callosum.",
                        url="https://isuog.org/static/uploaded/2d4519f5-90f4-4065-b8581c23842f42d5.pdf",
                    ),
                    Citation(
                        short_label="Harreld 2011",
                        title="Corpus callosal biometry in fetal magnetic resonance imaging.",
                        url="https://pubmed.ncbi.nlm.nih.gov/21853265/",
                    ),
                ],
            )
        )

    return _sort_cards(cards)
