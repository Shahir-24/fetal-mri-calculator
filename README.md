# Fetal MRI Calculator

Local-first fetal brain MRI biometry calculator built with FastAPI and Jinja.

This version focuses completely on the fetal MRI workflow:
- gestational-age-adjusted z-scores and percentiles
- expected 5th-95th percentile ranges
- structured report-ready text
- advisory concern cards with literature-based likelihood ranges where the sources support them

## Run

### Run from source

```bash
python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install fastapi uvicorn jinja2 scipy python-multipart pytest httpx
.venv/bin/python -m app
```

Then open [http://127.0.0.1:8001](http://127.0.0.1:8001).

### Build a cross-platform executable locally

Use the included build helper to create a single-file app for your platform:

```bash
python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install pyinstaller
.venv/bin/python scripts/build.py
```

The built executable will be placed in `dist/`.

### Download a packaged app from GitHub

This repository can build platform-specific release artifacts on GitHub using `PyInstaller`.
After a tagged release, GitHub can publish one artifact per platform:

- macOS: `Fetal MRI Calculator`
- Windows: `Fetal MRI Calculator.exe`
- Linux: `Fetal MRI Calculator`

On Windows, double-click the `.exe` file.
On macOS or Linux, run the downloaded file after making it executable:

```bash
chmod +x "Fetal MRI Calculator"
./"Fetal MRI Calculator"
```

The app will open your browser automatically at `http://127.0.0.1:8001`.

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
