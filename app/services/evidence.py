from __future__ import annotations

from dataclasses import dataclass

from app.domain.models import EvidenceHit


@dataclass(frozen=True)
class EvidenceDocument:
    title: str
    source_label: str
    url: str
    summary: str
    keywords: tuple[str, ...]


EVIDENCE_DOCUMENTS = [
    EvidenceDocument(
        title="Mild fetal ventriculomegaly evaluation and management",
        source_label="SMFM 2018",
        url="https://publications.smfm.org/publications/256-society-for-maternal-fetal-medicine-consult-series-45/",
        summary=(
            "SMFM recommends detailed anatomic evaluation, diagnostic testing with chromosomal microarray, "
            "CMV and toxoplasmosis testing, and follow-up ultrasound when ventriculomegaly is detected. "
            "Counseling separates mild 10-12 mm ventriculomegaly from moderate 13-15 mm ventriculomegaly."
        ),
        keywords=(
            "ventriculomegaly",
            "mild ventriculomegaly",
            "moderate ventriculomegaly",
            "severe ventriculomegaly",
            "atrial diameter",
            "microarray",
            "cmv",
            "toxoplasmosis",
            "follow-up",
            "asymmetry",
        ),
    ),
    EvidenceDocument(
        title="Patient-facing ventriculomegaly counseling",
        source_label="ISUOG VM Leaflet",
        url="https://www.isuog.org/resource/ventriculomegaly--isuog-patient-information-series-draft-ra-25-09_final-pdf.html",
        summary=(
            "ISUOG patient guidance frames ventriculomegaly as extra fluid in the fetal brain ventricles, "
            "emphasizes that outcome depends on severity and associated findings, and discusses additional "
            "testing, specialist review, and follow-up imaging."
        ),
        keywords=(
            "ventriculomegaly",
            "parent counseling",
            "associated findings",
            "follow-up",
            "genetic testing",
            "infection",
            "mild ventriculomegaly",
            "moderate ventriculomegaly",
            "severe ventriculomegaly",
        ),
    ),
    EvidenceDocument(
        title="Targeted fetal CNS neurosonography checklist",
        source_label="ISUOG CNS 2021",
        url="https://www.isuog.org/static/b91bae06-731b-4a2d-8bbcbb2f0d886af4/ISUOG-Practice-Guidelines-CNS-part-2-targeted-neurosonography.pdf",
        summary=(
            "ISUOG targeted neurosonography guidance supports a structured second-line CNS review that includes "
            "ventricles, midline structures, posterior fossa, cortical development, spine, and associated anomalies."
        ),
        keywords=(
            "targeted neurosonography",
            "cortex",
            "sulcation",
            "posterior fossa",
            "corpus callosum",
            "csp",
            "third ventricle",
            "spine",
            "associated anomalies",
            "ventriculomegaly",
        ),
    ),
    EvidenceDocument(
        title="Corpus callosum counseling context",
        source_label="ISUOG ACC Leaflet",
        url="https://www.isuog.org/clinical-resources/patient-information-series/patient-information-pregnancy-conditions/brain/agenesis-of-the-corpus-callosum.html",
        summary=(
            "ISUOG patient guidance for corpus callosum abnormalities emphasizes the broad outcome range, "
            "the importance of associated brain or body anomalies, and the role of genetic testing and specialist counseling."
        ),
        keywords=(
            "corpus callosum",
            "callosal",
            "short corpus callosum",
            "agenesis",
            "csp",
            "midline",
            "genetic testing",
            "parent counseling",
        ),
    ),
    EvidenceDocument(
        title="Posterior fossa and Dandy-Walker counseling context",
        source_label="ISUOG Dandy-Walker",
        url="https://www.isuog.org/clinical-resources/patient-information-series/patient-information-pregnancy-conditions/brain/dandy-walker-complex.html",
        summary=(
            "ISUOG patient guidance for Dandy-Walker complex explains that prognosis depends on the exact posterior-fossa "
            "entity, associated anomalies, and genetic findings, so fetal MRI and specialist review can be important."
        ),
        keywords=(
            "posterior fossa",
            "dandy-walker",
            "vermian",
            "vermis",
            "small vermis",
            "small tcd",
            "cerebellum",
            "genetic testing",
            "fetal mri",
            "parent counseling",
        ),
    ),
    EvidenceDocument(
        title="Severe ventriculomegaly outcome literature",
        source_label="Carta 2018",
        url="https://openaccess.sgul.ac.uk/id/eprint/109965/",
        summary=(
            "A systematic review of apparently isolated severe bilateral ventriculomegaly reports substantially higher "
            "risk than mild ventriculomegaly and supports careful multidisciplinary counseling."
        ),
        keywords=(
            "severe ventriculomegaly",
            "ventriculomegaly",
            "hydrocephalus",
            "multidisciplinary",
            "outcome",
            "prognosis",
        ),
    ),
]


def retrieve_evidence(search_terms: list[str], *, limit: int = 4) -> list[EvidenceHit]:
    normalized_terms = {term.lower().strip() for term in search_terms if term.strip()}
    hits: list[EvidenceHit] = []

    for document in EVIDENCE_DOCUMENTS:
        keyword_matches = [
            keyword
            for keyword in document.keywords
            if keyword in normalized_terms or any(keyword in term or term in keyword for term in normalized_terms)
        ]
        score = len(keyword_matches) * 3
        if any(term in document.summary.lower() for term in normalized_terms):
            score += 1
        if score == 0:
            continue
        hits.append(
            EvidenceHit(
                title=document.title,
                source_label=document.source_label,
                url=document.url,
                summary=document.summary,
                matched_terms=keyword_matches[:5],
                relevance_score=score,
            )
        )

    hits.sort(key=lambda hit: hit.relevance_score, reverse=True)
    return hits[:limit]
