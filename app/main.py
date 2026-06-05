from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.services.calculator import build_case_presets, build_reference_case, calculate_bundle
from app.services.registry import grouped_input_fields, implemented_sources, load_registry


def _app_base_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent

BASE_DIR = _app_base_path()

app = FastAPI(title="Fetal MRI Calculator")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _parse_int(value: str | None, default: int = 0) -> int:
    if value is None or value == "":
        return default
    return int(value)


def _parse_float(value: str) -> float:
    return float(value.replace(",", "").strip())


def _parse_measurements(form_data: dict[str, str]) -> tuple[dict[str, float], list[str]]:
    registry = load_registry()
    measurements: dict[str, float] = {}
    errors: list[str] = []
    fields_by_name = {field.field_name: field for field in registry.input_fields}
    for field_name, raw_value in form_data.items():
        field = fields_by_name.get(field_name)
        if field is None or raw_value == "":
            continue
        try:
            parsed = _parse_float(raw_value)
        except ValueError:
            errors.append(f"{field.label} must be a valid number.")
            continue
        if parsed <= 0:
            errors.append(f"{field.label} must be greater than 0.")
            continue
        measurements[field_name] = parsed
    return measurements, errors


def _default_form_values() -> dict[str, str]:
    return {"gestational_weeks": "", "gestational_days": "0"}


def _build_context(
    request: Request,
    *,
    form_values: dict[str, str] | None = None,
    errors: list[str] | None = None,
    bundle=None,
) -> dict:
    registry = load_registry()
    return {
        "request": request,
        "field_groups": grouped_input_fields(),
        "implemented_sources": implemented_sources(),
        "implemented_parameter_count": len(registry.input_fields),
        "deferred_parameters": registry.deferred_parameters,
        "reference_case": build_reference_case(24, 0),
        "case_presets": build_case_presets(24, 0),
        "form_values": form_values or _default_form_values(),
        "errors": errors or [],
        "bundle": bundle,
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", _build_context(request))


@app.post("/calculate", response_class=HTMLResponse)
async def calculate(request: Request) -> HTMLResponse:
    form = await request.form()
    form_values = {key: str(value) for key, value in form.items()}
    measurements, errors = _parse_measurements(form_values)

    weeks_raw = form_values.get("gestational_weeks", "")
    days_raw = form_values.get("gestational_days", "0")

    if measurements and weeks_raw == "":
        errors.append("Gestational age in weeks is required before measurements can be interpreted.")

    gestational_days = 0
    if days_raw != "":
        try:
            gestational_days = _parse_int(days_raw)
        except ValueError:
            errors.append("Gestational age days must be an integer between 0 and 6.")
    if not 0 <= gestational_days <= 6:
        errors.append("Gestational age days must be between 0 and 6.")

    bundle = None
    if not errors and weeks_raw != "" and measurements:
        try:
            gestational_weeks = _parse_int(weeks_raw)
            if gestational_weeks <= 0:
                raise ValueError
            bundle = calculate_bundle(gestational_weeks, gestational_days, measurements)
        except ValueError:
            errors.append("Gestational age weeks must be a positive whole number.")

    return templates.TemplateResponse(
        request,
        "partials/results.html",
        _build_context(request, form_values=form_values, errors=errors, bundle=bundle),
    )


def main(host: str = "127.0.0.1", port: int = 8001, open_browser: bool = True) -> None:
    import threading
    import time
    import uvicorn
    import webbrowser

    if open_browser:
        def _open() -> None:
            time.sleep(1.0)
            webbrowser.open(f"http://{host}:{port}")

        threading.Thread(target=_open, daemon=True).start()

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
