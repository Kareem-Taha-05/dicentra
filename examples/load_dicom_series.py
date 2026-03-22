"""
Example: load a DICOM series from a folder and print slice info.

Run:
    python examples/load_dicom_series.py path/to/folder/
"""

import sys

sys.path.insert(0, ".")

from app.data.dicom_model import load_series_from_folder


def main():
    if len(sys.argv) < 2:
        print("Usage: python examples/load_dicom_series.py <folder>")
        sys.exit(1)

    folder = sys.argv[1]
    series_list = load_series_from_folder(folder)

    print(f"Found {len(series_list)} series in {folder}")
    for s in series_list:
        print(
            f"  [{s.modality}] {s.series_description or 'No description'}" f" — {s.n_slices} slices"
        )


if __name__ == "__main__":
    main()
