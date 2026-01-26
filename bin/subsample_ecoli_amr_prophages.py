#!/usr/bin/env python3
"""
Subsample E. coli AMR-Carrying Prophages for Phylogenetic Analysis

With 3,918 AMR-carrying prophages, phylogenetic tree construction is too slow
and memory-intensive. This script intelligently subsamples to a manageable
number while preserving temporal diversity.

Strategies:
1. Representative sampling by year (balanced across 2021-2024)
2. Top N most complete prophages (longest sequences)
3. By year sampling (N per year)
4. Random stratified sampling

Usage:
    python3 subsample_ecoli_amr_prophages.py --strategy by_year --n-per-year 100
    python3 subsample_ecoli_amr_prophages.py --strategy top --n 500
"""

import argparse
import csv
import random
from pathlib import Path
from Bio import SeqIO
from collections import defaultdict


def load_metadata(metadata_tsv):
    """Load E. coli AMR-prophage metadata"""
    print(f"Loading metadata from {metadata_tsv}...")

    prophages = []
    with open(metadata_tsv) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            # E. coli metadata has: prophage_id, year, sample_id, amr_carrying, length_bp, original_id
            prophages.append({
                'prophage_id': row['prophage_id'],
                'sample_id': row['sample_id'],
                'year': int(row['year']),
                'organism': 'Escherichia coli',  # All are E. coli
                'length': int(row['length_bp']),
                'amr_carrying': row.get('amr_carrying', 'yes'),
                'original_id': row.get('original_id', '')
            })

    print(f"  Loaded {len(prophages)} AMR-carrying E. coli prophages")
    return prophages


def subsample_by_year(prophages, n_per_year):
    """Sample N prophages per year"""
    print(f"\nSubsampling {n_per_year} prophages per year...")

    by_year = defaultdict(list)
    for p in prophages:
        if p['year']:
            by_year[p['year']].append(p)

    selected = []
    for year in sorted(by_year.keys()):
        year_prophages = by_year[year]
        # Sort by length (longest = most complete)
        year_prophages.sort(key=lambda x: x['length'], reverse=True)

        # Take top N
        n = min(n_per_year, len(year_prophages))
        selected.extend(year_prophages[:n])

    print(f"  Selected {len(selected)} prophages")
    return selected


def subsample_top_complete(prophages, n):
    """Select top N most complete prophages"""
    print(f"\nSelecting top {n} most complete prophages...")

    # Sort by length (proxy for completeness)
    sorted_prophages = sorted(prophages, key=lambda x: x['length'], reverse=True)

    selected = sorted_prophages[:n]
    print(f"  Selected {len(selected)} prophages (lengths: {selected[0]['length']}-{selected[-1]['length']} bp)")
    return selected


