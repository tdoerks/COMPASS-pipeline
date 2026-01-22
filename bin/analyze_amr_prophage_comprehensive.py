#!/usr/bin/env python3
"""
Comprehensive AMR-Prophage Analysis

Performs all publication-ready analyses on AMR genes in prophages:
- Gene frequency analysis
- Drug class temporal trends
- Sample-level statistics
- Gene co-occurrence patterns
- Prophage characteristics
- BLAST-ready sequence export

Usage:
    python3 analyze_amr_prophage_comprehensive.py \\
        --csv-2021 /path/to/2021/method3_direct_scan.csv \\
        --csv-2022 /path/to/2022/method3_direct_scan.csv \\
        --csv-2023 /path/to/2023/method3_direct_scan.csv \\
        --csv-2024 /path/to/2024/method3_direct_scan.csv \\
        --vibrant-2021 /path/to/2021/vibrant \\
        --vibrant-2022 /path/to/2022/vibrant \\
        --vibrant-2023 /path/to/2023/vibrant \\
        --vibrant-2024 /path/to/2024/vibrant \\
        --output-dir ./comprehensive_analysis_output

Author: Claude + Tyler Doerks
Date: January 2026
"""

import sys
import os
import csv
import argparse
from pathlib import Path
from collections import Counter, defaultdict
import random
from Bio import SeqIO
from Bio.SeqUtils import GC

def load_amr_data(csv_files):
    """
    Load AMR data from Method 3 CSV files

    Returns: list of dicts with keys: year, sample, gene, class, subclass, method, prophage_contig
    """
    all_data = []

    for year, csv_file in csv_files.items():
        if not Path(csv_file).exists():
            print(f"⚠️  Warning: {csv_file} not found, skipping {year}")
            continue

        print(f"Loading {year} data from {csv_file}...")

        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip rows without AMR genes (gene == 'None')
                if row.get('gene') == 'None' or not row.get('gene'):
                    continue

                all_data.append({
                    'year': year,
                    'sample': row.get('sample', ''),
                    'gene': row.get('gene', ''),
                    'class': row.get('class', ''),
                    'subclass': row.get('subclass', ''),
                    'method': row.get('method', ''),
                    'prophage_contig': row.get('prophage_contig', '')
                })

        print(f"  Loaded {sum(1 for d in all_data if d['year'] == year)} genes from {year}")

    print(f"\n✅ Total AMR genes loaded: {len(all_data)}")
    return all_data


def analyze_gene_frequency(data, output_file):
    """
    Analyze AMR gene frequency across all years
    """
    print("\n" + "="*80)
    print("ANALYSIS 1: Gene Frequency")
    print("="*80)

    gene_counts = Counter(d['gene'] for d in data)
    gene_by_year = defaultdict(lambda: defaultdict(int))

    for d in data:
        gene_by_year[d['gene']][d['year']] += 1

    # Get all years present in data (sorted)
    all_years = sorted(set(d['year'] for d in data))

    # Write results
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['gene', 'total_count'] + all_years + ['num_years_present'])

        for gene, total in gene_counts.most_common():
            counts_by_year = gene_by_year[gene]
            num_years = sum(1 for y in all_years if counts_by_year[y] > 0)

            row = [gene, total] + [counts_by_year.get(y, 0) for y in all_years] + [num_years]
            writer.writerow(row)

    print(f"✅ Gene frequency analysis saved to: {output_file}")
    print(f"   Total unique genes: {len(gene_counts)}")
    print(f"   Top 10 most common genes:")
    for gene, count in gene_counts.most_common(10):
        print(f"     {gene}: {count}")


