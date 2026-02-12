#!/usr/bin/env python3
"""
Simple ETEC Validation Comparison - ABRicate Version

Compare COMPASS ABRicate results against paper-reported genes (Figures S12, S13, Table S4).
Uses ABRicate CARD database results instead of AMRFinder.

Usage:
    ./bin/compare_etec_validation_abricate.py \\
        data/validation/etec_results \\
        --output figures/etec_validation
"""

import os
import sys
import csv
import argparse
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Sample list
ETEC_SAMPLES = ['E925', 'E1649', 'E36', 'E2980', 'E1441', 'E1779', 'E562', 'E1373']

# Expected prophage counts from Table S4
TABLE_S4_PROPHAGE_COUNTS = {
    'E925': 5,
    'E1649': 4,
    'E36': 13,
    'E2980': 7,
    'E1441': 4,
    'E1779': 9,
    'E562': 2,
    'E1373': 3
}


def parse_abricate_results(results_dir, sample):
    """Parse ABRicate CARD results for AMR genes."""
    abricate_file = Path(results_dir) / "abricate" / f"{sample}_card.tsv"

    if not abricate_file.exists():
        return set(), 0

    genes = set()
    with open(abricate_file, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue

            fields = line.strip().split('\t')
            if len(fields) < 6:
                continue

            gene = fields[5]  # GENE column
            coverage = float(fields[9])  # %COVERAGE column
            identity = float(fields[10])  # %IDENTITY column

            # Only count high-confidence hits (>80% coverage and >80% identity)
            if coverage >= 80.0 and identity >= 80.0:
                genes.add(gene)

    return genes, len(genes)


def parse_vibrant_results(results_dir, sample):
    """Parse VIBRANT prophage results."""
    vibrant_dir = Path(results_dir) / "vibrant" / f"{sample}_vibrant"

    if not vibrant_dir.exists():
        return 0

    summary_files = list(vibrant_dir.glob("**/VIBRANT_summary_results*.tsv"))

    if not summary_files:
        return 0

    prophage_count = 0
    for summary_file in summary_files:
        with open(summary_file, 'r') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                scaffold = row.get('scaffold', row.get('fragment', ''))
                if scaffold:
                    prophage_count += 1

    return prophage_count


def generate_comparison_table(results_dir, output_dir):
    """Generate CSV comparison table: genes x samples."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Parse all samples
    all_data = {}
    for sample in ETEC_SAMPLES:
        detected_genes, count = parse_abricate_results(results_dir, sample)
        all_data[sample] = detected_genes

    # Get union of all detected genes
    all_detected = set()
    for genes in all_data.values():
        all_detected.update(genes)

    # Write comparison table
    output_csv = output_dir / "amr_gene_comparison.csv"

    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow(['Gene'] + ETEC_SAMPLES + ['Total_Samples'])

        # Sort genes alphabetically
        for gene in sorted(all_detected):
            row = [gene]

            # Check presence in each sample
            count = 0
            for sample in ETEC_SAMPLES:
                present = gene in all_data[sample]
                row.append('Yes' if present else 'No')
                if present:
                    count += 1

            row.append(count)
            writer.writerow(row)

    print(f"✓ AMR gene comparison table: {output_csv}")

    return output_csv


def plot_gene_counts_comparison(results_dir, output_dir):
    """Simple bar chart: AMR gene counts per strain."""

    counts = {}
    for sample in ETEC_SAMPLES:
        _, count = parse_abricate_results(results_dir, sample)
        counts[sample] = count

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    samples = list(counts.keys())
    values = [counts[s] for s in samples]

    bars = ax.bar(samples, values, color='#7B68A6', alpha=0.8)

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom', fontsize=10)

    ax.set_xlabel('ETEC Strain', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of AMR Genes Detected', fontsize=12, fontweight='bold')
    ax.set_title('AMR Gene Counts by Strain\n(COMPASS ABRicate CARD Results)',
                 fontsize=14, fontweight='bold', pad=20)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()

    output_file = Path(output_dir) / "amr_gene_counts.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ AMR gene counts bar chart: {output_file}")

    return counts


def plot_prophage_comparison(results_dir, output_dir):
    """Compare prophage counts: COMPASS vs. Paper Table S4."""

    compass_counts = {}
    for sample in ETEC_SAMPLES:
        count = parse_vibrant_results(results_dir, sample)
        compass_counts[sample] = count

    # Create comparison figure
    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(ETEC_SAMPLES))
    width = 0.35

    paper_values = [TABLE_S4_PROPHAGE_COUNTS[s] for s in ETEC_SAMPLES]
    compass_values = [compass_counts[s] for s in ETEC_SAMPLES]

    bars1 = ax.bar(x - width/2, paper_values, width, label='Paper (Table S4)',
                   color='#D4A5A5', alpha=0.8)
    bars2 = ax.bar(x + width/2, compass_values, width, label='COMPASS (VIBRANT)',
                   color='#7B68A6', alpha=0.8)

    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontsize=9)

    ax.set_xlabel('ETEC Strain', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Prophages', fontsize=12, fontweight='bold')
    ax.set_title('Prophage Count Comparison\nCOMPASS vs. Paper Table S4',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(ETEC_SAMPLES)
    ax.legend(loc='upper right', frameon=False, fontsize=11)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', alpha=0.3, linestyle='--')

    plt.tight_layout()

    output_file = Path(output_dir) / "prophage_count_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Prophage comparison chart: {output_file}")

    # Calculate accuracy
    differences = {s: abs(compass_counts[s] - TABLE_S4_PROPHAGE_COUNTS[s])
                   for s in ETEC_SAMPLES}

    return compass_counts, differences


def plot_simple_heatmap(results_dir, output_dir):
    """Simple presence/absence heatmap (no dendrogram) - Figure S12 style."""

    # Parse all samples
    all_data = {}
    all_genes = set()

    for sample in ETEC_SAMPLES:
        detected_genes, _ = parse_abricate_results(results_dir, sample)
        all_data[sample] = detected_genes
        all_genes.update(detected_genes)

    # Sort genes alphabetically
    sorted_genes = sorted(all_genes)

    # Create presence/absence matrix
    matrix = []
    for sample in ETEC_SAMPLES:
        row = [1 if gene in all_data[sample] else 0 for gene in sorted_genes]
        matrix.append(row)

    matrix = np.array(matrix)

    # Create figure
    fig, ax = plt.subplots(figsize=(20, 8))

    # Plot heatmap (purple for present, white for absent - like paper)
    cmap = plt.cm.colors.ListedColormap(['white', '#7B68A6'])
    im = ax.imshow(matrix, cmap=cmap, aspect='auto', interpolation='nearest')

    # Set ticks
    ax.set_yticks(np.arange(len(ETEC_SAMPLES)))
    ax.set_yticklabels(ETEC_SAMPLES, fontsize=11)

    ax.set_xticks(np.arange(len(sorted_genes)))
    ax.set_xticklabels(sorted_genes, rotation=90, ha='right', fontsize=7)

    ax.set_xlabel('AMR Genes (ABRicate CARD)', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_ylabel('ETEC Strain', fontsize=12, fontweight='bold')
    ax.set_title('AMR Gene Presence/Absence\n(Figure S12 Style - COMPASS ABRicate Results)',
                 fontsize=14, fontweight='bold', pad=20)

    # Add grid
    ax.set_xticks(np.arange(len(sorted_genes))+0.5, minor=True)
    ax.set_yticks(np.arange(len(ETEC_SAMPLES))+0.5, minor=True)
    ax.grid(which='minor', color='gray', linestyle='-', linewidth=0.5)

    # Legend
    legend_elements = [
        mpatches.Patch(color='#7B68A6', label='Present'),
        mpatches.Patch(color='white', label='Absent', edgecolor='gray')
    ]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1),
             frameon=False, fontsize=10)

    plt.tight_layout()

    output_file = Path(output_dir) / "figure_s12_style_heatmap.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Figure S12-style heatmap: {output_file}")

    return matrix


def generate_summary_statistics(results_dir, output_dir):
    """Generate summary statistics CSV."""

    output_file = Path(output_dir) / "validation_summary_statistics.csv"

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Sample', 'AMR_Genes_Detected', 'Prophages_Detected',
                        'Prophages_Expected', 'Prophage_Difference'])

        for sample in ETEC_SAMPLES:
            _, amr_count = parse_abricate_results(results_dir, sample)
            prophage_count = parse_vibrant_results(results_dir, sample)
            expected_prophages = TABLE_S4_PROPHAGE_COUNTS[sample]
            difference = abs(prophage_count - expected_prophages)

            writer.writerow([sample, amr_count, prophage_count,
                           expected_prophages, difference])

    print(f"✓ Summary statistics: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Simple ETEC validation comparison using ABRicate results")
    parser.add_argument("results_dir", help="Path to COMPASS results directory")
    parser.add_argument("--output", "-o", default="figures/etec_validation",
                       help="Output directory for figures")

    args = parser.parse_args()

    # Check results directory exists
    if not Path(args.results_dir).exists():
        print(f"ERROR: Results directory not found: {args.results_dir}")
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("ETEC Validation Comparison (ABRicate)")
    print("=" * 60)
    print(f"Results: {args.results_dir}")
    print(f"Output: {output_dir}")
    print("")

    # Generate comparisons
    print("Generating comparisons...")
    print("")

    # 1. Comparison table (CSV)
    generate_comparison_table(args.results_dir, output_dir)

    # 2. Gene counts bar chart
    plot_gene_counts_comparison(args.results_dir, output_dir)

    # 3. Prophage comparison
    plot_prophage_comparison(args.results_dir, output_dir)

    # 4. Simple heatmap (no dendrogram)
    plot_simple_heatmap(args.results_dir, output_dir)

    # 5. Summary statistics
    generate_summary_statistics(args.results_dir, output_dir)

    print("")
    print("=" * 60)
    print("✓ Validation comparison complete!")
    print("=" * 60)
    print(f"\nOutputs in: {output_dir}/")
    print("  - amr_gene_comparison.csv")
    print("  - amr_gene_counts.png")
    print("  - prophage_count_comparison.png")
    print("  - figure_s12_style_heatmap.png")
    print("  - validation_summary_statistics.csv")


if __name__ == "__main__":
    main()
