# Architecture

Dicentra follows a strict **MVC** (Model / Controller / View) pattern.

## Layers

```
┌─────────────────────────────────────┐
│  View  (app/gui/)                   │
│  Pure reactive Qt widgets           │
│  Zero business logic                │
└──────────────┬──────────────────────┘
               │ Qt signals
┌──────────────▼──────────────────────┐
│  Controller  (app/logic/controller) │
│  Connects model to signals          │
│  W/L rendering — MedVol pattern     │
└──────────────┬──────────────────────┘
               │ method calls
┌──────────────▼──────────────────────┐
│  Model  (app/data/dicom_model.py)   │
│  Zero Qt imports                    │
│  Testable without a display         │
└─────────────────────────────────────┘
```

## W/L rendering — MedVol pattern

Inspired by MedVol's `update_views()` approach:

```python
# Every render call:
hu  = raw_hu_frames[_display_index]          # read raw float32 HU array
arr = apply_window_level(hu, width, center)  # pure function → uint8
wl_render_ready.emit(arr)                    # update canvas only
```

`raw_hu_frames` is built once on load (slope/intercept already applied).  
W/L changes never touch the frame index — no signal loops possible.

## Signal flow

```
WLPanel.wl_changed
  → Controller.set_window_level()
    → _redisplay()  →  wl_render_ready  →  _show_wl_rerender (canvas only)
    → wl_changed    →  WLPanel.set_wl   (silent, blockSignals)
                    →  HistogramPanel.update_wl_band
```

## Testing

All 43 tests in `tests/` run without a display. The model layer has zero Qt imports, so it is tested directly. Controller logic is tested with `unittest.mock`.
