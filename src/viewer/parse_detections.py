import xml.etree.ElementTree as ET
import json
import argparse
import os
import sys
from datetime import datetime

"""
parse_detections.py
-------------------
Parses a SNAP Object Detection Report XML and outputs a detections.json
ready to be consumed by viewer.html.

Usage:
    python parse_detections.py <path_to_xml> [--output detections.json]

Example:
    python parse_detections.py "C:\\Users\\guigu\\.snap\\var\\log\\...xml"
    python parse_detections.py report.xml --output data/detections.json
"""


def parse_filename_metadata(xml_path: str) -> dict:
    """
    Extract acquisition metadata from the SNAP report filename.
    Example filename pattern:
      S1A_IW_GRDH_1SDV_20260107T233152_20260107T233217_062668_07DB60_...xml
    """
    basename = os.path.basename(xml_path)
    parts = basename.split("_")
    metadata = {
        "satellite": None,
        "mode": None,
        "product_type": None,
        "start_time": None,
        "stop_time": None,
        "orbit": None,
        "source_file": basename,
    }
    try:
        metadata["satellite"] = parts[0]          # S1A
        metadata["mode"] = parts[1]               # IW
        metadata["product_type"] = parts[2]       # GRDH
        raw_start = parts[4]                      # 20260107T233152
        raw_stop  = parts[5]                      # 20260107T233217
        metadata["start_time"] = datetime.strptime(raw_start, "%Y%m%dT%H%M%S").strftime("%Y-%m-%d %H:%M:%S UTC")
        metadata["stop_time"]  = datetime.strptime(raw_stop,  "%Y%m%dT%H%M%S").strftime("%Y-%m-%d %H:%M:%S UTC")
        metadata["orbit"] = int(parts[6])
    except (IndexError, ValueError):
        pass  # metadata remains partial — not a blocker
    return metadata


def classify_vessel(length_m: float) -> str:
    """Rough vessel class based on detected length."""
    if length_m < 50:
        return "small"       # Small craft / fishing
    elif length_m < 150:
        return "medium"      # Coastal / feeder
    elif length_m < 250:
        return "large"       # Cargo / tanker
    else:
        return "very_large"  # VLCC / large bulk carrier


def parse_detection_xml(xml_path: str) -> dict:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    targets = root.findall(".//target")
    features = []

    for t in targets:
        lat    = float(t.get("Detected_lat"))
        lon    = float(t.get("Detected_lon"))
        raw_width  = float(t.get("Detected_width"))
        raw_length = float(t.get("Detected_length"))
        length = max(raw_width, raw_length)  # In the report length and width depend on the orientation of the vessel
        width  = min(raw_width, raw_length)  # So we take the max as length and min as width
        px_x   = int(t.get("Detected_x"))
        px_y   = int(t.get("Detected_y"))

        features.append({
            "lat": round(lat, 7),
            "lon": round(lon, 7),
            "width_m": width,
            "length_m": length,
            "px_x": px_x,
            "px_y": px_y,
            "vessel_class": classify_vessel(length),
        })

    # Summary stats
    lengths = [f["length_m"] for f in features]
    lats    = [f["lat"] for f in features]
    lons    = [f["lon"] for f in features]

    return {
        "metadata": parse_filename_metadata(xml_path),
        "stats": {
            "total_detections": len(features),
            "length_min_m": min(lengths),
            "length_max_m": max(lengths),
            "length_mean_m": round(sum(lengths) / len(lengths), 1),
            "bbox": {
                "lat_min": min(lats), "lat_max": max(lats),
                "lon_min": min(lons), "lon_max": max(lons),
            },
            "by_class": {
                cls: sum(1 for f in features if f["vessel_class"] == cls)
                for cls in ["small", "medium", "large", "very_large"]
            }
        },
        "detections": features,
    }


def main():
    parser = argparse.ArgumentParser(description="Parse SNAP detection report XML to JSON.")
    parser.add_argument("xml", help="Path to the SNAP object detection report XML")
    parser.add_argument("--output", default=None, help="Output filename stem (saved to detections/<name>.json, default: detections.json)")
    args = parser.parse_args()

    if not os.path.exists(args.xml):
        print(f"Error: file not found: {args.xml}", file=sys.stderr)
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))
    stem = args.output if args.output else "detections"
    output_path = os.path.join(root_dir, "outputs", "detections", f"{stem}.json")

    print(f"Parsing {args.xml} ...")
    data = parse_detection_xml(args.xml)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Done — {data['stats']['total_detections']} detections written to {output_path}")
    stats = data["stats"]
    print(f"  Length: {stats['length_min_m']:.0f}m – {stats['length_max_m']:.0f}m (mean {stats['length_mean_m']:.0f}m)")
    print(f"  Classes: {stats['by_class']}")


if __name__ == "__main__":
    main()
