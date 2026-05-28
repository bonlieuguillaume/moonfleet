# Moonfleet — Technical Reference

## Description

Moonfleet is a Sentinel-1 SAR vessel-detection pipeline that orchestrates ESA SNAP's Graph Processing Tool (GPT) from Python. It ingests a Sentinel-1 GRD product (`.SAFE` directory or `.zip`), runs a CFAR-based detection graph (orbit correction → thermal noise removal → calibration → speckle filter → terrain correction → land-sea mask → adaptive thresholding → object discrimination), parses the resulting SNAP object-detection XML report, and produces a JSON detection file rendered by a Leaflet-based local web viewer.

## Project structure

```
moonfleet/
├── graphs/
│   ├── CFAR.xml                       # SNAP graph with AOI subset
│   └── CFAR_no_aoi.xml                # SNAP graph for full-scene processing
├── src/
│   ├── main.py                        # Full pipeline orchestrator (GPT + parse + enrich)
│   ├── naive.py                       # GPT wrapper with AOI parameter
│   ├── naive_no_aoi.py                # GPT wrapper without AOI
│   └── viewer/
│       ├── parse_detections.py        # SNAP XML → JSON detection report
│       ├── serve.py                   # Local HTTP server for the viewer
│       └── viewer.html                # Leaflet web viewer
├── data_raw/                          # (gitignored) Sentinel-1 input products
├── outputs/                           # (gitignored) processing outputs
│   ├── images/                        # .dim BEAM-DIMAP processed scenes
│   └── detections/                    # .json detection reports
├── moonfleet_env_light.yml            # Conda environment definition
└── README_TECHNICAL.md
```

## Requirements

| Item | Specification |
|---|---|
| OS | Windows 10/11 (primary), Linux compatible |
| Python | 3.11 |
| ESA SNAP | 13 (with Sentinel-1 Toolbox) |
| RAM | ≥ 16 GB recommended (for tile cache) |
| Disk | ≥ 20 GB free (raw S1 products are ~1 GB each, intermediate `.dim` outputs ~1–3 GB) |
| Network | Required on first run (orbit files, DEM, SRTM auxiliary downloads) |

## Installation

