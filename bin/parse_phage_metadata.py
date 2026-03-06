#!/usr/bin/env python3
"""
Parse phage metadata from Excel file and create lookup tables for report integration.

This script extracts phage identification information from the metadata file
and creates CSV lookup tables that can be merged with pipeline results.
"""

import pandas as pd
import sys
import argparse
from pathlib import Path


def parse_metadata(metadata_file, output_prefix="phage_metadata"):
    """
    Parse the metadata Excel file and extract relevant phage information.

    Args:
        metadata_file: Path to metadata.xlsx file
        output_prefix: Prefix for output CSV files
    """

    # Read prophage metadata (Table 1)
    print(f"Reading metadata from {metadata_file}...")
    try:
        # Try reading Table 1 first (prophage metadata)
        phage_df = pd.read_excel(metadata_file, sheet_name='Table 1', header=0)
        print(f"Loaded {len(phage_df)} prophage records from Table 1")
    except Exception as e:
        print(f"Error reading Excel Table 1: {e}")
        print("Trying to read as CSV...")
        phage_df = pd.read_csv(metadata_file)
        print(f"Loaded {len(phage_df)} prophage records from CSV")

    # Clean up the data - replace 'NA' strings with actual NaN
    phage_df = phage_df.replace('NA', pd.NA)

    # Create main lookup table with key phage information
    # Use contig_id as the primary key for matching with VIBRANT results
    phage_lookup = phage_df[[
        'file_name', 'source_file', 'contig_id', 'seq_name',
        'lineage_genomad', 'host_domain', 'phylum', 'class', 'order', 'family', 'genus', 'species',
        'environment', 'ncbi_isolation_source',
        'contig_length', 'provirus', 'gene_count', 'viral_genes', 'host_genes',
        'checkv_quality', 'miuvig_quality', 'completeness', 'completeness_method',
        'latitude', 'longitude', 'accession', 'ncbi_country'
    ]].copy()

    # Save full lookup table
    lookup_file = f"{output_prefix}_lookup.csv"
    phage_lookup.to_csv(lookup_file, index=False)
    print(f"Created phage lookup table: {lookup_file}")
    print(f"  - {len(phage_lookup)} phage records")

    # Create simplified summary for report integration
    phage_summary = phage_df[[
        'contig_id', 'file_name', 'host_domain', 'phylum', 'genus',
        'environment', 'checkv_quality', 'completeness', 'viral_genes'
    ]].copy()

    summary_file = f"{output_prefix}_summary.csv"
    phage_summary.to_csv(summary_file, index=False)
    print(f"Created phage summary table: {summary_file}")

    # Print summary statistics
    print("\nMetadata Summary:")
    print(f"  Total phages: {len(phage_df)}")
    print(f"  Host domains: {phage_df['host_domain'].value_counts().to_dict()}")
    print(f"  Top 5 phyla: {phage_df['phylum'].value_counts().head(5).to_dict()}")
    print(f"  Quality distribution:")
    print(f"    {phage_df['checkv_quality'].value_counts().to_dict()}")
    print(f"  Environments with data: {phage_df['environment'].notna().sum()}")
    print(f"  Average completeness: {phage_df['completeness'].mean():.2f}%")

    # Read AMG metadata (Table 2) if available
    amg_summary = None
    try:
        amg_df = pd.read_excel(metadata_file, sheet_name='Table 2', header=0)
        print(f"\nLoaded {len(amg_df)} AMG records from Table 2")

        # Create AMG summary by scaffold
        amg_summary = amg_df.groupby('scaffold').agg({
            'KO': 'count',  # Count of KO annotations
            'KO name': lambda x: '; '.join([str(i) for i in x.dropna().unique()][:5]),  # Top 5 KO names
            'Pfam': 'count',  # Count of Pfam annotations
            'VOG': 'count',  # Count of VOG annotations
        }).reset_index()

        amg_summary.columns = ['contig_id', 'ko_count', 'ko_names', 'pfam_count', 'vog_count']

        # Save AMG summary
        amg_file = f"{output_prefix}_amg_summary.csv"
        amg_summary.to_csv(amg_file, index=False)
        print(f"Created AMG summary table: {amg_file}")
        print(f"  - {len(amg_summary)} scaffolds with AMG annotations")
    except Exception as e:
        print(f"\nNote: Could not read Table 2 (AMG data): {e}")

    return phage_lookup, phage_summary, amg_summary


def match_vibrant_to_metadata(vibrant_results_dir, metadata_lookup):
    """
    Match VIBRANT results to metadata based on contig IDs.

    Args:
        vibrant_results_dir: Directory containing VIBRANT results
        metadata_lookup: DataFrame with phage metadata lookup table
    """
    # This function would be called from the combine_results process
    # to merge VIBRANT output with metadata
    pass


def main():
    parser = argparse.ArgumentParser(
        description='Parse phage metadata and create lookup tables for COMPASS pipeline'
    )
    parser.add_argument('metadata_file',
                       help='Path to metadata.xlsx or metadata.csv file')
    parser.add_argument('-o', '--output-prefix',
                       default='phage_metadata',
                       help='Prefix for output files (default: phage_metadata)')
    parser.add_argument('--sheet-name',
                       default='Table 2',
                       help='Sheet name to read from Excel (default: Table 2)')

    args = parser.parse_args()

    # Check if file exists
    if not Path(args.metadata_file).exists():
        print(f"Error: File not found: {args.metadata_file}")
        sys.exit(1)

    # Parse metadata
    try:
        phage_lookup, phage_summary, amg_summary = parse_metadata(args.metadata_file, args.output_prefix)
        print("\n✅ Metadata parsing completed successfully!")
        print(f"\nOutput files created:")
        print(f"  - {args.output_prefix}_lookup.csv (full metadata)")
        print(f"  - {args.output_prefix}_summary.csv (simplified for reports)")
        if amg_summary is not None:
            print(f"  - {args.output_prefix}_amg_summary.csv (AMG annotations)")
    except Exception as e:
        print(f"\n❌ Error parsing metadata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
