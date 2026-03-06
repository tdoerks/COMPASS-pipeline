#!/usr/bin/env python3
"""
Parse MOBsuite results from COMPASS pipeline

Extracts plasmid replicon types, MOB types, and plasmid-associated
genes for comparative analysis.

Usage:
    python parse_mobsuite.py -i /path/to/mobsuite/dir -o plasmid_data.csv -y 2022
"""

import argparse
import pandas as pd
from pathlib import Path
import sys

def parse_mobsuite_file(file_path):
    """Parse MOBsuite mobtyper output file"""
    try:
        # MOBsuite outputs TSV format
        df = pd.read_csv(file_path, sep='\t')

        results = []
        for _, row in df.iterrows():
            result = {
                'file_id': row.get('file_id', ''),
                'num_contigs': row.get('num_contigs', 0),
                'total_length': row.get('total_length', 0),
                'gc_content': row.get('gc', 0),
                'rep_types': row.get('rep_type(s)', ''),
                'rep_type_accessions': row.get('rep_type_accession(s)', ''),
                'relaxase_types': row.get('relaxase_type(s)', ''),
                'relaxase_type_accessions': row.get('relaxase_type_accession(s)', ''),
                'mpf_types': row.get('mpf_type', ''),
                'mpf_type_accessions': row.get('mpf_type_accession(s)', ''),
                'orit_types': row.get('orit_type(s)', ''),
                'orit_accessions': row.get('orit_accession(s)', ''),
                'predicted_mobility': row.get('PredictedMobility', ''),
                'mash_nearest_neighbor': row.get('mash_nearest_neighbor', ''),
                'mash_neighbor_distance': row.get('mash_neighbor_distance', ''),
                'mash_neighbor_cluster': row.get('mash_neighbor_cluster', ''),
            }
            results.append(result)

        return results
    except Exception as e:
        print(f"Error parsing {file_path}: {e}", file=sys.stderr)
        return []

def extract_sample_id(dirname):
    """Extract sample ID from directory name"""
    # MOBsuite creates directories like SRR12345/
    return dirname

def main():
    parser = argparse.ArgumentParser(description='Parse MOBsuite results')
    parser.add_argument('-i', '--input-dir', required=True,
                       help='Directory containing MOBsuite sample subdirectories')
    parser.add_argument('-o', '--output', required=True,
                       help='Output CSV file')
    parser.add_argument('-y', '--year', required=True,
                       help='Year of data (e.g., 2022, 2023, 2024)')

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    # MOBsuite creates a subdirectory for each sample
    sample_dirs = [d for d in input_dir.iterdir() if d.is_dir()]

    print(f"Found {len(sample_dirs)} sample directories in {input_dir}")

    all_results = []
    samples_with_plasmids = 0

    for sample_dir in sample_dirs:
        sample_id = extract_sample_id(sample_dir.name)

        # Look for mobtyper output file
        mobtyper_file = sample_dir / 'mobtyper_results.txt'
        if not mobtyper_file.exists():
            # Try alternative names
            mobtyper_file = sample_dir / 'mobtyper_aggregate_report.txt'

        if mobtyper_file.exists():
            results = parse_mobsuite_file(mobtyper_file)

            if results:
                samples_with_plasmids += 1

            # Add sample ID and year to each result
            for result in results:
                result['sample_id'] = sample_id
                result['year'] = args.year
                all_results.append(result)

    # Convert to DataFrame and save
    df = pd.DataFrame(all_results)

    if len(df) == 0:
        print("Warning: No plasmids found", file=sys.stderr)
    else:
        print(f"Extracted {len(df)} plasmid entries from {samples_with_plasmids} samples")
        print(f"\nReplicon type distribution:")
        # Split multi-replicon entries
        all_reps = []
        for reps in df['rep_types'].dropna():
            if reps:
                all_reps.extend(str(reps).split(','))
        rep_counts = pd.Series(all_reps).value_counts()
        print(rep_counts.head(20))

        print(f"\nPredicted mobility distribution:")
        print(df['predicted_mobility'].value_counts())

    df.to_csv(args.output, index=False)
    print(f"\nResults saved to {args.output}")

if __name__ == '__main__':
    main()