def analyze_drug_class_trends(data, output_file):
    """
    Analyze drug class distribution over time
    """
    print("\n" + "="*80)
    print("ANALYSIS 2: Drug Class Temporal Trends")
    print("="*80)

    class_by_year = defaultdict(lambda: defaultdict(int))

    for d in data:
        if d['class']:
            class_by_year[d['year']][d['class']] += 1

    # Get all unique classes and years
    all_classes = set()
    for year_data in class_by_year.values():
        all_classes.update(year_data.keys())

    all_years = sorted(class_by_year.keys())

    # Write results
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['drug_class'] + all_years + ['total', 'trend'])

        for drug_class in sorted(all_classes):
            counts = [class_by_year[y].get(drug_class, 0) for y in all_years]
            total = sum(counts)

            # Simple trend: compare last year to first year
            if counts[0] > 0 and counts[-1] > 0:
                if counts[-1] > counts[0] * 1.5:
                    trend = 'increasing'
                elif counts[-1] < counts[0] * 0.67:
                    trend = 'decreasing'
                else:
                    trend = 'stable'
            else:
                trend = 'insufficient_data'

            writer.writerow([drug_class] + counts + [total, trend])

    print(f"✅ Drug class trends saved to: {output_file}")
    print(f"   Drug classes found: {len(all_classes)}")


def analyze_top_samples(data, output_file, top_n=50):
    """
    Identify samples with most AMR genes in prophages
    """
    print("\n" + "="*80)
    print(f"ANALYSIS 3: Top {top_n} Samples by Gene Count")
    print("="*80)

    sample_counts = defaultdict(lambda: {'year': '', 'genes': [], 'classes': set()})

    for d in data:
        key = f"{d['year']}_{d['sample']}"
        sample_counts[key]['year'] = d['year']
        sample_counts[key]['genes'].append(d['gene'])
        if d['class']:
            sample_counts[key]['classes'].add(d['class'])

    # Sort by gene count
    sorted_samples = sorted(
        sample_counts.items(),
        key=lambda x: len(x[1]['genes']),
        reverse=True
    )[:top_n]

    # Write results
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['rank', 'sample', 'year', 'gene_count', 'unique_genes', 'drug_classes', 'genes_list'])

        for rank, (sample_key, info) in enumerate(sorted_samples, 1):
            sample = sample_key.split('_', 1)[1]
            unique_genes = len(set(info['genes']))
            genes_list = ','.join(sorted(set(info['genes'])))

            writer.writerow([
                rank,
                sample,
                info['year'],
                len(info['genes']),
                unique_genes,
                len(info['classes']),
                genes_list
            ])

    print(f"✅ Top samples analysis saved to: {output_file}")
    print(f"   Top 5 samples:")
    for rank, (sample_key, info) in enumerate(sorted_samples[:5], 1):
        sample = sample_key.split('_', 1)[1]
        print(f"     {rank}. {sample} ({info['year']}): {len(info['genes'])} genes")


def analyze_gene_cooccurrence(data, output_file):
    """
    Analyze which AMR genes co-occur in the same samples
    """
    print("\n" + "="*80)
    print("ANALYSIS 4: Gene Co-occurrence Patterns")
    print("="*80)

    # Group genes by sample
    sample_genes = defaultdict(set)
    for d in data:
        key = f"{d['year']}_{d['sample']}"
        sample_genes[key].add(d['gene'])

    # Count co-occurrences
    cooccurrence = defaultdict(int)

    for genes in sample_genes.values():
        if len(genes) > 1:
            # Count all pairs
            genes_list = sorted(genes)
            for i, gene1 in enumerate(genes_list):
                for gene2 in genes_list[i+1:]:
                    pair = f"{gene1}+{gene2}"
                    cooccurrence[pair] += 1

    # Write results
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['gene1', 'gene2', 'cooccurrence_count', 'percent_of_samples'])

        total_samples = len(sample_genes)

        for pair, count in sorted(cooccurrence.items(), key=lambda x: x[1], reverse=True):
            gene1, gene2 = pair.split('+')
            percent = (count / total_samples) * 100

            writer.writerow([gene1, gene2, count, f"{percent:.2f}"])

    print(f"✅ Gene co-occurrence analysis saved to: {output_file}")
    print(f"   Total gene pairs found: {len(cooccurrence)}")
    if cooccurrence:
        top_pair = max(cooccurrence.items(), key=lambda x: x[1])
        print(f"   Most common pair: {top_pair[0]} ({top_pair[1]} samples)")


