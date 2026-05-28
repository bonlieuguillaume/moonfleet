# 🌊 Moonfleet

**Detect vessels anywhere in the ocean from a single command.**

![Python](https://img.shields.io/badge/python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![SNAP](https://img.shields.io/badge/SNAP-13-orange)

## What it does

Moonfleet is an end-to-end vessel detection pipeline built on **Sentinel-1 SAR** imagery. From a single raw `.SAFE` product (or `.zip`), it runs a full SNAP processing graph — orbit correction, calibration, speckle filtering, terrain correction, land masking and CFAR-based ship detection — then parses the results into an enriched JSON report. The output is immediately viewable in a built-in interactive web map, complete with detection markers, vessel classes and live filters. **One command. From satellite tile to interactive map.**

## Screenshots

![Viewer overview](data/data_raw/hormuz/display/viewer-overview.png)
*The Moonfleet viewer — dark maritime theme, detection markers, and run metadata at a glance.*

![Detections cluster over the Strait of Hormuz](data/data_raw/hormuz/display/hormuz-detections-cluster.png)
*A dense cluster of vessel detections over the Strait of Hormuz, with the tile footprint overlaid in cyan.*

![Custom vessel class panel](data/data_raw/hormuz/display/custom-class-panel.png)
*Define your own vessel classes with per-class length and width intervals — fully editable from the UI.*

![CFAR detection zoom](data/data_raw/hormuz/display/cfar-result-zoom.png)
*Zoomed-in view of CFAR detections — each marker shows length, width and inferred class.*

## Key features

- 🛰️ **One-command pipeline** — SNAP processing, XML parsing and JSON enrichment in a single call.
- 🌐 **Interactive web viewer** with a dark maritime theme, built for quick visual inspection.
- 🏷️ **Custom vessel classes** with per-class length and width intervals, editable on the fly.
- 🎚️ **Live filtering** with length and width range sliders.
- 🗺️ **AOI support or full-scene processing** — restrict to a WKT polygon or process the whole tile.
- 📐 **Coverage overlay** — the AOI polygon or full tile footprint is drawn directly on the map.
- ⚙️ **Run parameters embedded** in every JSON report and displayed in the viewer for full traceability.
- 📂 **Multi-report support** with a dropdown selector to switch between missions.

## How it works

1. **Feed** a Sentinel-1 `.SAFE` product (directory or zip) to `main.py`.
2. **SNAP GPT** runs the full processing graph and applies a CFAR detector.
3. **Parse** the SNAP object-detection XML report into structured detections.
4. **Enrich** the JSON with CFAR parameters and geographic coverage (AOI or tile footprint).
5. **Open** the interactive viewer and explore your detections.

## Quick start

```bash
# 1. Clone
git clone https://github.com/yourname/moonfleet.git
cd moonfleet

# 2. Create the environment
mamba env create -f environment.yml
mamba activate moonfleet

# 3. Run the pipeline
python src/main.py --input path/to/S1A_IW_GRDH_xxx.SAFE
```

Then launch the viewer:

```bash
python src/viewer/serve.py --open
```

---

> For installation details, graph internals and configuration, see [`README_TECHNICAL.md`](README_TECHNICAL.md).