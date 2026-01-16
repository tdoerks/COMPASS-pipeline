#!/usr/bin/env python3
"""
Generate COMPASS Summary for Kansas 2021-2025 NARMS Data

Simple wrapper script to generate the comprehensive COMPASS summary HTML report
with prophage functional categories for Kansas dataset.

Usage:
    python3 generate_kansas_compass_summary.py

Generates:
    - kansas_compass_summary.html (interactive HTML report)
    - kansas_compass_summary.tsv (tab-delimited summary table)
"""

import subprocess
import sys
from pathlib import Path

def main():
    print("=" * 80)
    print("🧬 GENERATING COMPASS SUMMARY FOR KANSAS 2021-2025 NARMS DATA")
    print("=" * 80)
    print()

    # Define paths
    data_dir = Path("/bulk/tylerdoe/archives/kansas_2021-2025_all_narms_v1.2mod")
    output_html = data_dir / "kansas_compass_summary.html"
    output_tsv = data_dir / "kansas_compass_summary.tsv"

    # Path to the generate_compass_summary.py script
    script_path = Path(__file__).parent / "bin" / "generate_compass_summary.py"

    # Check if data directory exists
    if not data_dir.exists():
        print(f"❌ Error: Data directory not found: {data_dir}")
        print()
        print("Please verify the path or update the script if your data is elsewhere.")
        sys.exit(1)

    print(f"📁 Data directory: {data_dir}")
    print(f"📊 Output HTML: {output_html}")
    print(f"📄 Output TSV: {output_tsv}")
    print()

    # Build command
    cmd = [
        "python3",
        str(script_path),
        "--outdir", str(data_dir),
        "--output_html", str(output_html),
        "--output_tsv", str(output_tsv)
    ]

    print("Running command:")
    print(" ".join(cmd))
    print()
    print("=" * 80)
    print()

    # Run the command
    try:
        result = subprocess.run(cmd, check=True)

        print()
        print("=" * 80)
        print("✅ COMPASS SUMMARY GENERATED SUCCESSFULLY!")
        print("=" * 80)
        print()
        print("Generated files:")
        print(f"  📊 HTML Report: {output_html}")
        print(f"  📄 TSV Table: {output_tsv}")
        print()
        print("To view the HTML report:")
        print(f"  1. Download: scp tylerdoe@beocat.ksu.edu:{output_html} .")
        print(f"  2. Open in your browser")
        print()
        print("The report includes:")
        print("  • Overview tab with key statistics")
        print("  • Data table tab with all sample details")
        print("  • Prophage Functional Diversity tab with pie chart")
        print("    - DNA Packaging, Structural, Lysis, Regulation, DNA Modification")
        print()

        return 0

    except subprocess.CalledProcessError as e:
        print()
        print("=" * 80)
        print("❌ ERROR GENERATING COMPASS SUMMARY")
        print("=" * 80)
        print()
        print(f"Command failed with exit code: {e.returncode}")
        print()
        print("Check the error messages above for details.")
        print()
        return 1

    except Exception as e:
        print()
        print("=" * 80)
        print("❌ UNEXPECTED ERROR")
        print("=" * 80)
        print()
        print(f"Error: {e}")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
