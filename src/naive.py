import subprocess
import os

def run_snap_graph(gpt_path, graph_xml, input_file, output_file):
    """
    Executes a SNAP XML graph using the Graph Processing Tool (GPT).

    This function wraps the GPT command-line interface, allowing you to trigger
    complex Remote Sensing workflows from Python without using the snappy library.
    It passes the input and output file paths as external parameters.

    Args:
        gpt_path (str): Absolute path to the SNAP gpt executable.
        graph_xml (str): Path to the .xml file containing the processing graph.
        input_file (str): Path to the input satellite data (e.g., .SAFE, .zip).
        output_file (str): Path where the processed output should be saved.

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
    # -Pname=value: Sets a processing parameter (referenced as ${name} in the XML)
    command = [
        gpt_path,
        graph_xml,
        "-e",
        f"-Pinput={input_file}",
        f"-Poutput={output_file}"
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
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )   
        print("Processing completed successfully.")
        return process.stdout

    except subprocess.CalledProcessError as e:
        # Capture and display the Java/SNAP error logs
        print(f"Error during graph execution:\n{e.stderr}")
        return None

# --- CONFIGURATION ---
# Windows example: r"C:\Program Files\snap\bin\gpt.exe"
# Linux example: "/usr/local/snap/bin/gpt"
GPT_BIN = r"C:\Program Files\esa-snap\bin\gpt.exe"
GRAPH_XML = r"C:\Users\guigu\Documents\pro_asus\moonfleet\moonfleet_graphs\CFAR.xml"
IN_FILE = r"C:\Users\guigu\Documents\pro_asus\moonfleet\data_raw\suez\S1A_IW_GRDH_1SDV_20260107T233152_20260107T233217_062668_07DB60_04F7.zip"
OUT_FILE = r"C:\Users\guigu\Documents\pro_asus\moonfleet\outputs\naive_2.dim"

# Only run the code inside this block if this specific file executed directly
# If you were to import this file into another script, the code inside that block would be ignored
# prevents from starting automatically just because you wanted to borrow a function from the file

if __name__ == "__main__":
    run_snap_graph(GPT_BIN, GRAPH_XML, IN_FILE, OUT_FILE) 