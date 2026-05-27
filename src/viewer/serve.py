import http.server
import socketserver
import argparse
import webbrowser
import threading
import os

"""
serve.py
--------
Minimal HTTP server for the Moonfleet viewer.
Serves the moonfleet project root so that both outputs/ and src/ are
reachable, regardless of where the script is launched from.

Usage:
    python serve.py
    python serve.py --port 9000
    python serve.py --port 8000 --open   # auto-opens browser

Viewer URL once running:
    http://localhost:8000/src/viewer/viewer.html
"""



def main():
    # action="store_true": unnecessary to write --open true, just --open is enough to set it to True
    parser = argparse.ArgumentParser(description="Moonfleet local viewer server")
    parser.add_argument("--port", type=int, default=8000, help="Port to serve on (default: 8000)")
    parser.add_argument("--open", action="store_true", help="Auto-open browser") 
    args = parser.parse_args()

    # Always serve from the project root so outputs/ and src/ are both reachable.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))
    os.chdir(root_dir)

    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *a: None  # silence request logs

    with socketserver.TCPServer(("", args.port), handler) as httpd:
        url = f"http://localhost:{args.port}/src/viewer/viewer.html"
        print(f"  Moonfleet viewer running at {url}")
        print(f"  Serving files from: {root_dir}")
        print(f"  Press Ctrl+C to stop")
        if args.open:
            # delay opening the browser slightly to ensure the server is ready
            threading.Timer(0.5, lambda: webbrowser.open(url)).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Server stopped.")

if __name__ == "__main__":
    main()
