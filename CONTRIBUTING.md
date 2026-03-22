# Contributing to Dicentra

Thank you for your interest in contributing. This guide covers everything you need.

---

## Development setup

```bash
git clone https://github.com/Kareem-Taha-05/dicentra.git
cd dicentra
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pre-commit install
```

## Running tests

```bash
pytest tests/ -v
```

All 43 tests run without a display — no Qt window required.

## Code style

We use **Ruff** for linting and formatting:

```bash
ruff check .
ruff format .
```

Pre-commit runs both automatically on every commit.

## Project structure

```
dicentra/
├── app/
│   ├── data/          # DicomModel — zero Qt, pure data
│   ├── logic/         # Controller, image processor, colormaps, export
│   └── gui/           # All PyQt5 widgets
├── config/            # Settings, presets, constants
├── tests/             # Pytest suite — pure Python, no display
├── docs/              # MkDocs documentation
└── examples/          # Standalone usage scripts
```

## Architecture principles

- **Model** (`app/data/`) has zero Qt imports — tested without a display
- **Controller** (`app/logic/controller.py`) connects model to signals
- **Views** (`app/gui/`) are purely reactive — no business logic
- Window/Level rendering uses the MedVol pattern: raw HU cache + pure functions

## Submitting a pull request

1. Fork the repository and create a feature branch: `git checkout -b feat/my-feature`
2. Write tests for new behaviour
3. Run `pytest tests/ -v` — all tests must pass
4. Open a PR against `main` — fill in the template
