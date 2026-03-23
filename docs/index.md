---
title: Dicentra
description: Clinical DICOM viewer built with Python and PyQt5
hide:
  - navigation
  - toc
---

<div align="center" markdown>

# Dicentra

**Clinical DICOM viewer — window/level, series browser, metadata, colormaps**

[Get Started](installation.md){ .md-button .md-button--primary }
[Quick Start](quickstart.md){ .md-button }
[GitHub](https://github.com/Kareem-Taha-05/dicentra){ .md-button }

</div>

---

## What is Dicentra?

Dicentra is a desktop DICOM viewer focused on clinical 2D imaging workflows. It opens any DICOM file or multi-slice series, auto-computes the correct Window/Level from the actual pixel data, and keeps the series browser, histogram, and metadata in perfect sync as you work.

Built on **PyQt5 · pydicom · NumPy · Matplotlib** — no heavyweight dependencies, no configuration, runs anywhere Python runs.

!!! warning "Not for clinical use"
    Dicentra is intended for research and educational purposes only.

---

## Feature overview

<div class="grid cards" markdown>

-   **🔆 Window / Level**

    ---

    Auto-computes W/L on load using the 1st–99th percentile of the pixel data.
    Live HU sliders, exact spinboxes, and 7 clinical presets.

-   **📊 Live Histogram**

    ---

    Per-frame HU distribution with a W/L overlay band. Click any bar to snap the Level center to that HU value.

-   **🎨 8 Colormap LUTs**

    ---

    Grayscale, Inverted, Hot, Cool, Viridis, Plasma, Bone, Jet — as clickable chips, live-applied on every render.

-   **📂 Series Browser**

    ---

    Folder scan groups files by `SeriesInstanceUID`. Thumbnails generated in a background thread. Click a card to load the full volume.

-   **📏 Measurement Ruler**

    ---

    Click-drag distance measurement in millimetres using `PixelSpacing`. Up to 5 simultaneous colour-coded rulers.

-   **🗂 Metadata Browser**

    ---

    Every DICOM tag in a searchable, sortable table with 7 category filter chips and built-in anonymisation.

</div>

---

## Quick install

```bash
git clone https://github.com/Kareem-Taha-05/dicentra.git
cd dicentra
pip install -r requirements.txt
python main.py
```

See the full [Installation guide](installation.md) for virtual environment setup and platform notes.
