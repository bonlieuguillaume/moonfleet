"""
main.py
-------
Full Moonfleet pipeline orchestrator.

Steps:
  1. Run the SNAP GPT graph on the input S1 product (with or without AOI).
  2. Locate the SNAP object-detection XML report that SNAP always writes to
     ~/.snap/var/log/<product_stem>_Orb_NR_Cal_Spk_TC_THR_object_detection_report.xml
  3. Parse the report into a JSON detection file.
  4. Enrich the JSON with:
       - parameters: every CFAR parameter used (default or custom)
       - coverage:   the AOI polygon if one was given, otherwise the product
                     footprint extracted from the Sentinel-1 manifest.safe.

Output files (both share the same stem):
  outputs/images/<stem>.dim        SNAP processed image
  outputs/detections/<stem>.json   detection JSON for viewer.html

Usage examples:
    python src/main.py --input data_raw/S1A_...B981.SAFE
    python src/main.py --input data_raw/S1A_...B981.zip --aoi "POLYGON ((...))
    python src/main.py --input data_raw/S1A_...B981.SAFE --output mission1 --pfa 7
"""

__version__ = "0.1"

import os
import sys
import json
import argparse
import zipfile
from xml.etree import ElementTree as ET

# ── path setup so we can import sibling modules ──────────────────────────────
_SRC_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SRC_DIR)
sys.path.insert(0, os.path.join(_SRC_DIR, "viewer"))

from naive          import run_snap_graph as _run_with_aoi
from naive_no_aoi   import run_snap_graph as _run_without_aoi
from viewer.parse_detections import parse_detection_xml

# SNAP always writes the detection XML to this directory, regardless of --output
_SNAP_LOG_DIR = os.path.join(os.path.expanduser("~"), ".snap", "var", "log")


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def derive_xml_path(input_file: str) -> str:
    """
    Build the path to the SNAP object-detection XML report.

    SNAP names the report after the input product, appending the processing
    suffix, regardless of the output file name the user chose.
    e.g. S1A_IW_GRDH_..._B981_Orb_NR_Cal_Spk_TC_THR_object_detection_report.xml
    """
    stem = os.path.splitext(os.path.basename(input_file.rstrip("/\\")))[0]
    xml_name = f"{stem}_Orb_NR_Cal_Spk_TC_THR_object_detection_report.xml"
    return os.path.join(_SNAP_LOG_DIR, xml_name)


def get_tile_footprint(input_file: str) -> str | None:
    """
    Extract the product geographic footprint as a WKT polygon from
    the Sentinel-1 manifest.safe (handles both .SAFE directories and .zip).
    Returns None if the footprint cannot be read.
    """
    manifest_content = None
    clean = input_file.rstrip("/\\")

    if os.path.isdir(clean):
        manifest_path = os.path.join(clean, "manifest.safe")
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as fh:
                manifest_content = fh.read()
    elif clean.lower().endswith(".zip"):
        try:
            with zipfile.ZipFile(clean, "r") as z:
                for name in z.namelist():
                    if name.endswith("manifest.safe"):
                        with z.open(name) as fh:
                            manifest_content = fh.read().decode("utf-8")
                        break
        except Exception:
            pass

    if not manifest_content:
        return None

    try:
        root = ET.fromstring(manifest_content)
        ns = {"gml": "http://www.opengis.net/gml"}
        coords_el = root.find(".//gml:coordinates", ns)
        if coords_el is not None:
            # GML coordinates are "lat,lon lat,lon …"; WKT uses "lon lat, …"
            pairs = coords_el.text.strip().split()
            wkt_pts = []
            for pair in pairs:
                lat, lon = pair.split(",")
                wkt_pts.append(f"{float(lon):.6f} {float(lat):.6f}")
            return "POLYGON ((" + ", ".join(wkt_pts) + "))"
    except Exception:
        pass

    return None


