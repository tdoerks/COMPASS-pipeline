#!/usr/bin/env python3
"""
Integrate AMR, plasmid, and prophage data by sample ID

Creates master dataset linking mobile genetic elements with
antimicrobial resistance genes for network analysis.

Usage:
    python integrate_data.py \
        --amr amr_2022.csv amr_2023.csv amr_2024.csv \
        --plasmids plasmid_2022.csv plasmid_2023.csv plasmid_2024.csv \
        --prophages prophage_2022.csv prophage_2023.csv prophage_2024.csv \
        --mlst mlst_2022.csv mlst_2023.csv mlst_2024.csv \
        --output integrated_data.csv
"""

import argparse
import pandas as pd
from pathlib import Path
import sys

def load_and_combine_files(file_list, data_type):
    """Load multiple CSV files and combine them"""
    if not file_list:
        print(f"Warning: No {data_type} files provided", file=sys.stderr)
        return pd.DataFrame()

    dfs = []
    for file_path in file_list:
        path = Path(file_path)
        if path.exists():
            df = pd.read_csv(path)
            dfs.append(df)
            print(f"Loaded {len(df)} {data_type} entries from {path.name}")
        else:
            print(f"Warning: File {path} not found", file=sys.stderr)

    if dfs:
        combined = pd.concat(dfs, ignore_index=True)
        print(f"Total {data_type} entries: {len(combined)}")
        return combined
    return pd.DataFrame()

def create_sample_summary(amr_df, plasmid_df, prophage_df, mlst_df):
    """Create per-sample summary linking all data types"""

    # Get all unique samples
    all_samples = set()
    if len(amr_df) > 0:
        all_samples.update(amr_df['sample_id'].unique())
    if len(plasmid_df) > 0:
        all_samples.update(plasmid_df['sample_id'].unique())
    if len(prophage_df) > 0:
        all_samples.update(prophage_df['sample_id'].unique())
    if len(mlst_df) > 0:
        all_samples.update(mlst_df['sample_id'].unique())

    print(f"\nFound {len(all_samples)} unique samples across all datasets")

    summaries = []

    for sample_id in all_samples:
        summary = {'sample_id': sample_id}

        # MLST data
        if len(mlst_df) > 0:
            mlst_sample = mlst_df[mlst_df['sample_id'] == sample_id]
            if len(mlst_sample) > 0:
                summary['year'] = mlst_sample.iloc[0]['year']
                summary['mlst_scheme'] = mlst_sample.iloc[0].get('scheme', '')
                summary['sequence_type'] = mlst_sample.iloc[0].get('st', '')

        # AMR data
        if len(amr_df) > 0:
            amr_sample = amr_df[amr_df['sample_id'] == sample_id]
            summary['num_amr_genes'] = len(amr_sample)
            summary['amr_classes'] = ','.join(amr_sample['class'].dropna().unique())
            summary['amr_genes'] = ','.join(amr_sample['gene_symbol'].dropna().unique())

        # Plasmid data
        if len(plasmid_df) > 0:
            plasmid_sample = plasmid_df[plasmid_df['sample_id'] == sample_id]
            summary['num_plasmids'] = len(plasmid_sample)

            # Extract replicon types
            all_reps = []
            for reps in plasmid_sample['rep_types'].dropna():
                if reps:
                    all_reps.extend(str(reps).split(','))
            summary['replicon_types'] = ','.join(set(all_reps))

            # Mobility
            mobilities = plasmid_sample['predicted_mobility'].dropna().unique()
            summary['plasmid_mobility'] = ','.join(mobilities)

        # Prophage data
        if len(prophage_df) > 0:
            prophage_sample = prophage_df[prophage_df['sample_id'] == sample_id]
            summary['num_prophages'] = len(prophage_sample)
            summary['prophage_scaffolds'] = ','.join(prophage_sample['scaffold'].dropna().unique())

        summaries.append(summary)

    return pd.DataFrame(summaries)