def analyze_prophage_characteristics(data, vibrant_dirs, output_file):
    """
    Analyze characteristics of AMR-carrying prophages (size, GC content)
    """
    print("\n" + "="*80)
    print("ANALYSIS 5: Prophage Characteristics")
    print("="*80)

    # Get unique sample-prophage combinations
    prophages_to_check = set()
    for d in data:
        if d['prophage_contig']:
            prophages_to_check.add((d['year'], d['sample'], d['prophage_contig']))

    print(f"Analyzing {len(prophages_to_check)} unique prophage sequences...")

    characteristics = []

    for year, sample, contig in prophages_to_check:
        vibrant_dir = vibrant_dirs.get(year)
        if not vibrant_dir or not Path(vibrant_dir).exists():
            continue

        phage_file = Path(vibrant_dir) / f"{sample}_phages.fna"
        if not phage_file.exists():
            continue

        try:
            for record in SeqIO.parse(phage_file, "fasta"):
                if contig in record.id:
                    length = len(record.seq)
                    gc_content = GC(record.seq)

                    # Count AMR genes in this prophage
                    amr_count = sum(1 for d in data
                                   if d['year'] == year
                                   and d['sample'] == sample
                                   and d['prophage_contig'] == contig)

                    characteristics.append({
                        'year': year,
                        'sample': sample,
                        'contig': contig,
                        'length': length,
                        'gc_content': gc_content,
                        'amr_count': amr_count
                    })
                    break
        except Exception as e:
            print(f"  ⚠️  Error processing {sample}: {e}")

    # Write results
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['year', 'sample', 'prophage_contig', 'length_bp', 'gc_content', 'amr_gene_count'])

        for char in characteristics:
            writer.writerow([
                char['year'],
                char['sample'],
                char['contig'],
                char['length'],
                f"{char['gc_content']:.2f}",
                char['amr_count']
            ])

    print(f"✅ Prophage characteristics saved to: {output_file}")
    print(f"   Prophages analyzed: {len(characteristics)}")

    if characteristics:
        lengths = [c['length'] for c in characteristics]
        gc_values = [c['gc_content'] for c in characteristics]

        print(f"   Length range: {min(lengths):,} - {max(lengths):,} bp")
        print(f"   Mean length: {sum(lengths)/len(lengths):,.0f} bp")
        print(f"   GC content range: {min(gc_values):.1f}% - {max(gc_values):.1f}%")
        print(f"   Mean GC: {sum(gc_values)/len(gc_values):.1f}%")


def export_blast_sequences(data, vibrant_dirs, output_file, num_samples=30):
    """
    Export random sample of AMR-carrying prophages for BLAST validation
    """
    print("\n" + "="*80)
    print("ANALYSIS 6: BLAST-Ready Sequence Export")
    print("="*80)

    # Get all unique sample-prophage combinations
    all_prophages = []
    for d in data:
        if d['prophage_contig']:
            all_prophages.append((d['year'], d['sample'], d['prophage_contig'], d['gene']))

    # Group by unique prophage (multiple genes can be in same prophage)
    prophage_genes = defaultdict(list)
    for year, sample, contig, gene in all_prophages:
        key = (year, sample, contig)
        prophage_genes[key].append(gene)

    # Random sample
    unique_prophages = list(prophage_genes.keys())
    sample_size = min(num_samples, len(unique_prophages))
    random.seed(42)  # Reproducible sampling
    sampled = random.sample(unique_prophages, sample_size)

    print(f"Exporting {sample_size} prophages for BLAST validation...")

    sequences = []

    for year, sample, contig in sampled:
        vibrant_dir = vibrant_dirs.get(year)
        if not vibrant_dir or not Path(vibrant_dir).exists():
            continue

        phage_file = Path(vibrant_dir) / f"{sample}_phages.fna"
        if not phage_file.exists():
            continue

        try:
            for record in SeqIO.parse(phage_file, "fasta"):
                if contig in record.id:
                    genes = prophage_genes[(year, sample, contig)]

                    # Rename with metadata
                    record.id = f"{year}_{sample}_{record.id}"
                    record.description = f"year={year} sample={sample} AMR_genes={','.join(genes)} length={len(record.seq)}bp"

                    sequences.append(record)
                    break
        except Exception as e:
            print(f"  ⚠️  Error processing {sample}: {e}")

    # Write FASTA
    SeqIO.write(sequences, output_file, "fasta")

    print(f"✅ BLAST sequences exported to: {output_file}")
    print(f"   Sequences exported: {len(sequences)}")
    print(f"\n📋 Next steps for BLAST validation:")
    print(f"   1. BLAST against local phage database (if available)")
    print(f"   2. Or upload to NCBI BLAST: https://blast.ncbi.nlm.nih.gov/Blast.cgi")
    print(f"   3. Verify top hits are phage/prophage sequences")
    print(f"   4. Expected: E-values < 1e-50, coverage > 70%")


