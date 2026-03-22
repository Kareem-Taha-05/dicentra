# Changelog

All notable changes to Dicentra are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [2.0.0] — 2025-01-01

### Added
- Complete rewrite with MVC architecture (Model / Controller / View separation)
- Window/Level control with live HU histogram and 7 clinical presets
- MedVol-inspired rendering: raw HU frame cache + pure-function W/L application
- Multi-frame M2D playback with `|< << > || >> >|` controls and scrubber
- DICOM series loading: sorts slices by `InstanceNumber`, stacks as volume
- Measurement ruler with pixel-spacing-aware mm output
- 8 colourmap LUTs (Grayscale, Inverted, Hot, Cool, Viridis, Plasma, Bone, Jet)
- Export suite: PNG, JPEG, animated GIF, CSV metadata, JSON metadata
- Series browser: parallel folder scan, thumbnails, recent files
- Metadata browser: comprehensive tag viewer with 7 filter categories
- 3D tile viewer for all slices
- Auto W/L on load using 1st–99th percentile of middle frame
- "Deep Space Medical" dark theme (indigo/violet palette)
- 43 unit tests, zero Qt dependencies in test suite

### Changed
- Window/Level now operates on cached float32 HU arrays — no signal loops
- Presets use standard radiological values (Brain W=80, Bone W=2000, etc.)

---

## [1.0.0] — 2024-06-01

### Added
- Initial release — single DICOM file viewer, basic metadata display
