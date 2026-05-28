"""
generate_readme.py
------------------
Generates two README files using the Claude API:

  README.md             — showcase README: visual, feature-focused, with screenshot placeholders
  README_TECHNICAL.md   — technical reference: installation, deployment, CLI, architecture
"""

import anthropic
import os

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR     = os.path.join(BASE_DIR, "src")
GRAPHS_DIR  = os.path.join(BASE_DIR, "graphs")

OUTPUT_SHOWCASE  = os.path.join(BASE_DIR, "README.md")
OUTPUT_TECHNICAL = os.path.join(BASE_DIR, "README_TECHNICAL.md")


# ─── FILE COLLECTION ─────────────────────────────────────────────

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def collect_project_files(src_dir: str, graphs_dir: str) -> dict:
    """
    Collect Python sources and SNAP XML graphs.
    viewer.html is excluded (too long, not needed for README context).
    """
    files = {}

    # Top-level src/ Python files
    for fname in os.listdir(src_dir):
        if fname.endswith(".py"):
            files[f"src/{fname}"] = read_file(os.path.join(src_dir, fname))

    # src/viewer/ Python files (parse_detections, serve — not the HTML)
    viewer_dir = os.path.join(src_dir, "viewer")
    if os.path.isdir(viewer_dir):
        for fname in os.listdir(viewer_dir):
            if fname.endswith(".py"):
                files[f"src/viewer/{fname}"] = read_file(os.path.join(viewer_dir, fname))

    # SNAP graph XML files
    for fname in os.listdir(graphs_dir):
        if fname.endswith(".xml"):
            files[f"graphs/{fname}"] = read_file(os.path.join(graphs_dir, fname))

    return files


def build_files_block(files: dict) -> str:
    block = ""
    for filepath, content in files.items():
        ext = filepath.rsplit(".", 1)[-1]
        block += f"\n\n### {filepath}\n```{ext}\n{content}\n```"
    return block


# ─── PROMPTS ─────────────────────────────────────────────────────

PROMPT_SHOWCASE = """\
You are writing the main README.md for a GitHub repository called **Moonfleet** \
— a Sentinel-1 SAR vessel detection pipeline.

This README is the project's front page. It should immediately tell a visitor \
what Moonfleet does, impress them with results, and show off its features. \
It is NOT a technical manual — keep installation details minimal.

Write in English. Use GitHub-flavored Markdown.

Include these sections in this exact order:

1. **Title + one-line tagline**
   Make it punchy, e.g. "Detect vessels anywhere in the ocean from a single command."

2. **Badges**
   Python version (3.11), License (MIT), SNAP (13).

3. **What it does** (3–4 sentences)
   What problem it solves, what satellite data it uses, what it produces.
   Mention the end-to-end nature: one command from raw Sentinel-1 to an \
   interactive web map.

4. **Screenshots / Results** — this is the centrepiece.
   Include 4 Markdown image references. Use paths of the form:
     `data/data_raw/hormuz/displays/<your_chosen_name>.png`
   Choose clear, lowercase, hyphenated names that describe what the screenshot shows \
   (e.g. `viewer-overview.png`, `hormuz-detections-cluster.png`, \
   `custom-class-panel.png`, `cfar-result-zoom.png`).
   Add a short italic caption under each image.
   The user will take actual screenshots and rename them to match these paths exactly.

5. **Key features** (bullet list)
   Focus on what makes it useful and unique:
   - one-command pipeline (SNAP + parsing + JSON in one call)
   - interactive web viewer with dark maritime theme
   - custom vessel classes with per-class length/width intervals
   - length & width range sliders for live filtering
   - AOI support or full-scene processing
   - coverage overlay (AOI polygon or tile footprint) on the map
   - run parameters stored in the JSON and displayed in the viewer
   - multi-report support with a dropdown selector

6. **How it works** (numbered, high-level, 5 steps max)
   Feed a Sentinel-1 product → SNAP GPT runs CFAR → parse detection XML → \
   JSON enriched with parameters and coverage → open the interactive viewer.

7. **Quick start**
   Three commands only: clone, create env (`mamba env create`), run `main.py`. \
   No detailed flags — just enough to see it work.

Do NOT include detailed installation instructions, dependency tables, \
graph internals, or deployment notes. Those go in README_TECHNICAL.md.

Project files for context:
{files_block}"""


