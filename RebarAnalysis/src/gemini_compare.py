import os
import sys
import argparse
import contextlib
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

@contextlib.contextmanager
def silence_stderr():
    """A context manager to temporarily redirect stderr to devnull."""
    stderr_fd = sys.stderr.fileno()
    saved_stderr_fd = os.dup(stderr_fd)
    try:
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull_fd, stderr_fd)
        yield
    finally:
        os.dup2(saved_stderr_fd, stderr_fd)
        os.close(devnull_fd)
        os.close(saved_stderr_fd)

PROMPT = """
Analyze the two provided images: an architect's drawing and a code's output. Your response must follow the specified format precisely.

**1. Output Format:**
Your entire output must be a single block of plain text. It should start with the table and end with the final similarity score.
-   **Table Style:** Create a plain-text table suitable for a terminal, using `|`, `-`, and `+` characters for borders.
-   **No Markdown:** Do not wrap your response in markdown backticks (```) or include any other text or explanations.

**2. Table Content:**
The table must have four columns: "Parameter", "Architect's Design", "Code's Output", and "Acceptance".

**3. Comparison Logic & Rules:**
-   **Parameters:** Compare the 'Number of rods', 'Radius of rods (avg)', and all 'Distances between rods'.
-   **Units:** You must include the units (e.g., mm, px) for all measurements in the "Architect's Design" and "Code's Output" columns.
-   **"Acceptance" Column (Strict Rule):**
    -   If the units being compared in a row are different (e.g., "mm" vs. "px"), the value in this column **must** be "NA".
    -   Only if the units are identical, you may use "Acceptable", "Minor Mismatch", or "Not Acceptable".

**4. Final Similarity:**
After the table, on a new line, provide a "Final Similarity" score as a percentage.
"""

def get_api_key():
    """Gets the Google API key."""
    load_dotenv()
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in .env file or environment variables.", file=sys.stderr)
    return api_key

def generate_comparison(api_key, software_img_path, actual_img_path):
    """Sends images to the Gemini API and returns the comparison table."""
    try:
        genai.configure(api_key=api_key)
        software_img = Image.open(software_img_path)
        actual_img = Image.open(actual_img_path)
        model = genai.GenerativeModel('gemini-2.5-pro')
        response = model.generate_content([PROMPT, software_img, actual_img])
        return response.text
    except Exception as e:
        print(f"\nAn error occurred during API call: {e}", file=sys.stderr)
        return None

def main():
    """Main function to parse arguments and run the comparison."""
    parser = argparse.ArgumentParser(
        description='Compare a software design drawing with a real-world measurement image.'
    )
    parser.add_argument(
        '--software', type=str, required=True, help='Path to the software design image.'
    )
    parser.add_argument(
        '--output', type=str, required=True, help='Path to the real-world measurement image.'
    )
    args = parser.parse_args()

    api_key = get_api_key()
    if not api_key:
        print("API key not found.", file=sys.stderr)
        return

    with silence_stderr():
        comparison_table = generate_comparison(api_key, args.software, args.output)

    if comparison_table:
        print(comparison_table)

if __name__ == '__main__':
    main()