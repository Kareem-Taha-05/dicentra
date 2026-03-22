# Usage Guide

## Window / Level

Window/Level (W/L) is the DICOM way of controlling image contrast and brightness.

- **W (Window Width)** — the range of HU values mapped to the full grey scale.  
  Narrow W = high contrast between tissues. Wide W = everything compressed to mid-grey.
- **L (Level / Center)** — the HU value that maps to 50% grey.  
  Moving L left (lower) = brighter image for typical soft tissue. Moving right = darker.

On load, Dicentra auto-computes W/L from the 1st–99th percentile of the middle slice, so the full content of the file is always visible immediately.

## Colourmap LUTs

The swatch row beneath the image canvas selects the colour lookup table:

| LUT | Use |
|-----|-----|
| Grayscale | Standard clinical viewing |
| Inverted | Bone on dark background |
| Hot | Temperature / perfusion maps |
| Cool | Alternative contrast |
| Viridis | Perceptually uniform, accessible |
| Plasma | High-contrast quantitative maps |
| Bone | Radiographic emulation |
| Jet | Legacy scientific visualisation |

## Metadata browser

The **Metadata** tab shows all DICOM tags. Use the category chips to filter:

- **Patient** — demographics, DOB, sex, weight
- **Study** — UIDs, accession number, dates
- **Modality** — acquisition parameters (TR, TE, kVP, etc.)
- **Equipment** — manufacturer, institution, physicians
- **Image** — orientation, position, W/L, rescale
- **Pixel Data** — rows, columns, bits, pixel spacing

Type in the search box to filter by tag name or keyword.

## Anonymisation

In the **Metadata** tab, click **🔒 Anonymize**. Enter a prefix — all patient-identifying fields are replaced with `{prefix}_Patient`, `{prefix}_ID`, etc. Save to a new file.