PROMPT_TECHNICAL = """\
You are a technical writer. Generate **README_TECHNICAL.md** for the Moonfleet \
project — a Sentinel-1 SAR vessel detection pipeline using ESA SNAP GPT.

This document targets developers and analysts who want to install, configure, \
run, or extend the system. Be precise, complete, and concise.

Write in English. Use GitHub-flavored Markdown.

Include these sections in this exact order:

1. **Title**
   "Moonfleet — Technical Reference"

2. **Short description** (2–3 sentences, technical angle)
   What pipeline stages, what formats in/out, what tools (SNAP, Python, Leaflet).

3. **Project structure**
   Directory tree with a one-line description per file/folder. \
   Mark gitignored folders (`data_raw/`, `outputs/`) as such.

4. **Requirements**
   OS (Windows 10/11, Linux compatible), Python 3.11, SNAP 13, \
   RAM (≥16 GB recommended for tile cache), disk space.

5. **Installation**
   Step by step:
   - Install Miniforge (link to releases page)
   - `conda init powershell` + restart terminal
   - Clone the repo
   - `mamba env create -f moonfleet_env_light.yml`
   - `mamba activate moonfleet`
   - Select the interpreter in VS Code

6. **Deployment on a new machine — checklist**
   Hardcoded values to adapt:
   - `gpt.exe` default path (3 files: naive.py, naive_no_aoi.py, main.py)
   - Tile cache `-c 16384M` → adapt to ~50% of available RAM
   - Threads `-q 16` → adapt to physical core count
   SNAP auxiliary downloads that require internet on first run: \
   Sentinel-1 precise orbits, Copernicus 30m DEM, SRTM (land-sea mask).

7. **Usage — full CLI reference for main.py**
   Table or list of every argument with type, default, and description. \
   Then 3 concrete example invocations:
   - full scene, default params
   - with AOI and custom output name
   - custom CFAR params (pfa, min-target, etc.)
   Also briefly document running naive.py / naive_no_aoi.py and \
   parse_detections.py standalone.

8. **SNAP graphs**
   One paragraph per XML (CFAR.xml, CFAR_no_aoi.xml): \
   operator chain, what each parameter controls, difference between the two.

9. **Output files**
   What is produced and where:
   - `outputs/images/<stem>.dim` — SNAP BEAM-DIMAP image
   - `outputs/detections/<stem>.json` — detection report schema: \
     `metadata`, `parameters`, `coverage`, `stats`, `detections[]`
   Include the JSON field descriptions.

10. **Web viewer**
    How to launch (`python src/viewer/serve.py`), what URL to open. \
    Document each sidebar section: vessel classes (default + custom mode), \
    filters (length/width range sliders with keyboard input), \
    statistics panel, run parameters panel, coverage button, \
    basemap switcher, marker size, detection list with collapsible/resizable split.

11. **Dependencies table**
    Columns: package | version | purpose.
    Include Python stdlib modules used (xml, subprocess, zipfile…) \
    and conda packages from moonfleet_env_light.yml.

Project files for context:
{files_block}"""


# ─── GENERATION ──────────────────────────────────────────────────

def generate_readme(prompt: str, output_path: str, label: str) -> None:
    client = anthropic.Anthropic()
    print(f"Generating {label}...")
    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    content = message.content[0].text
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  → {output_path}")


# ─── MAIN ────────────────────────────────────────────────────────

if __name__ == "__main__":
    files       = collect_project_files(SRC_DIR, GRAPHS_DIR)
    files_block = build_files_block(files)

    generate_readme(
        PROMPT_SHOWCASE.format(files_block=files_block),
        OUTPUT_SHOWCASE,
        "showcase README  → README.md"
    )
    generate_readme(
        PROMPT_TECHNICAL.format(files_block=files_block),
        OUTPUT_TECHNICAL,
        "technical README → README_TECHNICAL.md"
    )

    print("\nDone.")