def subsample_representative(prophages, n):
    """Stratified sampling across years (balanced 2021-2024)"""
    print(f"\nPerforming representative sampling (target: {n})...")

    # Group by year only (all are E. coli)
    groups = defaultdict(list)
    for p in prophages:
        groups[p['year']].append(p)

    # Calculate samples per year
    n_years = len(groups)
    per_year = max(1, n // n_years)

    print(f"  Sampling {per_year} prophages per year from {n_years} years")

    selected = []
    for year in sorted(groups.keys()):
        year_prophages = groups[year]
        # Sort by length (longest = most complete)
        year_prophages.sort(key=lambda x: x['length'], reverse=True)

        # Take top per_year from this year
        n_sample = min(per_year, len(year_prophages))
        selected.extend(year_prophages[:n_sample])
        print(f"    {year}: selected {n_sample} of {len(year_prophages)} prophages")

    # If we need more, add longest remaining
    if len(selected) < n:
        remaining = [p for p in prophages if p not in selected]
        remaining.sort(key=lambda x: x['length'], reverse=True)
        additional = min(n - len(selected), len(remaining))
        selected.extend(remaining[:additional])
        print(f"    Additional: selected {additional} longest remaining prophages")

    print(f"  Total selected: {len(selected)} prophages")
    return selected


def subsample_random(prophages, n):
    """Random sampling"""
    print(f"\nRandom sampling {n} prophages...")

    selected = random.sample(prophages, min(n, len(prophages)))
    print(f"  Selected {len(selected)} prophages")
    return selected


def extract_sequences(selected_prophages, input_fasta, output_fasta):
    """Extract selected sequences from FASTA"""
    print(f"\nExtracting sequences from {input_fasta}...")

    selected_ids = {p['prophage_id'] for p in selected_prophages}

    extracted = []
    for record in SeqIO.parse(input_fasta, "fasta"):
        if record.id in selected_ids:
            extracted.append(record)

    SeqIO.write(extracted, output_fasta, "fasta")
    print(f"  ✅ Extracted {len(extracted)} sequences to {output_fasta}")

    return len(extracted)


def save_metadata(selected_prophages, output_tsv):
    """Save metadata for selected E. coli AMR-prophages"""
    print(f"\nSaving metadata to {output_tsv}...")

    with open(output_tsv, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        # Match E. coli metadata format
        writer.writerow(['prophage_id', 'year', 'sample_id', 'amr_carrying', 'length_bp', 'original_id'])

        for p in selected_prophages:
            writer.writerow([
                p['prophage_id'],
                p['year'],
                p['sample_id'],
                p.get('amr_carrying', 'yes'),
                p['length'],
                p.get('original_id', '')
            ])

    print(f"  ✅ Saved metadata for {len(selected_prophages)} prophages")


def print_summary(selected_prophages):
    """Print summary statistics for E. coli AMR-prophages"""
    print("\n" + "=" * 70)
    print("E. coli AMR-Prophage Subsampling Summary")
    print("=" * 70)

    print(f"\nTotal prophages: {len(selected_prophages)}")
    print(f"Organism: Escherichia coli (all)")
    print(f"AMR-carrying: yes (all)")

    # By year
    by_year = defaultdict(int)
    for p in selected_prophages:
        by_year[p['year']] += 1

    print("\nProphages by year:")
    for year in sorted(by_year.keys()):
        print(f"  {year}: {by_year[year]}")

    # Length stats
    lengths = [p['length'] for p in selected_prophages]
    print(f"\nLength statistics:")
    print(f"  Mean: {sum(lengths)/len(lengths):.0f} bp")
    print(f"  Min: {min(lengths):,} bp")
    print(f"  Max: {max(lengths):,} bp")

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Subsample E. coli AMR-prophages for phylogenetic analysis')
    parser.add_argument('--strategy', choices=['representative', 'top', 'by_year', 'random'],
                       default='by_year',
                       help='Subsampling strategy (default: by_year)')
    parser.add_argument('--n', type=int, default=400,
                       help='Number of prophages to select for representative/top/random (default: 400)')
    parser.add_argument('--n-per-year', type=int, default=100,
                       help='Number per year for by_year strategy (default: 100, yields ~400 total for 2021-2024)')
    parser.add_argument('--input-fasta', required=True,
                       help='Input FASTA file (amr_prophages.fasta)')
    parser.add_argument('--input-metadata', required=True,
                       help='Input metadata TSV file (amr_prophage_metadata.tsv)')
    parser.add_argument('--output-fasta', required=True,
                       help='Output FASTA file (amr_prophages_subsample.fasta)')
    parser.add_argument('--output-metadata', required=True,
                       help='Output metadata TSV file (amr_prophage_subsample_metadata.tsv)')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility (default: 42)')

    args = parser.parse_args()

    # Set random seed
    random.seed(args.seed)

    # Expand paths (keep as strings if they're already absolute)
    input_fasta = Path(args.input_fasta).expanduser() if args.input_fasta.startswith('~') else Path(args.input_fasta)
    input_metadata = Path(args.input_metadata).expanduser() if args.input_metadata.startswith('~') else Path(args.input_metadata)
    output_fasta = Path(args.output_fasta).expanduser() if args.output_fasta.startswith('~') else Path(args.output_fasta)
    output_metadata = Path(args.output_metadata).expanduser() if args.output_metadata.startswith('~') else Path(args.output_metadata)

    print("=" * 70)
    print("E. coli AMR-Prophage Subsampling for Phylogeny")
    print("=" * 70)

    # Load metadata
    prophages = load_metadata(input_metadata)

    # Subsample
    if args.strategy == 'representative':
        selected = subsample_representative(prophages, args.n)
    elif args.strategy == 'top':
        selected = subsample_top_complete(prophages, args.n)
    elif args.strategy == 'by_year':
        selected = subsample_by_year(prophages, args.n_per_year)
    elif args.strategy == 'random':
        selected = subsample_random(prophages, args.n)

    # Extract sequences
    extract_sequences(selected, input_fasta, output_fasta)

    # Save metadata
    save_metadata(selected, output_metadata)

    # Print summary
    print_summary(selected)

    print("\n" + "=" * 70)
    print("✅ Subsampling complete!")
    print("=" * 70)
    print(f"\nOutput files:")
    print(f"  - {output_fasta}")
    print(f"  - {output_metadata}")
    print(f"\nNext steps:")
    print(f"  1. Align with MAFFT (2-5 hours for {len(selected)} sequences):")
    print(f"     mafft --auto --thread 16 {output_fasta.name} > subsample_aligned.fasta")
    print(f"  2. Build tree with FastTree (~30-60 min):")
    print(f"     FastTree -nt -gtr -gamma -boot 1000 subsample_aligned.fasta > subsample_tree.nwk")
    print(f"  3. Clean tree format:")
    print(f"     bash clean_phylo_tree.sh subsample_tree.nwk")
    print(f"  4. Visualize with iTOL: https://itol.embl.de/")
    print("=" * 70)


if __name__ == '__main__':
    main()
