# Fetal MRI Calculator

Local-first fetal brain MRI biometry calculator built with FastAPI and Jinja.

---

## ⚡ **Quick Start: Download & Run (No Installation Required)**

### 1️⃣ Download the app for your platform:

Go to **[Releases](https://github.com/Shahir-24/fetal-mri-calculator/releases)** and download:

- 🍎 **macOS**: `fetal-mri-calculator-macos.zip` → unzip and double-click `fetal-mri-calculator-macos.command`
- 🪟 **Windows**: `fetal-mri-calculator-windows.zip` → unzip on Windows and double-click `fetal-mri-calculator.exe`
- 🐧 **Linux**: `fetal-mri-calculator-linux.zip` → unzip and run `./fetal-mri-calculator-linux`

### 2️⃣ Important
- `fetal-mri-calculator.exe` is a Windows executable and will not run on macOS or Linux.
- Use the macOS package on macOS, the Linux package on Linux, and the Windows package on Windows.

### 3️⃣ Open the app and you're done! 🎉

The app opens automatically in your browser at `http://127.0.0.1:8001`

---

## 📊 Features

This version focuses completely on the fetal MRI workflow:
- gestational-age-adjusted z-scores and percentiles
- expected 5th-95th percentile ranges
- structured report-ready text
- advisory concern cards with literature-based likelihood ranges where the sources support them

## 🔧 Alternative Ways to Run (For Developers)

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