def create_cooccurrence_matrix(summary_df):
    """Create co-occurrence matrices for plasmid-AMR associations"""

    # Plasmid replicon types vs AMR classes
    cooccurrence = []

    for _, row in summary_df.iterrows():
        sample_id = row['sample_id']
        reps = str(row.get('replicon_types', '')).split(',') if row.get('replicon_types') else []
        amr_classes = str(row.get('amr_classes', '')).split(',') if row.get('amr_classes') else []

        for rep in reps:
            rep = rep.strip()
            if rep and rep != 'nan':
                for amr_class in amr_classes:
                    amr_class = amr_class.strip()
                    if amr_class and amr_class != 'nan':
                        cooccurrence.append({
                            'sample_id': sample_id,
                            'replicon_type': rep,
                            'amr_class': amr_class
                        })

    return pd.DataFrame(cooccurrence)

def main():
    parser = argparse.ArgumentParser(description='Integrate multi-year COMPASS data')
    parser.add_argument('--amr', nargs='+', required=True,
                       help='AMR CSV files (from parse_amrfinder.py)')
    parser.add_argument('--plasmids', nargs='+', required=True,
                       help='Plasmid CSV files (from parse_mobsuite.py)')
    parser.add_argument('--prophages', nargs='+', required=True,
                       help='Prophage CSV files (from parse_vibrant.py)')
    parser.add_argument('--mlst', nargs='+', required=True,
                       help='MLST CSV files (from parse_mlst.py)')
    parser.add_argument('--output', required=True,
                       help='Output CSV file for integrated summary')

    args = parser.parse_args()

    print("=" * 60)
    print("COMPASS Data Integration Pipeline")
    print("=" * 60)

    # Load all data
    print("\nLoading AMR data...")
    amr_df = load_and_combine_files(args.amr, 'AMR')

    print("\nLoading plasmid data...")
    plasmid_df = load_and_combine_files(args.plasmids, 'plasmid')

    print("\nLoading prophage data...")
    prophage_df = load_and_combine_files(args.prophages, 'prophage')

    print("\nLoading MLST data...")
    mlst_df = load_and_combine_files(args.mlst, 'MLST')

    # Create integrated summary
    print("\n" + "=" * 60)
    print("Creating integrated sample summary...")
    print("=" * 60)

    summary_df = create_sample_summary(amr_df, plasmid_df, prophage_df, mlst_df)

    # Save summary
    summary_df.to_csv(args.output, index=False)
    print(f"\n✓ Integrated summary saved to {args.output}")
    print(f"  {len(summary_df)} samples")

    # Create co-occurrence matrix
    print("\nCreating plasmid-AMR co-occurrence matrix...")
    cooccurrence_df = create_cooccurrence_matrix(summary_df)
    cooccurrence_output = args.output.replace('.csv', '_cooccurrence.csv')
    cooccurrence_df.to_csv(cooccurrence_output, index=False)
    print(f"✓ Co-occurrence matrix saved to {cooccurrence_output}")
    print(f"  {len(cooccurrence_df)} plasmid-AMR associations")

    # Print summary statistics
    print("\n" + "=" * 60)
    print("Summary Statistics")
    print("=" * 60)

    if len(summary_df) > 0:
        print(f"\nTotal samples: {len(summary_df)}")

        if 'year' in summary_df.columns:
            print(f"\nSamples by year:")
            print(summary_df['year'].value_counts().sort_index())

        if 'num_amr_genes' in summary_df.columns:
            print(f"\nAMR genes per sample:")
            print(f"  Mean: {summary_df['num_amr_genes'].mean():.2f}")
            print(f"  Median: {summary_df['num_amr_genes'].median():.0f}")
            print(f"  Max: {summary_df['num_amr_genes'].max():.0f}")

        if 'num_plasmids' in summary_df.columns:
            print(f"\nPlasmids per sample:")
            print(f"  Mean: {summary_df['num_plasmids'].mean():.2f}")
            print(f"  Samples with plasmids: {(summary_df['num_plasmids'] > 0).sum()}")

        if 'num_prophages' in summary_df.columns:
            print(f"\nProphages per sample:")
            print(f"  Mean: {summary_df['num_prophages'].mean():.2f}")
            print(f"  Samples with prophages: {(summary_df['num_prophages'] > 0).sum()}")

    print("\n" + "=" * 60)
    print("Integration complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
