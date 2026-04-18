import subprocess
import os
import argparse
import sys

def run_snap_graph(gpt_path, graph_xml, input_file, output_file):
    """
    Executes a SNAP XML graph using the Graph Processing Tool (GPT).
    """
    if not os.path.exists(gpt_path):
        raise FileNotFoundError(f"GPT tool not found at: {gpt_path}")

    # Build the command line arguments
    command = [
        gpt_path,
        graph_xml,
        "-e",
        f"-Pinput={input_file}",
        f"-Poutput={output_file}"
    ]

    print(f"Starting processing: {os.path.basename(input_file)}")
    
    try:
        process = subprocess.run(
            command, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )   
        print("Processing completed successfully.")
        return process.stdout

    except subprocess.CalledProcessError as e:
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
        help="Path to the SNAP gpt executable"
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
        "--output", 
        required=True, 
        help="Path for the output file"
    )

    args = parser.parse_args()

    # Execute the function with parsed arguments
    run_snap_graph(args.gpt, args.graph, args.input, args.output)

if __name__ == "__main__":
    main()