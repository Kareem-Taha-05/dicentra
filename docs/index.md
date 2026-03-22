# Dicentra

**A modern, modular DICOM viewer built for clinical imaging workflows.**

Dicentra is a desktop application for viewing, analysing, and exporting DICOM medical images. It is built with Python and PyQt5, and follows a clean MVC architecture that makes it easy to extend.

![Dicentra screenshot](../assets/demo/screenshot_main.png)

---

## Highlights

| Feature | Detail |
|---------|--------|
| **Image viewer** | Single frame + M2D multi-frame playback |
| **Window / Level** | Live sliders, 7 clinical presets, HU histogram |
| **Colourmap LUTs** | 8 built-in: Grayscale, Hot, Viridis, Plasma, and more |
| **Ruler** | Click-drag distance measurement in mm |
| **Export** | PNG, JPEG, animated GIF, CSV, JSON |
| **Series browser** | Parallel folder scan with thumbnails |
| **Metadata** | Full DICOM tag browser with category filters |
| **Theme** | "Deep Space Medical" dark theme |

---

## Quick install

```bash
git clone https://github.com/your-username/dicentra.git
cd dicentra
pip install -r requirements.txt
python main.py
```

See [Installation](installation.md) for a full guide including virtual environments.

---

> **Not for clinical use.** Research and educational purposes only.
