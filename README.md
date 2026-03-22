# Dicentra

A modern, modular DICOM file viewer focused on **2D clinical workflow, image analysis, and data intelligence**. Built with Python, PyQt5, pydicom, and Matplotlib.

> **Not for clinical use.** Research and educational purposes only.

---

## Features

### 🖼 Image Viewer
- Display single-frame DICOM images with correct HU rescaling
- Auto W/L on load — shows the full original dynamic range immediately
- Play M2D multi-frame files as animations with live frame counter
- Custom `RulerCanvas` widget — renders image with full overlay support

### 🎨 Colormap / LUT Selector
- 8 built-in lookup tables: **Grayscale, Inverted, Hot, Cool, Viridis, Plasma, Bone, Jet**
- Visual swatch chips — click to switch colourmap instantly

### 📏 Measurement Ruler
- Toggle ruler mode, then **click-drag** anywhere on the image to measure
- Distance shown in **millimetres** using `PixelSpacing` DICOM tag
- Up to 5 simultaneous colour-coded measurements
- Results panel in the left sidebar; **Clear** removes all

### 💾 Export Suite
- **PNG / JPEG** — save current frame with W/L and LUT baked in
- **Animated GIF** — export all M2D frames at 10 fps
- **CSV / JSON** — all metadata tags

### 🔆 Window / Level Control
- W (Contrast) and L (Level) sliders with exact HU spinboxes
- Live HU range display
- 7 clinical presets — Brain, Subdural, Stroke, Bone, Soft Tissue, Lung, Liver
- 80ms debounce — smooth, no stutter

### 📊 Live Pixel Histogram
- Per-frame HU distribution with W/L overlay band
- Click to snap L (brightness center) to any HU value

### ⏯ Frame Navigation
- `|<` `<<` `>` / `||` `>>` `>|` controls + scrubber slider
- Keyboard: Space, ←, →, Home, End

### 📂 DICOM Series Browser
- Open a folder → auto-groups by SeriesInstanceUID
- Series cards with thumbnail, modality badge, description, slice count
- Background scan thread — UI stays responsive
- Recent files list (persisted across sessions)
- File Info + Quick Stats cards for every loaded file

### 🗂 Metadata Browser
- All DICOM tags in a searchable table
- Quick-filter chips: Patient · Study · Modality · Physician · Image · Pixel Data
- Anonymisation with custom prefix

### 🔲 3D / Tile Viewer
- All slices as a scrollable tile grid

---

## Quick Start

```bash
git clone https://github.com/your-org/dicentra.git
cd dicentra
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## Usage

### Load and view a file
1. Click **📂 Load** → select a `.dcm` file. The image displays immediately at full dynamic range.
2. Adjust **W** (contrast) and **L** (level/brightness) sliders, or click a preset.
3. Pick a **colormap** from the swatch row.

### Navigate frames
- **> / ||** — play / pause
- **<< / >>** — step one frame
- **|< / >|** — jump to first / last frame
- Drag the scrubber to any frame
- Keyboard: Space / ← / → / Home / End

### Measure distances
1. Click **📏 Ruler** to enable.
2. Drag on the image — live mm readout.
3. Results appear in the **Measurements** panel on the left.

### Export
Click **💾 Export** → choose PNG, JPEG, GIF, CSV, or JSON.

---

## Project Structure

```
dicentra/
├── main.py
├── requirements.txt
├── config/settings.py
│
├── app/
│   ├── data/dicom_model.py
│   ├── logic/
│   │   ├── controller.py
│   │   ├── image_processor.py
│   │   ├── colormap.py
│   │   └── export_utils.py
│   └── gui/
│       ├── main_window.py
│       ├── image_tab.py
│       ├── ruler_canvas.py
│       ├── colormap_bar.py
│       ├── export_dialog.py
│       ├── wl_panel.py
│       ├── histogram_panel.py
│       ├── series_browser.py
│       ├── metadata_tab.py
│       ├── threed_tab.py
│       └── stylesheet.py
│
└── tests/
    ├── test_image_processor.py
    ├── test_dicom_model.py
    └── test_new_features.py
```

---

## Running Tests

```bash
pytest tests/ -v
# 43 tests — all pure Python, no display required
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `pydicom` | DICOM I/O |
| `numpy` | Array processing, LUTs |
| `PyQt5` | GUI framework |
| `matplotlib` | Embedded histogram |
| `Pillow` | PNG/JPEG export |
| `imageio` | Animated GIF export |

---

## License

MIT
