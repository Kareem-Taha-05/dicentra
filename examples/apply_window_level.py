"""
Example: apply Window/Level to a DICOM file and save as PNG.

Run:
    python examples/apply_window_level.py file.dcm output.png --width 80 --center 40
"""
import sys
import argparse
sys.path.insert(0, ".")

import numpy as np
from PIL import Image
from app.data.dicom_model import DicomModel
from app.logic.image_processor import apply_window_level

def main():
    p = argparse.ArgumentParser()
    p.add_argument("input",  help="DICOM file path")
    p.add_argument("output", help="Output PNG path")
    p.add_argument("--width",  type=float, default=400, help="Window width")
    p.add_argument("--center", type=float, default=40,  help="Window center (level)")
    args = p.parse_args()

    model = DicomModel()
    model.load(args.input)

    ds        = model.dataset
    slope     = float(getattr(ds, "RescaleSlope",     1.0))
    intercept = float(getattr(ds, "RescaleIntercept", 0.0))

    raw = model.frames[0].astype(np.float32)
    hu  = raw * slope + intercept
    img = apply_window_level(hu, args.width, args.center)

    Image.fromarray(img).save(args.output)
    print(f"Saved {args.output}  (W={args.width}  L={args.center})")

if __name__ == "__main__":
    main()
