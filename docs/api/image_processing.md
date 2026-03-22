# Image Processing API

Module: `app.logic.image_processor`

---

## `apply_window_level`

```python
apply_window_level(
    hu_array: np.ndarray,
    window_width: float,
    window_center: float,
) -> np.ndarray
```

Apply DICOM Window/Level to a float32 HU array and return a uint8 image.

**Parameters**

| Name | Type | Description |
|------|------|-------------|
| `hu_array` | `np.ndarray` (float32) | Raw Hounsfield Unit values |
| `window_width` | `float` | Range of HU values to map (>0) |
| `window_center` | `float` | HU value at 50% grey |

**Returns** `np.ndarray` (uint8) — values in [0, 255]

---

## `compute_histogram`

```python
compute_histogram(
    hu_array: np.ndarray,
    bins: int = 128,
) -> tuple[np.ndarray, np.ndarray]
```

Compute a log-scale HU histogram for the pixel distribution panel.

**Returns** `(counts, edges)` — compatible with `matplotlib.axes.bar`

---

## `normalize_to_uint8`

```python
normalize_to_uint8(array: np.ndarray) -> np.ndarray
```

Linearly map any numeric array to [0, 255] uint8.
