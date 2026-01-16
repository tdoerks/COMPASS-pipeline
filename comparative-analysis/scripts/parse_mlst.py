#!/usr/bin/env python3
"""
Parse MLST results from COMPASS pipeline

Extracts multi-locus sequence types for contextualizing
plasmid/prophage/AMR patterns.

Usage:
    python parse_mlst.py -i /path/to/mlst/file.tsv -o mlst_data.csv -y 2022
"""

import argparse
import pandas as pd
from pathlib import Path
import sys

def parse_mlst_file(file_path):
    """Parse MLST results file"""
    try:
        # MLST outputs TSV format
        # Format: FILE\tSCHEME\tST\tadk(allele)\tfumC(allele)\t...
        df = pd.read_csv(file_path, sep='\t')

        results = []
        for _, row in df.iterrows():
            # Extract sample ID from filename column
            sample_file = row.iloc[0]  # First column is filename
            sample_id = Path(sample_file).stem.split('_')[0]

            result = {
                'sample_id': sample_id,
                'scheme': row.iloc[1] if len(row) > 1 else '',
                'st': row.iloc[2] if len(row) > 2 else '',
            }

            # Add allele information
            for col_idx in range(3, len(row)):
                col_name = df.columns[col_idx]
                allele = row.iloc[col_idx]
                # Parse allele info (e.g., "adk(10)" -> gene: adk, allele: 10)
                if '(' in str(allele):
                    gene = col_name
                    allele_num = str(allele).split('(')[1].split(')')[0]
                    result[f'allele_{gene}'] = allele_num

            results.append(result)

        return results
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return []

def main():
    parser = argparse.ArgumentParser(description='Parse MLST results')
    parser.add_argument('-i', '--input', required=True,
                       help='MLST results TSV file')
    parser.add_argument('-o', '--output', required=True,
                       help='Output CSV file')
    parser.add_argument('-y', '--year', required=True,
                       help='Year of data (e.g., 2022, 2023, 2024)')

    args = parser.parse_args()

    input_file = Path(args.input)
    if not input_file.exists():
        print(f"Error: Input file {input_file} does not exist", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing MLST results from {input_file}")

    results = parse_mlst_file(input_file)

    # Add year to each result
    for result in results:
        result['year'] = args.year

    # Convert to DataFrame and save
    df = pd.DataFrame(results)

    if len(df) == 0:
        print("Warning: No MLST results found", file=sys.stderr)
    else:
        print(f"Extracted MLST data for {len(df)} samples")
        print(f"\nSequence Type (ST) distribution:")
        print(df['st'].value_counts().head(20))

        print(f"\nMLST scheme distribution:")
        print(df['scheme'].value_counts())

    df.to_csv(args.output, index=False)
    print(f"\nResults saved to {args.output}")

if __name__ == '__main__':
    main()
