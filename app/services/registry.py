from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.domain.models import Citation, InputField, ParameterDefinition, ValidatedRange
from app.services.normative_models import QuadraticLinearModel, QuadraticMeanPchipSigmaModel


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@dataclass(frozen=True)
class Registry:
    parameters: dict[str, ParameterDefinition]
    models: dict[str, object]
    input_fields: list[InputField]
    deferred_parameters: list[str]


def _load_json(filename: str) -> dict:
    return json.loads((DATA_DIR / filename).read_text())


@lru_cache(maxsize=1)
def load_registry() -> Registry:
    kyriakopoulou = _load_json("kyriakopoulou_2017_formulas.json")
    harreld = _load_json("harreld_2011_corpus_callosum.json")

    parameters: dict[str, ParameterDefinition] = {}
    models: dict[str, object] = {}

    kyriakopoulou_citation = Citation(
        short_label=kyriakopoulou["source"]["short_label"],
        title=kyriakopoulou["source"]["title"],
        url=kyriakopoulou["source"]["url"],
        note=kyriakopoulou["source"]["note"],
    )
    kyriakopoulou_range = ValidatedRange(
        min_weeks=kyriakopoulou["validated_ga_weeks"]["min"],
        max_weeks=kyriakopoulou["validated_ga_weeks"]["max"],
    )

    for parameter_id, spec in kyriakopoulou["parameters"].items():
        model = QuadraticLinearModel(
            mean_intercept=spec["mean_coeffs"][0],
            mean_linear=spec["mean_coeffs"][1],
            mean_quadratic=spec["mean_coeffs"][2],
            sd_intercept=spec["sd_coeffs"][0],
            sd_linear=spec["sd_coeffs"][1],
        )
        parameters[parameter_id] = ParameterDefinition(
            parameter_id=parameter_id,
            label=spec["label"],
            unit=spec["unit"],
            group=spec["group"],
            citation=kyriakopoulou_citation,
            validated_range=kyriakopoulou_range,
            model_name="Quadratic mean + linear SD from supplement calculator",
        )
        models[parameter_id] = model

    harreld_citation = Citation(
        short_label=harreld["source"]["short_label"],
        title=harreld["source"]["title"],
        url=harreld["source"]["url"],
        note=harreld["source"]["note"],
    )
    harreld_range = ValidatedRange(
        min_weeks=harreld["validated_ga_weeks"]["min"],
        max_weeks=harreld["validated_ga_weeks"]["max"],
    )
    corpus_callosum_id = harreld["parameter"]["parameter_id"]
    parameters[corpus_callosum_id] = ParameterDefinition(
        parameter_id=corpus_callosum_id,
        label=harreld["parameter"]["label"],
        unit=harreld["parameter"]["unit"],
        group=harreld["parameter"]["group"],
        citation=harreld_citation,
        validated_range=harreld_range,
        model_name="Quadratic mean + PCHIP sigma derived from 95% individual prediction intervals",
    )
    models[corpus_callosum_id] = QuadraticMeanPchipSigmaModel(
        mean_intercept=harreld["parameter"]["mean_coeffs"][0],
        mean_linear=harreld["parameter"]["mean_coeffs"][1],
        mean_quadratic=harreld["parameter"]["mean_coeffs"][2],
        sigma_points=harreld["parameter"]["sigma_points"],
    )

    input_fields = [
        InputField(
            "skull_bpd",
            "skull_bpd",
            "Skull biparietal diameter",
            "Global Brain / Skull Growth",
            "mm",
            "Outer calvarial biparietal diameter on the standard axial plane.",
        ),
        InputField(
            "skull_ofd",
            "skull_ofd",
            "Skull occipitofrontal diameter",
            "Global Brain / Skull Growth",
            "mm",
            "Outer calvarial fronto-occipital diameter on the same axial plane.",
        ),
        InputField(
            "brain_bpd",
            "brain_bpd",
            "Brain biparietal diameter",
            "Global Brain / Skull Growth",
            "mm",
            "Inner cerebral biparietal diameter excluding the calvarium.",
        ),
        InputField(
            "brain_ofd",
            "brain_ofd",
            "Brain fronto-occipital length",
            "Global Brain / Skull Growth",
            "mm",
            "Inner cerebral fronto-occipital measurement on the axial brain plane.",
        ),
        InputField(
            "atrial_left",
            "atrial_diameter",
            "Left atrial diameter",
            "Ventricular System",
            "mm",
            "Measured at the atrium of the lateral ventricle perpendicular to the ventricle axis.",
        ),
        InputField(
            "atrial_right",
            "atrial_diameter",
            "Right atrial diameter",
            "Ventricular System",
            "mm",
            "Use the same atrial measurement convention on the contralateral side.",
        ),
        InputField(
            "tcd",
            "tcd",
            "Transverse cerebellar diameter",
            "Posterior Fossa",
            "mm",
            "Outer-to-outer transverse cerebellar width on the posterior-fossa view.",
        ),
        InputField(
            "vermian_height",
            "vermian_height",
            "Vermian height",
            "Posterior Fossa",
            "mm",
            "Craniocaudal vermian dimension on the midsagittal posterior-fossa plane.",
        ),
        InputField(
            "vermian_width",
            "vermian_width",
            "Vermian width",
            "Posterior Fossa",
            "mm",
            "Anteroposterior vermian dimension on the midsagittal posterior-fossa plane.",
        ),
        InputField(
            "corpus_callosum_length",
            "corpus_callosum_length",
            "Corpus callosum length",
            "Midline Structures",
            "mm",
            "Curvilinear callosal length on a true midsagittal image.",
        ),
    ]

    deferred_parameters = [
        "Cavum septum pellucidum width",
        "Pons AP diameter",
        "Third ventricle width",
        "Chiari II posterior-fossa measurements (TDPF and CSA)",
        "Microcephaly / macrocephaly cards using derived head circumference",
        "Non-numeric findings such as absent CSP or non-visualized corpus callosum",
        "Ambiguous discordance trigger between brain and skull diameters pending explicit numeric rule",
    ]

    return Registry(
        parameters=parameters,
        models=models,
        input_fields=input_fields,
        deferred_parameters=deferred_parameters,
    )


def grouped_input_fields() -> list[tuple[str, list[InputField]]]:
    registry = load_registry()
    groups: dict[str, list[InputField]] = {}
    for field in registry.input_fields:
        groups.setdefault(field.group, []).append(field)
    return list(groups.items())


def implemented_sources() -> list[Citation]:
    registry = load_registry()
    seen: set[str] = set()
    citations: list[Citation] = []
    for field in registry.input_fields:
        citation = registry.parameters[field.parameter_id].citation
        if citation.short_label in seen:
            continue
        seen.add(citation.short_label)
        citations.append(citation)
    return citations
