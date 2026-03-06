#!/usr/bin/env python3
"""
Parse VIBRANT results from COMPASS pipeline

Extracts prophage predictions, locations, and associated genes
for comparative analysis.

Usage:
    python parse_vibrant.py -i /path/to/vibrant/dir -o prophage_data.csv -y 2022
"""

import argparse
import pandas as pd
from pathlib import Path
import sys
import re

def parse_vibrant_summary(file_path):
    """Parse VIBRANT summary file for prophage predictions"""
    try:
        results = []

        # VIBRANT creates different output files
        # Try to read the phages_lysogenic file (integrated prophages)
        with open(file_path, 'r') as f:
            for line in f:
                if line.startswith('>'):
                    # Parse header line
                    # Format: >scaffold_name fragment_X
                    parts = line.strip().split()
                    if len(parts) >= 1:
                        scaffold = parts[0][1:]  # Remove '>'
                        fragment = parts[1] if len(parts) > 1 else 'fragment_1'

                        result = {
                            'scaffold': scaffold,
                            'fragment': fragment,
                            'prophage_type': 'lysogenic'
                        }
                        results.append(result)

        return results
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return []

def parse_vibrant_annotations(file_path):
    """Parse VIBRANT protein annotations for prophage genes"""
    try:
        df = pd.read_csv(file_path, sep='\t')

        results = []
        for _, row in df.iterrows():
            result = {
                'protein': row.get('protein', ''),
                'scaffold': row.get('scaffold', ''),
                'annotation': row.get('AMG annotation', ''),
                'ko': row.get('KO', ''),
                'kegg_hit': row.get('KEGG hit', ''),
                'pfam_hit': row.get('Pfam hit', ''),
                'vog_hit': row.get('VOG hit', '')
            }
            results.append(result)

        return results
    except Exception as e:
        print(f"Error parsing annotations {file_path}: {e}", file=sys.stderr)
        return []

def extract_sample_id(dirname):
    """Extract sample ID from directory name"""
    # VIBRANT creates directories like SRR12345/
    return dirname

def main():
    parser = argparse.ArgumentParser(description='Parse VIBRANT prophage results')
    parser.add_argument('-i', '--input-dir', required=True,
                       help='Directory containing VIBRANT sample subdirectories')
    parser.add_argument('-o', '--output', required=True,
                       help='Output CSV file')
    parser.add_argument('-y', '--year', required=True,
                       help='Year of data (e.g., 2022, 2023, 2024)')

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    # VIBRANT creates a subdirectory for each sample
    sample_dirs = [d for d in input_dir.iterdir() if d.is_dir()]

    print(f"Found {len(sample_dirs)} sample directories in {input_dir}")

    all_prophages = []
    all_genes = []
    samples_with_prophages = 0

    for sample_dir in sample_dirs:
        sample_id = extract_sample_id(sample_dir.name)

        # Look for VIBRANT output files
        # VIBRANT creates VIBRANT_*/  subdirectory
        vibrant_subdirs = list(sample_dir.glob('VIBRANT_*'))

        for vibrant_dir in vibrant_subdirs:
            # Look for prophage predictions
            lysogenic_file = vibrant_dir / 'VIBRANT_phages_lysogenic' / 'lysogenic.fasta'
            if lysogenic_file.exists():
                prophages = parse_vibrant_summary(lysogenic_file)
                samples_with_prophages += 1 if prophages else samples_with_prophages

                for prophage in prophages:
                    prophage['sample_id'] = sample_id
                    prophage['year'] = args.year
                    all_prophages.append(prophage)

            # Look for gene annotations
            annotation_file = vibrant_dir / 'VIBRANT_results' / f'{sample_id}.phages_combined.txt'
            if annotation_file.exists():
                genes = parse_vibrant_annotations(annotation_file)
                for gene in genes:
                    gene['sample_id'] = sample_id
                    gene['year'] = args.year
                    all_genes.append(gene)

    # Convert to DataFrames and save
    df_prophages = pd.DataFrame(all_prophages)
    df_genes = pd.DataFrame(all_genes)

    if len(df_prophages) == 0:
        print("Warning: No prophages found", file=sys.stderr)
    else:
        print(f"Extracted {len(df_prophages)} prophage predictions from {samples_with_prophages} samples")

        # Count prophages per sample
        prophages_per_sample = df_prophages.groupby('sample_id').size()
        print(f"\nAverage prophages per sample: {prophages_per_sample.mean():.2f}")
        print(f"Max prophages in one sample: {prophages_per_sample.max()}")

    # Save prophages
    df_prophages.to_csv(args.output, index=False)
    print(f"\nProphage results saved to {args.output}")

    # Save genes if found
    if len(df_genes) > 0:
        genes_output = args.output.replace('.csv', '_genes.csv')
        df_genes.to_csv(genes_output, index=False)
        print(f"Prophage gene annotations saved to {genes_output}")

if __name__ == '__main__':
    main()