1. **Install Miniforge** from the [official releases page](https://github.com/conda-forge/miniforge/releases).
2. **Initialize conda for PowerShell** and restart the terminal:
   ```powershell
   conda init powershell
   ```
3. **Clone the repository**:
   ```powershell
   git clone <repo-url> moonfleet
   cd moonfleet
   ```
4. **Create the environment** from the lightweight specification:
   ```powershell
   mamba env create -f moonfleet_env_light.yml
   ```
5. **Activate the environment**:
   ```powershell
   mamba activate moonfleet
   ```
6. **Select the interpreter in VS Code**: `Ctrl+Shift+P` → *Python: Select Interpreter* → choose the `moonfleet` env.

## Deployment on a new machine — checklist

The following values are hardcoded and must be reviewed when deploying to a new machine.

### 1. SNAP `gpt.exe` path

Default in **three files**: `src/main.py`, `src/naive.py`, `src/naive_no_aoi.py`:

```python
default=r"C:\Program Files\esa-snap\bin\gpt.exe"
```

Override per invocation with `--gpt /path/to/gpt`, or edit the defaults.
Linux: typically `/opt/snap/bin/gpt` or `~/snap/bin/gpt`.

### 2. Tile cache `-c 16384M`

In `src/naive.py` and `src/naive_no_aoi.py`. Set to **~50 % of available RAM**:

| Machine RAM | Recommended `-c` |
|---|---|
| 16 GB | `8192M` |
| 32 GB | `16384M` |
| 64 GB | `32768M` |

### 3. Threads `-q 16`

In `src/naive.py` and `src/naive_no_aoi.py`. Set to the **physical core count** of the host CPU.

### 4. SNAP auxiliary downloads (first-run, requires internet)

On the first run, SNAP will fetch and cache the following resources to `~/.snap/auxdata/`:

- **Sentinel-1 Precise Orbits** (`Apply-Orbit-File` operator)
- **Copernicus 30 m Global DEM** (`Terrain-Correction` operator)
- **SRTM** tiles (`Land-Sea-Mask` operator)

Subsequent runs are offline-capable.

## Usage — `main.py` CLI reference

```
python src/main.py --input <path> [options]
```

| Argument | Type | Default | Description |
|---|---|---|---|
| `--input` | path | *required* | Sentinel-1 product (`.SAFE` dir or `.zip`) |
| `--gpt` | path | `C:\Program Files\esa-snap\bin\gpt.exe` | SNAP `gpt` executable |
| `--graph` | path | auto-selected | Override SNAP XML graph (defaults to `CFAR.xml` if `--aoi`, else `CFAR_no_aoi.xml`) |
| `--aoi` | WKT string | `None` | AOI as `POLYGON ((...))`; if omitted, full scene is processed |
| `--output` | string | `detections` | Output stem for both `.dim` and `.json` |
| `--target-window` | float | `50` | CFAR target window size (m) |
| `--guard-window` | float | `500.0` | CFAR guard window size (m) |
| `--background-window` | float | `800.0` | CFAR background window size (m) |
| `--pfa` | float | `6.5` | Probability of false alarm exponent: PFA = 10⁻ˣ |
| `--estimate-background` | `true`/`false` | `false` | Locally estimate background statistics |
| `--min-target` | float | `30.0` | Minimum target size (m) |
| `--max-target` | float | `500.0` | Maximum target size (m) |
| `--shoreline-extension` | int | `0` | Land-sea mask shoreline extension (m) |

### Examples

**1. Full scene, default parameters**
```powershell
python src/main.py --input data_raw/S1A_IW_GRDH_1SDV_20260107T233152_..._B981.SAFE
```

**2. With AOI and custom output stem**
```powershell
python src/main.py `
  --input data_raw/S1A_..._B981.zip `
  --aoi "POLYGON ((1.2 43.3, 1.8 43.3, 1.8 43.6, 1.2 43.6, 1.2 43.3))" `
  --output mission1_toulouse
```

**3. Custom CFAR parameters**
```powershell
python src/main.py `
  --input data_raw/S1A_..._B981.SAFE `
  --pfa 7.0 `
  --min-target 50 `
  --max-target 400 `
  --target-window 40 `
  --shoreline-extension 100
```

### Standalone modules

- **`naive.py`** — Run the AOI graph only (no JSON parsing):
  ```powershell
  python src/naive.py --graph graphs/CFAR.xml --input <product> --aoi "POLYGON ((...))" --output scene1
  ```
- **`naive_no_aoi.py`** — Same, without AOI:
  ```powershell
  python src/naive_no_aoi.py --graph graphs/CFAR_no_aoi.xml --input <product> --output scene1
  ```
- **`parse_detections.py`** — Parse an existing SNAP XML report to JSON:
  ```powershell
  python src/viewer/parse_detections.py "C:\Users\<user>\.snap\var\log\<scene>_..._object_detection_report.xml" --output scene1
  ```

## SNAP graphs

### `graphs/CFAR.xml` (with AOI)

Operator chain:
`Read → Apply-Orbit-File → ThermalNoiseRemoval → Calibration → Speckle-Filter → Terrain-Correction → Subset → Land-Sea-Mask → AdaptiveThresholding → Object-Discrimination → Write`

Externalized parameters: `${input}`, `${aoi}`, `${output}`, `${target_window}`, `${guard_window}`, `${background_window}`, `${pfa}`, `${estimate_background}`, `${min_target_size}`, `${max_target_size}`, `${shoreline_extension}`. Key fixed settings: precise orbits with `continueOnFail=true`, Lee Sigma speckle filter (7×7 window), Copernicus 30 m DEM, 10 m pixel spacing, gamma-nought calibration, SRTM-based land mask.

### `graphs/CFAR_no_aoi.xml` (full scene)

Identical operator chain **minus the `Subset` node**. The `Land-Sea-Mask` consumes `Terrain-Correction` directly instead of `Subset`, and the `${aoi}` parameter is not used. Use this graph when no AOI is supplied; processing time and memory footprint grow accordingly with the full scene size.

## Output files

Each pipeline run produces two files sharing the same stem (`--output` or `detections`):

```
outputs/images/<stem>.dim          # SNAP BEAM-DIMAP processed image (+ <stem>.data/ folder)
outputs/detections/<stem>.json     # Detection report consumed by viewer.html
```

### JSON schema

```json
{
  "metadata":   { ... },
  "parameters": { ... },
  "coverage":   { ... },
  "stats":      { ... },
  "detections": [ ... ]
}
```

**`metadata`** — parsed from the source filename:
| Field | Description |
|---|---|
| `satellite` | e.g. `S1A`, `S1B` |
| `mode` | acquisition mode (e.g. `IW`) |
| `product_type` | e.g. `GRDH` |
| `start_time`, `stop_time` | UTC timestamps (`YYYY-MM-DD HH:MM:SS UTC`) |
| `orbit` | absolute orbit number (int) |
| `source_file` | original XML report filename |

**`parameters`** — every CFAR value used for the run: `target_window_m`, `guard_window_m`, `background_window_m`, `pfa`, `estimate_background`, `min_target_size_m`, `max_target_size_m`, `shoreline_extension_m`.

**`coverage`** — geographic scope drawn by the viewer:
| Field | Description |
|---|---|
| `type` | `"aoi"` if user supplied an AOI, else `"tile_footprint"` |
| `wkt` | WKT polygon (AOI verbatim, footprint from `manifest.safe`, or bbox fallback) |

**`stats`** — aggregate metrics:
| Field | Description |
|---|---|
| `total_detections` | count of vessels |
| `length_min_m`, `length_max_m`, `length_mean_m` | length distribution |
| `bbox` | `{lat_min, lat_max, lon_min, lon_max}` |
| `by_class` | counts per `small` / `medium` / `large` / `very_large` |

**`detections[]`** — one entry per target:
| Field | Description |
|---|---|
| `lat`, `lon` | WGS84 coordinates (7 decimals) |
| `length_m`, `width_m` | normalized so `length = max(raw_w, raw_l)` |
| `px_x`, `px_y` | pixel position in the terrain-corrected raster |
| `vessel_class` | `small` (<50 m