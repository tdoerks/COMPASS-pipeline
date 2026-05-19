#!/usr/bin/env python3
"""
Simple script to create filtered_samples metadata for COMPASS summary generation.
Since we're running with pre-assembled FASTA files, we just list the samples that were processed.
"""
import argparse
import os
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Create filtered samples metadata from COMPASS results')
    parser.add_argument('--outdir', required=True, help='COMPASS output directory')
    args = parser.parse_args()

    outdir = Path(args.outdir)

    # Create filtered_samples directory
    filtered_dir = outdir / 'filtered_samples'
    filtered_dir.mkdir(parents=True, exist_ok=True)

    # Find all samples by looking at AMRFinder results (every sample should have these)
    amr_dir = outdir / 'amrfinder'
    samples = []

    if amr_dir.exists():
        for amr_file in amr_dir.glob('*_amr.tsv'):
            sample_id = amr_file.stem.replace('_amr', '')
            samples.append(sample_id)

    # Write filtered samples CSV
    output_file = filtered_dir / 'filtered_samples.csv'
    with open(output_file, 'w') as f:
        f.write('sample\n')
        for sample in sorted(samples):
            f.write(f'{sample}\n')

    print(f"✓ Created filtered samples metadata with {len(samples)} samples", file=sys.stderr)
    print(f"  Output: {output_file}", file=sys.stderr)
    print(f"  Samples: {', '.join(sorted(samples))}", file=sys.stderr)

    return 0

if __name__ == '__main__':
    sys.exit(main())
