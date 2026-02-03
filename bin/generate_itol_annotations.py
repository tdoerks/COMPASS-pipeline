#!/usr/bin/env python3
"""
Generate iTOL annotation files from prophage metadata TSV

Usage:
    python3 generate_itol_annotations.py <metadata.tsv> [output_dir]

Example:
    python3 generate_itol_annotations.py prophage_metadata_cleaned.tsv itol_annotations/

Outputs:
    - organism_colorstrip.txt: Color strip by organism
    - length_barchart.txt: Bar chart showing prophage lengths
    - labels.txt: Simple labels for tree tips
"""

import pandas as pd
import sys
from pathlib import Path

def generate_organism_colorstrip(df, output_file):
    """Generate color strip for organism column"""

    # Check if organism column exists
    if 'organism' not in df.columns:
        print("Warning: No 'organism' column found, skipping organism colorstrip")
        return

    # Color palette for organisms
    colors = {
        'Escherichia': '#3498DB',  # Blue
        'Salmonella': '#E74C3C',   # Red
        'Campylobacter': '#27AE60', # Green
        'E. coli': '#3498DB',
        'E.coli': '#3498DB',
        'Escherichia coli': '#3498DB'
    }

    with open(output_file, 'w') as f:
        f.write("DATASET_COLORSTRIP\n")
        f.write("SEPARATOR TAB\n")
        f.write("DATASET_LABEL\tOrganism\n")
        f.write("COLOR\t#ff0000\n")
        f.write("STRIP_WIDTH\t50\n")
        f.write("\n")
        f.write("LEGEND_TITLE\tOrganism\n")
        f.write("LEGEND_SHAPES\t1\t1\t1\n")
        f.write(f"LEGEND_COLORS\t{colors.get('Escherichia', '#3498DB')}\t{colors.get('Salmonella', '#E74C3C')}\t{colors.get('Campylobacter', '#27AE60')}\n")
        f.write("LEGEND_LABELS\tE. coli\tSalmonella\tCampylobacter\n")
        f.write("\n")
        f.write("DATA\n")

        for _, row in df.iterrows():
            prophage_id = row.get('prophage_id', row.get('original_id', ''))
            organism = row.get('organism', 'Unknown')

            # Get color for this organism
            color = colors.get(organism, '#999999')

            f.write(f"{prophage_id}\t{color}\t{organism}\n")

def generate_length_barchart(df, output_file):
    """Generate bar chart for prophage length"""

    # Check for length column
    length_col = None
    for col in ['length_bp', 'length', 'size']:
        if col in df.columns:
            length_col = col
            break

    if not length_col:
        print("Warning: No length column found, skipping length bar chart")
        return

    with open(output_file, 'w') as f:
        f.write("DATASET_SIMPLEBAR\n")
        f.write("SEPARATOR TAB\n")
        f.write("DATASET_LABEL\tProphage Length (bp)\n")
        f.write("COLOR\t#9B59B6\n")
        f.write("WIDTH\t200\n")
        f.write("\n")
        f.write("DATA\n")

        for _, row in df.iterrows():
            prophage_id = row.get('prophage_id', row.get('original_id', ''))
            length = row.get(length_col, 0)

            f.write(f"{prophage_id}\t{length}\n")

def generate_labels(df, output_file):
    """Generate simple labels file"""

    with open(output_file, 'w') as f:
        f.write("LABELS\n")
        f.write("SEPARATOR TAB\n")
        f.write("DATA\n")

        for _, row in df.iterrows():
            prophage_id = row.get('prophage_id', row.get('original_id', ''))
            sample_id = row.get('sample_id', '')

            # Create a short label (just sample ID)
            label = sample_id if sample_id else prophage_id

            f.write(f"{prophage_id}\t{label}\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_itol_annotations.py <metadata.tsv> [output_dir]")
        print("\nExample:")
        print("  python generate_itol_annotations.py prophage_metadata_cleaned.tsv itol_annotations/")
        sys.exit(1)

    metadata_file = sys.argv[1]
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("itol_annotations")

    # Create output directory
    output_dir.mkdir(exist_ok=True, parents=True)

    # Read metadata
    print(f"Reading {metadata_file}...")
    df = pd.read_csv(metadata_file, sep='\t')

    print(f"Found {len(df)} prophages")
    print(f"Columns: {list(df.columns)}")

    # Generate annotation files
    print("\nGenerating iTOL annotation files...")

    generate_organism_colorstrip(df, output_dir / "organism_colorstrip.txt")
    print("  ✓ organism_colorstrip.txt")

    generate_length_barchart(df, output_dir / "length_barchart.txt")
    print("  ✓ length_barchart.txt")

    generate_labels(df, output_dir / "labels.txt")
    print("  ✓ labels.txt")

    print(f"\nDone! Files saved to: {output_dir}/")
    print("\nNext steps:")
    print("1. Upload prophage_tree_cleaned.nwk to iTOL (https://itol.embl.de/upload.cgi)")
    print("2. Drag-and-drop the files from itol_annotations/ onto the tree")
    print("3. Customize colors and export")

if __name__ == "__main__":
    main()
