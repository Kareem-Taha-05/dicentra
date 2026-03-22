"""
Example: load a single DICOM file and print basic metadata.

Run:
    python examples/load_dicom_file.py path/to/file.dcm
"""

import sys

sys.path.insert(0, ".")

from app.data.dicom_model import DicomModel


def main():
    if len(sys.argv) < 2:
        print("Usage: python examples/load_dicom_file.py <file.dcm>")
        sys.exit(1)

    path = sys.argv[1]
    model = DicomModel()
    model.load(path)

    print(f"Loaded: {path}")
    print(f"Frames: {model.frame_count}")
    print(f"Multiframe: {model.is_multiframe}")

    ds = model.dataset
    for tag in ("PatientName", "StudyDate", "Modality", "Rows", "Columns"):
        val = getattr(ds, tag, "N/A")
        print(f"  {tag}: {val}")


if __name__ == "__main__":
    main()