def bbox_to_wkt(bbox: dict) -> str:
    """Convert a stats.bbox dict to a rectangular WKT polygon (fallback footprint)."""
    lo_lon, lo_lat = bbox["lon_min"], bbox["lat_min"]
    hi_lon, hi_lat = bbox["lon_max"], bbox["lat_max"]
    return (
        f"POLYGON (("
        f"{lo_lon:.6f} {lo_lat:.6f}, "
        f"{hi_lon:.6f} {lo_lat:.6f}, "
        f"{hi_lon:.6f} {hi_lat:.6f}, "
        f"{lo_lon:.6f} {hi_lat:.6f}, "
        f"{lo_lon:.6f} {lo_lat:.6f}"
        f"))"
    )


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Run the full Moonfleet vessel-detection pipeline."
    )

    # Required
    parser.add_argument(
        "--input", required=True,
        help="Path to the input Sentinel-1 product (.SAFE directory or .zip)"
    )

    # Optional — execution
    parser.add_argument(
        "--gpt",
        default=r"C:\Program Files\esa-snap\bin\gpt.exe",
        help="Path to the SNAP gpt executable (default: C:\\Program Files\\esa-snap\\bin\\gpt.exe)"
    )
    parser.add_argument(
        "--graph", default=None,
        help="Path to the SNAP .xml graph. Auto-selected (CFAR.xml / CFAR_no_aoi.xml) if omitted."
    )
    parser.add_argument(
        "--aoi", default=None,
        help="Area of interest as WKT POLYGON. If omitted, the full scene is processed."
    )
    parser.add_argument(
        "--output", default=None,
        help="Output stem used for both the .dim image and the .json report "
             "(e.g. 'mission1' → outputs/images/mission1.dim + outputs/detections/mission1.json). "
             "Defaults to 'detections'."
    )

    # Optional — CFAR detection parameters
    parser.add_argument("--target-window",       type=float, default=50,      help="CFAR target window size in meters (default: 50)")
    parser.add_argument("--guard-window",        type=float, default=500.0,   help="CFAR guard window size in meters (default: 500)")
    parser.add_argument("--background-window",   type=float, default=800.0,   help="CFAR background window size in meters (default: 800)")
    parser.add_argument("--pfa",                 type=float, default=6.5,     help="Probability of false alarm 10^(-pfa) (default: 6.5)")
    parser.add_argument("--estimate-background", default="false", choices=["true", "false"],
                        help="Locally estimate background statistics (default: false)")
    parser.add_argument("--min-target",          type=float, default=30.0,    help="Minimum target size in meters (default: 30)")
    parser.add_argument("--max-target",          type=float, default=500.0,   help="Maximum target size in meters (default: 500)")
    parser.add_argument("--shoreline-extension", type=int,   default=0,       help="Land-sea mask shoreline extension in pixels (default: 0)")

    args = parser.parse_args()

    root_dir  = os.path.abspath(os.path.join(_SRC_DIR, ".."))
    graphs_dir = os.path.join(root_dir, "graphs")
    stem      = args.output if args.output else "detections"
    dim_path  = os.path.join(root_dir, "outputs", "images",     f"{stem}.dim")
    json_path = os.path.join(root_dir, "outputs", "detections", f"{stem}.json")

    os.makedirs(os.path.dirname(dim_path),  exist_ok=True)
    os.makedirs(os.path.dirname(json_path), exist_ok=True)

    # Auto-select graph
    if args.graph is None:
        args.graph = os.path.join(graphs_dir, "CFAR.xml" if args.aoi else "CFAR_no_aoi.xml")

    # Shared CFAR kwargs
    cfar_kwargs = dict(
        target_window       = args.target_window,
        guard_window        = args.guard_window,
        background_window   = args.background_window,
        pfa                 = args.pfa,
        estimate_background = args.estimate_background,
        min_target_size     = args.min_target,
        max_target_size     = args.max_target,
        shoreline_extension = args.shoreline_extension,
    )

    # ── Step 1: SNAP processing ───────────────────────────────────────────────
    print("\n[1/3] Running SNAP GPT graph...")
    if args.aoi:
        _run_with_aoi(args.gpt, args.graph, args.input, args.aoi, dim_path, **cfar_kwargs)
    else:
        _run_without_aoi(args.gpt, args.graph, args.input, dim_path, **cfar_kwargs)

    # ── Step 2: Parse detection report ───────────────────────────────────────
    print("\n[2/3] Parsing SNAP detection report...")
    xml_path = derive_xml_path(args.input)
    if not os.path.exists(xml_path):
        print(f"Error: SNAP report not found at:\n  {xml_path}", file=sys.stderr)
        print("Make sure the SNAP graph ran to completion.", file=sys.stderr)
        sys.exit(1)

    data = parse_detection_xml(xml_path)

    # ── Step 3: Enrich and write JSON ─────────────────────────────────────────
    print("\n[3/3] Writing detection JSON...")

    # Store every CFAR parameter so the viewer can display them
    data["parameters"] = {
        "target_window_m":       args.target_window,
        "guard_window_m":        args.guard_window,
        "background_window_m":   args.background_window,
        "pfa":                   args.pfa,
        "estimate_background":   args.estimate_background,
        "min_target_size_m":     args.min_target,
        "max_target_size_m":     args.max_target,
        "shoreline_extension_px": args.shoreline_extension,
    }

    # Store the geographic coverage so the viewer can draw it on the map
    if args.aoi:
        data["coverage"] = {"type": "aoi", "wkt": args.aoi}
    else:
        footprint = get_tile_footprint(args.input)
        if footprint:
            data["coverage"] = {"type": "tile_footprint", "wkt": footprint}
        else:
            # Fallback: bounding box of detections
            data["coverage"] = {
                "type": "tile_footprint",
                "wkt": bbox_to_wkt(data["stats"]["bbox"]),
            }

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)

    # ── Summary ───────────────────────────────────────────────────────────────
    s = data["stats"]
    print(f"\nDone.")
    print(f"  Detections : {s['total_detections']}")
    print(f"  Length     : {s['length_min_m']:.0f} m – {s['length_max_m']:.0f} m  (mean {s['length_mean_m']:.0f} m)")
    print(f"  Classes    : {s['by_class']}")
    print(f"  Coverage   : {data['coverage']['type']}")
    print(f"  JSON       : {json_path}")


if __name__ == "__main__":
    main()
