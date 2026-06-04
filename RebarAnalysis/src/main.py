import subprocess
import os
import argparse
import sys

# Configuration
PYTHON_EXECUTABLE = sys.executable 
SCRIPT_DIR = os.path.dirname(__file__) 
ANALYSIS_SCRIPT_NAME = os.path.join(SCRIPT_DIR, "analysis_core.py")
COMPARISON_SCRIPT_NAME = os.path.join(SCRIPT_DIR, "gemini_compare.py")

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def run_analysis_core(input_path, output_path):
    print_header("STEP 1: RUNNING INTERACTIVE REBAR ANALYSIS")
    
    if not os.path.exists(ANALYSIS_SCRIPT_NAME):
        print(f"✗ ERROR: Core script '{ANALYSIS_SCRIPT_NAME}' not found.", file=sys.stderr)
        return False
    if not os.path.exists(input_path):
        print(f"✗ ERROR: Input image '{input_path}' not found.", file=sys.stderr)
        return False

    print(f"ℹ Launching '{ANALYSIS_SCRIPT_NAME}'...")
    print(f"   - Input Photo:  '{input_path}'")
    print(f"   - Output Path:  '{output_path}'")
    print("-" * 60)
    
    command = [
        PYTHON_EXECUTABLE, 
        ANALYSIS_SCRIPT_NAME,
        "--input", input_path,
        "--output", output_path
    ]
    
    try:
        subprocess.run(command, check=True, text=True)
        return True
    except subprocess.CalledProcessError:
        print("-" * 60, file=sys.stderr)
        print(f"✗ ERROR: '{ANALYSIS_SCRIPT_NAME}' exited with an error.", file=sys.stderr)
        return False

def run_gemini_comparison(software_image_path, code_output_path):
    print_header("STEP 2: RUNNING COMPARISON")

    if not os.path.exists(COMPARISON_SCRIPT_NAME):
        print(f"✗ ERROR: Comparison script '{COMPARISON_SCRIPT_NAME}' not found.", file=sys.stderr)
        return False
    if not os.path.exists(software_image_path):
        print(f"✗ ERROR: Architect's drawing not found: '{software_image_path}'", file=sys.stderr)
        return False
    if not os.path.exists(code_output_path):
        print(f"✗ ERROR: Code output image not found: '{code_output_path}'", file=sys.stderr)
        return False

    print(f"ℹ Launching '{COMPARISON_SCRIPT_NAME}'...")
    print(f"   - Architect's Drawing: '{software_image_path}'")
    print(f"   - Code's Output:       '{code_output_path}'")
    
    command = [
        PYTHON_EXECUTABLE,
        COMPARISON_SCRIPT_NAME,
        "--software", software_image_path,
        "--output", code_output_path
    ]

    try:
        print("\n--- Comparison Result ---")
        subprocess.run(command, check=True, text=True)
        return True
    except subprocess.CalledProcessError:
        print(f"✗ ERROR: '{COMPARISON_SCRIPT_NAME}' failed.", file=sys.stderr)
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Master control script for the Rebar Analysis and Comparison Tool.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--input", 
        required=True, 
        help="Path to the input photograph of the rebar."
    )
    parser.add_argument(
        "--output", 
        required=True, 
        help="Path to save the annotated analysis result image."
    )
    parser.add_argument(
        "--compare", 
        help="Optional: Path to the architect's design drawing for AI comparison."
    )

    args = parser.parse_args()

    analysis_successful = run_analysis_core(args.input, args.output)
    
    if analysis_successful:
        if args.compare:
            run_gemini_comparison(
                software_image_path=args.compare, 
                code_output_path=args.output
            )
        else:
            print("\nProcess finished successfully.")
    else:
        print("\nProcess aborted due to errors in the analysis step.", file=sys.stderr)