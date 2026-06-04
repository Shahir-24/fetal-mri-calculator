# Fetal MRI Calculator

Local-first fetal brain MRI biometry calculator built with FastAPI and Jinja.

This version focuses completely on the fetal MRI workflow:
- gestational-age-adjusted z-scores and percentiles
- expected 5th-95th percentile ranges
- structured report-ready text
- advisory concern cards with literature-based likelihood ranges where the sources support them

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install fastapi uvicorn jinja2 scipy python-multipart pytest httpx
.venv/bin/uvicorn app.main:app --reload
```

Then open [http://127.0.0.1:8001](http://127.0.0.1:8001).

On macOS you can also double-click:
- [Open Fetal MRI Calculator.command](/Users/shahir/Documents/TicTacToe/fetal%20mri%20calculator/Open%20Fetal%20MRI%20Calculator.command)
- or [Fetal MRI Calculator.app](/Users/shahir/Documents/TicTacToe/fetal%20mri%20calculator/Fetal%20MRI%20Calculator.app)

## Tests

```bash
.venv/bin/pytest
```

## Implemented exact-source models

- `Kyriakopoulou 2017`
  - skull BPD
  - skull OFD
  - brain BPD
  - brain OFD
  - atrial diameter
  - TCD
  - vermian height
  - vermian width
- `Harreld 2011`
  - corpus callosum length

## Current boundaries

- This is an advisory calculator, not a standalone diagnostic engine.
- Concern cards can show literature-based ranges when a source supports them, but they do not generate patient-specific causal probabilities from biometry alone.
- Qualitative findings remain deferred.

## Planned next

- CSP width
- pons AP diameter
- third ventricle width
- Chiari II posterior-fossa discriminator
- qualitative findings such as absent CSP or non-visualized corpus callosum
- microcephaly / macrocephaly cards
