#!/usr/bin/env python3
"""
Create COMPASS Samplesheet from SRR Accessions

Reads organism-specific SRR lists and creates a samplesheet compatible
with COMPASS pipeline's sra_list input mode.

Usage:
    python create_samplesheet.py --input data/srr_accessions_by_organism/ \
                                  --output samplesheet_diverse_1000.txt
"""

import argparse
from pathlib import Path
import re

def extract_organism_from_filename(filename):
    """Extract organism name from filename like 'Listeria_monocytogenes_srr_list.txt'"""
    # Remove _srr_list.txt suffix
    name = filename.stem.replace('_srr_list', '')
    # Replace underscores with spaces
    organism = name.replace('_', ' ')
    return organism

def main():
    parser = argparse.ArgumentParser(
        description='Create COMPASS samplesheet from SRR lists'
    )
    parser.add_argument(
        '--input',
        default='data/srr_accessions_by_organism',
        help='Directory with organism SRR lists (default: data/srr_accessions_by_organism)'
    )
    parser.add_argument(
        '--output',
        default='samplesheet_diverse_1000.txt',
        help='Output samplesheet file (default: samplesheet_diverse_1000.txt)'
    )
    parser.add_argument(
        '--format',
        choices=['txt', 'csv'],
        default='txt',
        help='Output format: txt (one SRR per line) or csv (with metadata)'
    )

    args = parser.parse_args()

    input_dir = Path(args.input)
    if not input_dir.exists():
        print(f"Error: Input directory not found: {input_dir}")
        return 1

    # Find all SRR list files
    srr_files = list(input_dir.glob('*_srr_list.txt'))
    if not srr_files:
        print(f"Error: No SRR list files found in {input_dir}")
        return 1

    print(f"Found {len(srr_files)} organism SRR lists")

    # Collect all SRRs with organism metadata
    all_data = []

    for srr_file in sorted(srr_files):
        organism = extract_organism_from_filename(srr_file)
        print(f"  {organism}: ", end='')

        with open(srr_file, 'r') as f:
            srrs = [line.strip() for line in f if line.strip()]
            print(f"{len(srrs)} samples")

            for srr in srrs:
                all_data.append({
                    'srr': srr,
                    'organism': organism
                })

    # Write output
    output_path = Path(args.output)

    if args.format == 'txt':
        # Simple text format: one SRR per line
        with open(output_path, 'w') as f:
            for item in all_data:
                f.write(f"{item['srr']}\n")
        print(f"\nWrote {len(all_data)} accessions to: {output_path}")
        print("Format: Plain text (one SRR per line)")

    elif args.format == 'csv':
        # CSV format with metadata
        with open(output_path, 'w') as f:
            f.write("srr,organism\n")
            for item in all_data:
                f.write(f"{item['srr']},{item['organism']}\n")
        print(f"\nWrote {len(all_data)} accessions to: {output_path}")
        print("Format: CSV with organism metadata")

    # Print summary statistics
    organism_counts = {}
    for item in all_data:
        org = item['organism']
        organism_counts[org] = organism_counts.get(org, 0) + 1

    print(f"\n{'='*60}")
    print("SAMPLESHEET SUMMARY")
    print(f"{'='*60}")
    print(f"\nTotal samples: {len(all_data)}")
    print(f"\nSamples per organism:")
    for org in sorted(organism_counts.keys()):
        print(f"  {org}: {organism_counts[org]}")

    print(f"\n{'='*60}")
    print("Next steps:")
    print(f"  1. Review samplesheet: head {output_path}")
    print(f"  2. Run COMPASS: sbatch run_diverse_bacteria_1000.sh")
    print(f"{'='*60}")

    return 0

if __name__ == '__main__':
    exit(main())