def generate_summary_report(data, output_dir):
    """
    Generate summary statistics for publication
    """
    print("\n" + "="*80)
    print("Generating Summary Report")
    print("="*80)

    summary_file = Path(output_dir) / "summary_statistics.txt"

    # Calculate statistics
    total_genes = len(data)
    unique_genes = len(set(d['gene'] for d in data))
    unique_samples = len(set(f"{d['year']}_{d['sample']}" for d in data))
    unique_classes = len(set(d['class'] for d in data if d['class']))

    genes_by_year = Counter(d['year'] for d in data)
    samples_by_year = defaultdict(set)
    for d in data:
        samples_by_year[d['year']].add(d['sample'])

    # Write summary
    with open(summary_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("COMPREHENSIVE AMR-PROPHAGE ANALYSIS SUMMARY\n")
        f.write("="*80 + "\n\n")

        f.write("OVERALL STATISTICS\n")
        f.write("-"*80 + "\n")
        f.write(f"Total AMR genes in prophages: {total_genes}\n")
        f.write(f"Unique AMR genes: {unique_genes}\n")
        f.write(f"Unique samples with AMR prophages: {unique_samples}\n")
        f.write(f"Drug classes represented: {unique_classes}\n\n")

        f.write("BY YEAR\n")
        f.write("-"*80 + "\n")
        for year in sorted(genes_by_year.keys()):
            f.write(f"{year}:\n")
            f.write(f"  AMR genes: {genes_by_year[year]}\n")
            f.write(f"  Samples: {len(samples_by_year[year])}\n\n")

        f.write("TOP 10 MOST COMMON GENES\n")
        f.write("-"*80 + "\n")
        gene_counts = Counter(d['gene'] for d in data)
        for i, (gene, count) in enumerate(gene_counts.most_common(10), 1):
            f.write(f"{i:2d}. {gene:20s} : {count:4d} occurrences\n")

        f.write("\n")
        f.write("TOP 5 DRUG CLASSES\n")
        f.write("-"*80 + "\n")
        class_counts = Counter(d['class'] for d in data if d['class'])
        for i, (drug_class, count) in enumerate(class_counts.most_common(5), 1):
            percent = (count / total_genes) * 100
            f.write(f"{i}. {drug_class:30s} : {count:4d} ({percent:5.1f}%)\n")

        f.write("\n" + "="*80 + "\n")

    print(f"✅ Summary report saved to: {summary_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Comprehensive AMR-prophage analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  %(prog)s \\
    --csv-2021 /homes/tylerdoe/ecoli_2021_prophage_amr_analysis_20260117/method3_direct_scan.csv \\
    --csv-2022 /homes/tylerdoe/ecoli_prophage_amr_analysis_20260116/ecoli_2022/method3_direct_scan.csv \\
    --csv-2023 /homes/tylerdoe/ecoli_prophage_amr_analysis_20260116/ecoli_2023/method3_direct_scan.csv \\
    --csv-2024 /homes/tylerdoe/ecoli_prophage_amr_analysis_20260116/ecoli_2024/method3_direct_scan.csv \\
    --vibrant-2021 /bulk/tylerdoe/archives/kansas_2021_ecoli/vibrant \\
    --vibrant-2022 /bulk/tylerdoe/archives/kansas_2022_ecoli/vibrant \\
    --vibrant-2023 /bulk/tylerdoe/archives/results_ecoli_2023/vibrant \\
    --vibrant-2024 /bulk/tylerdoe/archives/results_ecoli_all_2024/vibrant \\
    --output-dir ./comprehensive_analysis
        """
    )

    parser.add_argument('--csv-2020', required=False, help='Method 3 CSV for 2020 (optional)')
    parser.add_argument('--csv-2021', required=True, help='Method 3 CSV for 2021')
    parser.add_argument('--csv-2022', required=True, help='Method 3 CSV for 2022')
    parser.add_argument('--csv-2023', required=True, help='Method 3 CSV for 2023')
    parser.add_argument('--csv-2024', required=True, help='Method 3 CSV for 2024')

    parser.add_argument('--vibrant-2020', required=False, help='VIBRANT directory for 2020 (optional)')
    parser.add_argument('--vibrant-2021', required=True, help='VIBRANT directory for 2021')
    parser.add_argument('--vibrant-2022', required=True, help='VIBRANT directory for 2022')
    parser.add_argument('--vibrant-2023', required=True, help='VIBRANT directory for 2023')
    parser.add_argument('--vibrant-2024', required=True, help='VIBRANT directory for 2024')

    parser.add_argument('--output-dir', '-o', default='./comprehensive_analysis_output',
                       help='Output directory (default: ./comprehensive_analysis_output)')

    parser.add_argument('--blast-samples', type=int, default=30,
                       help='Number of prophages to export for BLAST (default: 30)')

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("COMPREHENSIVE AMR-PROPHAGE ANALYSIS")
    print("="*80)
    print(f"Output directory: {output_dir}")
    print()

    # Load data
    csv_files = {}
    vibrant_dirs = {}

    # Add 2020 if provided
    if args.csv_2020:
        csv_files['2020'] = args.csv_2020
    if args.vibrant_2020:
        vibrant_dirs['2020'] = args.vibrant_2020

    # Add 2021-2024 (required)
    csv_files.update({
        '2021': args.csv_2021,
        '2022': args.csv_2022,
        '2023': args.csv_2023,
        '2024': args.csv_2024
    })

    vibrant_dirs.update({
        '2021': args.vibrant_2021,
        '2022': args.vibrant_2022,
        '2023': args.vibrant_2023,
        '2024': args.vibrant_2024
    })

    data = load_amr_data(csv_files)

    if not data:
        print("❌ ERROR: No data loaded!")
        sys.exit(1)

    # Run analyses
    analyze_gene_frequency(data, output_dir / "gene_frequency.csv")
    analyze_drug_class_trends(data, output_dir / "drug_class_trends.csv")
    analyze_top_samples(data, output_dir / "top_samples.csv")
    analyze_gene_cooccurrence(data, output_dir / "gene_cooccurrence.csv")
    analyze_prophage_characteristics(data, vibrant_dirs, output_dir / "prophage_characteristics.csv")
    export_blast_sequences(data, vibrant_dirs, output_dir / "sequences_for_blast.fasta", args.blast_samples)
    generate_summary_report(data, output_dir)

    print("\n" + "="*80)
    print("✅ COMPREHENSIVE ANALYSIS COMPLETE!")
    print("="*80)
    print(f"\n📁 All results saved to: {output_dir}")
    print("\n📊 Output files:")
    print("   - gene_frequency.csv")
    print("   - drug_class_trends.csv")
    print("   - top_samples.csv")
    print("   - gene_cooccurrence.csv")
    print("   - prophage_characteristics.csv")
    print("   - sequences_for_blast.fasta")
    print("   - summary_statistics.txt")
    print("\n🧬 Ready for publication!")


if __name__ == '__main__':
    main()
