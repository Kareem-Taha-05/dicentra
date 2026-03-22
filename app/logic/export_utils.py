"""
app/logic/export_utils.py
=========================
Pure I/O export helpers — no Qt imports.
Called by export_dialog.py and testable without a display.
"""

from __future__ import annotations

import csv
import json

import numpy as np


def export_frame_png(arr: np.ndarray, path: str) -> None:
    """Save uint8 array (grayscale or RGBA) as PNG."""
    from PIL import Image

    if arr.ndim == 2:
        Image.fromarray(arr, mode="L").save(path)
    elif arr.shape[2] == 4:
        Image.fromarray(arr, mode="RGBA").save(path)
    else:
        Image.fromarray(arr, mode="RGB").save(path)


def export_frame_jpeg(arr: np.ndarray, path: str, quality: int = 92) -> None:
    from PIL import Image

    if arr.ndim == 2:
        img = Image.fromarray(arr, mode="L")
    elif arr.shape[2] == 4:
        img = Image.fromarray(arr[:, :, :3], mode="RGB")
    else:
        img = Image.fromarray(arr, mode="RGB")
    img.save(path, quality=quality)


def export_metadata_csv(tags, path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Tag", "Name", "Value"])
        for row in tags:
            writer.writerow([row.tag, row.name, row.value])


def export_metadata_json(tags, path: str) -> None:
    data = [{"tag": r.tag, "name": r.name, "value": r.value} for r in tags]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
