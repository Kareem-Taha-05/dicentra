# Quick Start

## 1. Open a single DICOM file

Click **📂 Load** in the header bar, or drag a `.dcm` file onto the window.

The image displays immediately using the full dynamic range of the file.

## 2. Adjust Window / Level

Move the **W** (contrast) and **L** (level) sliders in the right panel, or click a preset:

| Preset | Best for |
|--------|----------|
| Brain | Grey/white matter |
| Bone | Cortical bone detail |
| Lung | Airways and parenchyma |
| Soft Tissue | General abdomen |
| Liver | Hepatic parenchyma |
| Subdural | Blood near the brain surface |
| Stroke | Subtle early ischaemia |

## 3. Navigate frames (multi-frame files)

Use `|< << > || >> >|` buttons or drag the scrubber. Keyboard shortcuts:

| Key | Action |
|-----|--------|
| Space | Play / pause |
| ← → | Step one frame |
| Home / End | First / last frame |

## 4. Load a DICOM series

Click **📁 Open Folder** in the left sidebar, select a folder. Dicentra groups files by SeriesInstanceUID and shows thumbnails. Click a series card to load all slices as a scrollable volume.

## 5. Measure distances

Click **📏 Ruler**, then click-drag on the image. The measurement appears in mm (requires `PixelSpacing` tag in the file).

## 6. Export

Click **💾 Export** and choose:
- **PNG / JPEG** — current frame with W/L applied
- **GIF** — animated multi-frame export
- **CSV / JSON** — all DICOM metadata
