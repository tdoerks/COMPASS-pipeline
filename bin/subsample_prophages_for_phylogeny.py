#!/usr/bin/env python3
"""
Subsample Prophages for Phylogenetic Analysis

With 3,369 prophages, phylogenetic tree construction can be very slow.
This script intelligently subsamples to a manageable number while
preserving diversity.

Strategies:
1. Representative sampling by year
2. Top N most complete prophages
3. Prophages that show cross-sample movement
4. Random stratified sampling

Usage:
    python3 subsample_prophages_for_phylogeny.py --strategy representative --n 200
"""

import argparse
import csv
import random
from pathlib import Path
from Bio import SeqIO
from collections import defaultdict


def load_metadata(metadata_tsv):
    """Load prophage metadata"""
    print(f"Loading metadata from {metadata_tsv}...")

    prophages = []
    with open(metadata_tsv) as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            prophages.append({
                'prophage_id': row['prophage_id'],
                'sample_id': row['sample_id'],
                'year': int(row['year']) if row['year'] != 'Unknown' else None,
                'organism': row['organism'],
                'length': int(row['length_bp']),
                'quality': row.get('quality', row.get('completeness', 'Unknown'))
            })

    print(f"  Loaded {len(prophages)} prophages")
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
    """Stratified sampling across years and organisms"""
    print(f"\nPerforming representative sampling (target: {n})...")

    # Group by year and organism
    groups = defaultdict(list)
    for p in prophages:
        key = (p['year'], p['organism'])
        groups[key].append(p)

    # Calculate samples per group
    n_groups = len(groups)
    per_group = max(1, n // n_groups)

    selected = []
    for (year, organism), group_prophages in groups.items():
        # Sort by length
        group_prophages.sort(key=lambda x: x['length'], reverse=True)

        # Take top per_group from this group
        n_sample = min(per_group, len(group_prophages))
        selected.extend(group_prophages[:n_sample])

    # If we need more, add highest quality remaining
    if len(selected) < n:
        remaining = [p for p in prophages if p not in selected]
        remaining.sort(key=lambda x: x['length'], reverse=True)
        additional = min(n - len(selected), len(remaining))
        selected.extend(remaining[:additional])

    print(f"  Selected {len(selected)} prophages from {n_groups} groups")
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
    """Save metadata for selected prophages"""
    print(f"\nSaving metadata to {output_tsv}...")

    with open(output_tsv, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['prophage_id', 'sample_id', 'year', 'organism', 'length_bp', 'quality'])

        for p in selected_prophages:
            writer.writerow([
                p['prophage_id'],
                p['sample_id'],
                p['year'] if p['year'] else 'Unknown',
                p['organism'],
                p['length'],
                p['quality']
            ])

    print(f"  ✅ Saved metadata for {len(selected_prophages)} prophages")


def print_summary(selected_prophages):
    """Print summary statistics"""
    print("\n" + "=" * 70)
    print("Subsampling Summary")
    print("=" * 70)

    # By year
    by_year = defaultdict(int)
    for p in selected_prophages:
        year = p['year'] if p['year'] else 'Unknown'
        by_year[year] += 1

    print("\nProphages by year:")
    for year in sorted(by_year.keys(), key=lambda x: (isinstance(x, str), x)):
        print(f"  {year}: {by_year[year]}")

    # By organism
    by_organism = defaultdict(int)
    for p in selected_prophages:
        by_organism[p['organism']] += 1

    print("\nProphages by organism:")
    for organism, count in sorted(by_organism.items(), key=lambda x: x[1], reverse=True):
        print(f"  {organism}: {count}")

    # Length stats
    lengths = [p['length'] for p in selected_prophages]
    print(f"\nLength statistics:")
    print(f"  Mean: {sum(lengths)/len(lengths):.0f} bp")
    print(f"  Min: {min(lengths)} bp")
    print(f"  Max: {max(lengths)} bp")

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description='Subsample prophages for phylogenetic analysis')
    parser.add_argument('--strategy', choices=['representative', 'top', 'by_year', 'random'],
                       default='representative',
                       help='Subsampling strategy (default: representative)')
    parser.add_argument('--n', type=int, default=200,
                       help='Number of prophages to select (default: 200)')
    parser.add_argument('--n-per-year', type=int, default=40,
                       help='Number per year (for by_year strategy, default: 40)')
    parser.add_argument('--input-fasta',
                       default='~/compass_kansas_results/publication_analysis/phylogeny/complete_prophages.fasta',
                       help='Input FASTA file')
    parser.add_argument('--input-metadata',
                       default='~/compass_kansas_results/publication_analysis/phylogeny/prophage_metadata.tsv',
                       help='Input metadata TSV file')
    parser.add_argument('--output-fasta',
                       default='~/compass_kansas_results/publication_analysis/phylogeny/subsample_prophages.fasta',
                       help='Output FASTA file')
    parser.add_argument('--output-metadata',
                       default='~/compass_kansas_results/publication_analysis/phylogeny/subsample_metadata.tsv',
                       help='Output metadata TSV file')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed (default: 42)')

    args = parser.parse_args()

    # Set random seed
    random.seed(args.seed)

    # Expand paths
    input_fasta = Path(args.input_fasta).expanduser()
    input_metadata = Path(args.input_metadata).expanduser()
    output_fasta = Path(args.output_fasta).expanduser()
    output_metadata = Path(args.output_metadata).expanduser()

    print("=" * 70)
    print("Prophage Subsampling for Phylogeny")
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
    print(f"\nNext steps:")
    print(f"  1. Align: mafft --auto --thread 16 {output_fasta} > subsample_aligned.fasta")
    print(f"  2. Build tree: iqtree2 -s subsample_aligned.fasta -m MFP -bb 1000 -nt 16")
    print(f"  3. Visualize with iTOL or FigTree")
    print("=" * 70)


if __name__ == '__main__':
    main()
