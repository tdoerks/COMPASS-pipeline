#!/usr/bin/env python3
"""
Recreate filtered_samples.csv from actual analyzed samples

This script scans the COMPASS pipeline results directories (quast, busco, etc.)
to find which samples were actually analyzed, then extracts their metadata
from the original metadata CSV files.

Usage:
    python3 recreate_filtered_metadata.py --outdir /path/to/compass/results

Output:
    - filtered_samples/filtered_samples.csv with only analyzed samples
"""

import argparse
import pandas as pd
from pathlib import Path
import sys


def parse_args():
    parser = argparse.ArgumentParser(description='Recreate filtered_samples.csv from analyzed samples')
    parser.add_argument('--outdir', required=True, help='COMPASS pipeline output directory')
    return parser.parse_args()


def find_analyzed_samples(outdir):
    """Find all samples that have analysis results"""
    print("Scanning for analyzed samples...")

    analyzed_samples = set()
    outdir_path = Path(outdir)

    # Check QUAST directory (most reliable - every sample should have this)
    quast_dir = outdir_path / 'quast'
    if quast_dir.exists():
        for sample_dir in quast_dir.glob('*_quast'):
            sample_id = sample_dir.name.replace('_quast', '')
            analyzed_samples.add(sample_id)
        print(f"  Found {len(analyzed_samples)} samples from QUAST results")

    # Also check other directories to be comprehensive
    for analysis_dir in ['busco', 'amrfinder', 'mlst', 'mobsuite', 'vibrant']:
        dir_path = outdir_path / analysis_dir
        if dir_path.exists():
            for item in dir_path.iterdir():
                if item.is_dir():
                    # Extract sample ID (remove common suffixes)
                    sample_id = item.name
                    for suffix in ['_busco', '_amrfinder', '_mlst', '_mobsuite', '_vibrant']:
                        sample_id = sample_id.replace(suffix, '')
                    analyzed_samples.add(sample_id)

    print(f"  Total unique samples found: {len(analyzed_samples)}")
    return sorted(analyzed_samples)


def load_original_metadata(outdir):
    """Load original metadata from metadata directory"""
    print("\nLoading original metadata...")

    metadata_dir = Path(outdir) / 'metadata'
    if not metadata_dir.exists():
        print(f"ERROR: Metadata directory not found: {metadata_dir}")
        return None

    all_metadata = []

    # Load metadata from each organism's CSV
    for metadata_file in metadata_dir.glob('*_metadata.csv'):
        print(f"  Reading {metadata_file.name}...")
        try:
            df = pd.read_csv(metadata_file)
            all_metadata.append(df)
            print(f"    {len(df)} entries loaded")
        except Exception as e:
            print(f"    WARNING: Could not read {metadata_file}: {e}")

    if not all_metadata:
        print("ERROR: No metadata files found!")
        return None

    # Combine all metadata
    combined_metadata = pd.concat(all_metadata, ignore_index=True)
    print(f"\n  Total metadata entries: {len(combined_metadata)}")

    # Remove duplicates (same Run ID)
    if 'Run' in combined_metadata.columns:
        combined_metadata = combined_metadata.drop_duplicates(subset=['Run'], keep='first')
        print(f"  After deduplication: {len(combined_metadata)}")

    return combined_metadata


def create_filtered_metadata(analyzed_samples, original_metadata, outdir):
    """Create filtered metadata CSV with only analyzed samples"""
    print("\nCreating filtered metadata...")

    if 'Run' not in original_metadata.columns:
        print("ERROR: 'Run' column not found in metadata!")
        return False

    # Filter metadata to only analyzed samples
    filtered_df = original_metadata[original_metadata['Run'].isin(analyzed_samples)]

    print(f"  Matched {len(filtered_df)} samples with metadata")

    # Check for samples without metadata
    samples_without_metadata = set(analyzed_samples) - set(filtered_df['Run'])
    if samples_without_metadata:
        print(f"\n  ⚠️  WARNING: {len(samples_without_metadata)} analyzed samples have no metadata:")
        for sample in sorted(list(samples_without_metadata)[:10]):  # Show first 10
            print(f"    - {sample}")
        if len(samples_without_metadata) > 10:
            print(f"    ... and {len(samples_without_metadata) - 10} more")

    # Add organism column if not present (infer from ScientificName or BioProject)
    if 'organism' not in filtered_df.columns:
        print("\n  Adding 'organism' column...")

        def infer_organism(row):
            sci_name = str(row.get('ScientificName', ''))
            bioproject = str(row.get('BioProject', ''))

            if 'Salmonella' in sci_name:
                return 'Salmonella'
            elif 'Escherichia' in sci_name or 'E. coli' in sci_name:
                return 'Escherichia'
            elif 'Campylobacter' in sci_name:
                return 'Campylobacter'
            elif 'PRJNA292661' in bioproject:
                return 'Salmonella'
            elif 'PRJNA292663' in bioproject:
                return 'Escherichia'
            elif 'PRJNA292664' in bioproject:
                return 'Campylobacter'
            else:
                return 'Unknown'

        filtered_df['organism'] = filtered_df.apply(infer_organism, axis=1)

    # Add Year column if not present (extract from ReleaseDate or Collection_Date)
    if 'Year' not in filtered_df.columns and 'ReleaseDate' in filtered_df.columns:
        print("  Adding 'Year' column from ReleaseDate...")
        filtered_df['Year'] = pd.to_datetime(filtered_df['ReleaseDate'], errors='coerce').dt.year

    # Show organism breakdown
    if 'organism' in filtered_df.columns:
        print("\n  Organism breakdown:")
        for organism, count in filtered_df['organism'].value_counts().items():
            print(f"    {organism}: {count}")

    # Save filtered metadata
    output_dir = Path(outdir) / 'filtered_samples'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'filtered_samples.csv'

    filtered_df.to_csv(output_file, index=False)
    print(f"\n  ✅ Filtered metadata saved to: {output_file}")
    print(f"  Total samples: {len(filtered_df)}")
    print(f"  Total columns: {len(filtered_df.columns)}")

    return True


def main():
    args = parse_args()

    print("=" * 70)
    print("COMPASS Filtered Metadata Recreation")
    print("=" * 70)
    print(f"Output directory: {args.outdir}")
    print()

    # Step 1: Find analyzed samples
    analyzed_samples = find_analyzed_samples(args.outdir)

    if not analyzed_samples:
        print("\n❌ ERROR: No analyzed samples found!")
        print("   Make sure the output directory contains QUAST results.")
        return 1

    # Step 2: Load original metadata
    original_metadata = load_original_metadata(args.outdir)

    if original_metadata is None or len(original_metadata) == 0:
        print("\n❌ ERROR: Could not load original metadata!")
        return 1

    # Step 3: Create filtered metadata
    success = create_filtered_metadata(analyzed_samples, original_metadata, args.outdir)

    if not success:
        print("\n❌ ERROR: Failed to create filtered metadata!")
        return 1

    print("\n" + "=" * 70)
    print("✅ Success! Filtered metadata recreated.")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Verify the filtered_samples.csv has the correct samples")
    print("  2. Regenerate COMPASS summary report:")
    print(f"     ./bin/generate_compass_summary.py --outdir {args.outdir} \\")
    print(f"         --metadata {args.outdir}/filtered_samples/filtered_samples.csv")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
