#!/usr/bin/env python3
"""
Parse AMRFinder results from COMPASS pipeline

Extracts antimicrobial resistance genes and their locations
(chromosome vs plasmid) for comparative analysis.

Usage:
    python parse_amrfinder.py -i /path/to/amrfinder/dir -o amr_data.csv -y 2022
"""

import argparse
import pandas as pd
from pathlib import Path
import sys

def parse_amrfinder_file(file_path):
    """Parse a single AMRFinder output file"""
    try:
        # AMRFinder outputs TSV format
        df = pd.read_csv(file_path, sep='\t')

        # Extract key columns
        results = []
        for _, row in df.iterrows():
            result = {
                'gene_symbol': row.get('Gene symbol', ''),
                'sequence_name': row.get('Sequence name', ''),
                'element_type': row.get('Element type', ''),
                'element_subtype': row.get('Element subtype', ''),
                'class': row.get('Class', ''),
                'subclass': row.get('Subclass', ''),
                'method': row.get('Method', ''),
                'target_length': row.get('Target length', 0),
                'coverage': row.get('% Coverage of reference sequence', 0),
                'identity': row.get('% Identity to reference sequence', 0),
                'accession': row.get('Accession of closest sequence', ''),
                'name': row.get('Name of closest sequence', '')
            }
            results.append(result)

        return results
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return []

def extract_sample_id(filename):
    """Extract sample ID from filename (e.g., SRR12345_amrfinder.tsv -> SRR12345)"""
    return filename.split('_')[0]

def main():
    parser = argparse.ArgumentParser(description='Parse AMRFinder results')
    parser.add_argument('-i', '--input-dir', required=True,
                       help='Directory containing AMRFinder TSV files')
    parser.add_argument('-o', '--output', required=True,
                       help='Output CSV file')
    parser.add_argument('-y', '--year', required=True,
                       help='Year of data (e.g., 2022, 2023, 2024)')

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    # Find all AMRFinder output files
    amr_files = list(input_dir.glob('*.tsv'))
    if not amr_files:
        amr_files = list(input_dir.glob('*_amrfinder.txt'))

    print(f"Found {len(amr_files)} AMRFinder files in {input_dir}")

    all_results = []

    for amr_file in amr_files:
        sample_id = extract_sample_id(amr_file.name)
        results = parse_amrfinder_file(amr_file)

        # Add sample ID and year to each result
        for result in results:
            result['sample_id'] = sample_id
            result['year'] = args.year
            all_results.append(result)

    # Convert to DataFrame and save
    df = pd.DataFrame(all_results)

    if len(df) == 0:
        print("Warning: No AMR genes found", file=sys.stderr)
    else:
        print(f"Extracted {len(df)} AMR gene entries from {len(amr_files)} samples")
        print(f"\nAMR gene distribution:")
        print(df['gene_symbol'].value_counts().head(20))
        print(f"\nAMR class distribution:")
        print(df['class'].value_counts())

    df.to_csv(args.output, index=False)
    print(f"\nResults saved to {args.output}")

if __name__ == '__main__':
    main()
