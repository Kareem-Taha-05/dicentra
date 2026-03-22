# Data Loaders API

Module: `app.data.dicom_model`

---

## `DicomModel`

The central data model. Zero Qt imports — fully testable without a display.

### `load(file_path: str)`

Load a single DICOM file. Handles single-frame and multi-frame (3D volume) files.

### `load_series(file_paths: list[str])`

Load a list of single-frame DICOM files as a multi-frame volume. Files are sorted by `InstanceNumber` before stacking.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `is_loaded` | `bool` | True after a successful load |
| `is_multiframe` | `bool` | True if more than one frame |
| `frame_count` | `int` | Number of frames |
| `frames` | `list[np.ndarray]` | Raw pixel arrays |
| `dataset` | `pydicom.Dataset` | Full DICOM dataset |

---

## `load_series_from_folder`

```python
load_series_from_folder(folder: str) -> list[SeriesInfo]
```

Scan a folder for DICOM files, group by `SeriesInstanceUID`, return series metadata.
