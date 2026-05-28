import subprocess
import os
import argparse
import sys

def run_snap_graph(gpt_path, graph_xml, input_file, aoi, output_file,
                   target_window=50, guard_window=500.0, background_window=800.0,
                   pfa=6.5, estimate_background="false",
                   min_target_size=30.0, max_target_size=500.0, shoreline_extension=0):
    """
    Executes a SNAP XML graph using the Graph Processing Tool (GPT).

    This function wraps the GPT command-line interface, allowing you to trigger
    complex Remote Sensing workflows from Python without using the snappy library.
    It passes the input and output file paths as external parameters.

    Args:
        gpt_path (str): Absolute path to the SNAP gpt executable.
        graph_xml (str): Path to the .xml file containing the processing graph.
        aoi (str): Area of interest as WKT geometry (e.g. POLYGON ((...))).
        input_file (str): Path to the input satellite data (e.g., .SAFE, .zip).
        output_file (str): Path where the processed output should be saved.
        target_window (float): CFAR target window size in meters (default: 50).
        guard_window (float): CFAR guard window size in meters (default: 500).
        background_window (float): CFAR background window size in meters (default: 800).
        pfa (float): Probability of false alarm threshold (default: 6.5).
        estimate_background (str): Locally estimate background statistics — "true"/"false" (default: "false").
        min_target_size (float): Minimum target size in meters to keep (default: 30).
        max_target_size (float): Maximum target size in meters to keep (default: 500).
        shoreline_extension (int): Land-sea mask shoreline extension in meters (default: 0).

    Returns:
        str: The standard output of the process if successful.
        None: If the process fails.

    Raises:
        FileNotFoundError: If the gpt_path does not exist on the system.
    """
    # Verify that the GPT executable exists
    if not os.path.exists(gpt_path):
        raise FileNotFoundError(f"GPT tool not found at: {gpt_path}")

    # Build the command line arguments
    # Use a list instead of a single string because it's safer
    # It prevents "command injection" and handles spaces in file paths automatically
    # -e: Provides detailed error stack traces
    # -c: Tile cache: GPT CLI doesn't read the snap.conf, so we set it here to avoid "Out of Memory" errors
    # -q: Number of threads: GPT CLI doesn't read the snap.conf, so we set it here to speed up processing on multi-core machines
    # -Pname=value: Sets a processing parameter (referenced as ${name} in the XML)
    command = [
        gpt_path,
        graph_xml,
        "-e",
        "-c", "16384M",  
        "-q", "16",
        f"-Pinput={input_file}",
        f"-Paoi={aoi}",
        f"-Poutput={output_file}",
        f"-Ptarget_window={target_window}",
        f"-Pguard_window={guard_window}",
        f"-Pbackground_window={background_window}",
        f"-Ppfa={pfa}",
        f"-Pestimate_background={estimate_background}",
        f"-Pmin_target_size={min_target_size}",
        f"-Pmax_target_size={max_target_size}",
        f"-Pshoreline_extension={shoreline_extension}",
    ]

    print(f"Starting processing: {os.path.basename(input_file)}")
   
    try:
        # Execute the process
        # check=True: Raises CalledProcessError if return code is non-zero
        # stdout: captures the normal messages SNAP prints (like "Processing 10%...")
        # stderr: captures error messages
        process = subprocess.run(
            command,
            check=True,
            # stdout=subprocess.PIPE,
            # stderr=subprocess.PIPE,
            text=True
        )  
        print("Processing completed successfully.")
        return process.stdout

    except subprocess.CalledProcessError as e:
        # Capture and display the Java/SNAP error logs
        print(f"Error during graph execution:\n{e.stderr}", file=sys.stderr)
        return None

def main():
    # Setup command line argument parsing
    parser = argparse.ArgumentParser(
        description="Run a SNAP GPT graph from the command line."
    )

    # Adding arguments
    parser.add_argument(
        "--gpt",
        default=r"C:\Program Files\esa-snap\bin\gpt.exe",
        help="Path to the SNAP gpt executable, defaults to 'C:\\Program Files\\esa-snap\\bin\\gpt.exe' on Windows"
    )
    parser.add_argument(
        "--graph",
        required=True,
        help="Path to the .xml graph file"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the input satellite data"
    )
    parser.add_argument(
        "--aoi",
        required=True,
        help="Area of interest as WKT geometry (e.g. POLYGON ((...)))"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output filename stem (saved to outputs/images/<name>.dim, default: detections.dim (see later))"
    )
    parser.add_argument("--target-window",       type=float, default=50,      help="CFAR target window size in meters (default: 50)")
    parser.add_argument("--guard-window",        type=float, default=500.0,   help="CFAR guard window size in meters (default: 500)")
    parser.add_argument("--background-window",   type=float, default=800.0,   help="CFAR background window size in meters (default: 800)")
    parser.add_argument("--pfa",                 type=float, default=6.5,     help="Probability of false alarm (10^(x)) (default: 6.5)")
    parser.add_argument("--estimate-background", default="false", choices=["true", "false"], help="Locally estimate background statistics (default: false)")
    parser.add_argument("--min-target",          type=float, default=30.0,    help="Minimum target size in meters (default: 30)")
    parser.add_argument("--max-target",          type=float, default=500.0,   help="Maximum target size in meters (default: 500)")
    parser.add_argument("--shoreline-extension", type=int,   default=0,       help="Land-sea mask shoreline extension in meters (default: 0)")

    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, ".."))
    stem = args.output if args.output else "detections"
    output_path = os.path.join(root_dir, "outputs", "images", f"{stem}.dim")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    run_snap_graph(
        args.gpt, args.graph, args.input, args.aoi, output_path,
        target_window=args.target_window,
        guard_window=args.guard_window,
        background_window=args.background_window,
        pfa=args.pfa,
        estimate_background=args.estimate_background,
        min_target_size=args.min_target,
        max_target_size=args.max_target,
        shoreline_extension=args.shoreline_extension,
    )

# Only run the code inside this block if this specific file executed directly
# If you were to import this file into another script, the code inside that block would be ignored
# prevents from starting automatically just because you wanted to borrow a function from the file
if __name__ == "__main__":
    main()