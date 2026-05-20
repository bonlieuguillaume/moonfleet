import anthropic
import os

# Paths relative to the script location
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR    = os.path.join(BASE_DIR, "src")
GRAPHS_DIR = os.path.join(BASE_DIR, "graphs")
OUTPUT     = os.path.join(BASE_DIR, "README.md")


def read_file(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def collect_project_files(src_dir: str, graphs_dir: str) -> dict:
    """Collect all relevant project files."""
    files = {}

    # Python files
    for fname in os.listdir(src_dir):
        if fname.endswith('.py'):
            fpath = os.path.join(src_dir, fname)
            files[f"src/{fname}"] = read_file(fpath)

    # XML graph files
    for fname in os.listdir(graphs_dir):
        if fname.endswith('.xml'):
            fpath = os.path.join(graphs_dir, fname)
            files[f"graphs/{fname}"] = read_file(fpath)

    return files


def generate_readme(src_dir: str, graphs_dir: str, output_path: str):
    """Generate README.md using Claude API."""

    # Collect files
    files = collect_project_files(src_dir, graphs_dir)

    # Build prompt
    files_content = ""
    for filepath, content in files.items():
        ext = filepath.split('.')[-1]
        files_content += f"\n\n### {filepath}\n```{ext}\n{content}\n```"

    prompt = f"""You are a technical writer. Generate a professional README.md for this remote sensing project.

The project is a Sentinel-1 SAR ship detection pipeline using ESA SNAP GPT.

Include these sections:
1. Title and badges (Python, License)
2. Short description (2-3 sentences)
3. Features (bullet points)
4. Project structure (tree)
5. Installation (conda env setup)
6. Usage (CLI examples with all arguments)
7. SNAP Graphs description (one paragraph per XML)
8. Output description (what files are produced)
9. Dependencies table

Write in English. Be concise and technical.

Project files:
{files_content}"""

    # Call Claude API
    client = anthropic.Anthropic()

    print("Generating README with Claude...")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    readme_content = message.content[0].text

    # Save
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"README.md saved to {output_path}")
    return readme_content


if __name__ == "__main__":
    generate_readme(SRC_DIR, GRAPHS_DIR, OUTPUT)