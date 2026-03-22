"""
app/logic/colormap.py
=====================
Pure-NumPy colourmap engine. No Qt, no matplotlib dependency for runtime.

Each LUT is a (256, 3) uint8 array mapping grayscale [0-255] → RGB.
apply_lut() takes a uint8 grayscale array and returns an RGBA QImage-ready
(H, W, 4) uint8 array.
"""

from __future__ import annotations

from typing import Dict

import numpy as np

# ── LUT definitions ────────────────────────────────────────────────────────────


def _linear(r1, g1, b1, r2, g2, b2) -> np.ndarray:
    """Simple two-stop linear gradient LUT."""
    t = np.linspace(0, 1, 256)
    lut = np.zeros((256, 3), dtype=np.uint8)
    lut[:, 0] = (r1 + (r2 - r1) * t).astype(np.uint8)
    lut[:, 1] = (g1 + (g2 - g1) * t).astype(np.uint8)
    lut[:, 2] = (b1 + (b2 - b1) * t).astype(np.uint8)
    return lut


def _build_luts() -> Dict[str, np.ndarray]:
    luts: Dict[str, np.ndarray] = {}
    t = np.linspace(0, 1, 256)

    # Grayscale — identity
    g = (t * 255).astype(np.uint8)
    luts["Grayscale"] = np.stack([g, g, g], axis=1)

    # Grayscale Inverted
    gi = (255 - t * 255).astype(np.uint8)
    luts["Inverted"] = np.stack([gi, gi, gi], axis=1)

    # Hot — black → red → yellow → white
    r = np.clip(t * 3, 0, 1)
    gv = np.clip(t * 3 - 1, 0, 1)
    b = np.clip(t * 3 - 2, 0, 1)
    luts["Hot"] = (np.stack([r, gv, b], axis=1) * 255).astype(np.uint8)

    # Cool — cyan → magenta
    luts["Cool"] = (np.stack([t, 1 - t, np.ones(256)], axis=1) * 255).astype(np.uint8)

    # Viridis (approximated with 5 anchor points)
    anchors = np.array(
        [
            [0.267, 0.005, 0.329],
            [0.229, 0.322, 0.545],
            [0.128, 0.566, 0.551],
            [0.369, 0.788, 0.383],
            [0.993, 0.906, 0.144],
        ]
    )
    x = np.linspace(0, 1, 256)
    xp = np.linspace(0, 1, len(anchors))
    vir = np.stack([np.interp(x, xp, anchors[:, c]) for c in range(3)], axis=1)
    luts["Viridis"] = (vir * 255).astype(np.uint8)

    # Plasma (approximated)
    anchors_p = np.array(
        [
            [0.050, 0.030, 0.528],
            [0.460, 0.052, 0.600],
            [0.798, 0.198, 0.470],
            [0.972, 0.455, 0.196],
            [0.940, 0.975, 0.131],
        ]
    )
    pla = np.stack([np.interp(x, xp, anchors_p[:, c]) for c in range(3)], axis=1)
    luts["Plasma"] = (pla * 255).astype(np.uint8)

    # Bone — blue-grey tint like X-ray film
    bone_r = np.where(t < 0.75, t * 0.91, 0.91 * t + 0.09 * (t - 0.75) / 0.25)
    bone_g = np.where(
        t < 0.375, t * 0.91, np.where(t < 0.75, t * 0.91, t * 0.91 + 0.05 * (t - 0.375))
    )
    bone_b = np.where(t < 0.375, t * 0.91 + 0.15 * t / 0.375, t * 0.91)
    luts["Bone"] = (np.clip(np.stack([bone_r, bone_g, bone_b], axis=1), 0, 1) * 255).astype(
        np.uint8
    )

    # Jet — classic rainbow
    jet_r = np.where(
        t < 0.35,
        0,
        np.where(t < 0.66, (t - 0.35) / 0.31, np.where(t < 0.89, 1.0, (1.0 - (t - 0.89) / 0.11))),
    )
    jet_g = np.where(
        t < 0.125,
        0,
        np.where(
            t < 0.375,
            (t - 0.125) / 0.25,
            np.where(t < 0.64, 1.0, np.where(t < 0.91, 1.0 - (t - 0.64) / 0.27, 0)),
        ),
    )
    jet_b = np.where(
        t < 0.11,
        0.5 + t / 0.11 * 0.5,
        np.where(t < 0.34, 1.0, np.where(t < 0.65, 1.0 - (t - 0.34) / 0.31, 0)),
    )
    luts["Jet"] = (np.clip(np.stack([jet_r, jet_g, jet_b], axis=1), 0, 1) * 255).astype(np.uint8)

    return luts


# Build once at import time
LUTS: Dict[str, np.ndarray] = _build_luts()
LUT_NAMES = list(LUTS.keys())


# ── Application ────────────────────────────────────────────────────────────────


def apply_lut(gray: np.ndarray, lut_name: str = "Grayscale") -> np.ndarray:
    """
    Map a 2-D uint8 grayscale array through a named LUT.

    Returns a (H, W, 4) uint8 RGBA array suitable for QImage Format_RGBA8888.
    Alpha is always 255 (fully opaque).
    """
    lut = LUTS.get(lut_name, LUTS["Grayscale"])
    rgb = lut[gray]  # (H, W, 3) uint8
    h, w = gray.shape
    rgba = np.empty((h, w, 4), dtype=np.uint8)
    rgba[:, :, :3] = rgb
    rgba[:, :, 3] = 255
    return rgba


def lut_preview_strip(lut_name: str, width: int = 200, height: int = 16) -> np.ndarray:
    """
    Return a (height, width, 4) RGBA array showing the LUT gradient.
    Useful for drawing a preview swatch.
    """
    strip = np.tile(np.arange(256, dtype=np.uint8), (height, 1))  # (height, 256)
    # Scale to requested width
    indices = (np.linspace(0, 255, width)).astype(np.uint8)
    strip = np.tile(indices, (height, 1))
    return apply_lut(strip, lut_name)
