#!/usr/bin/env python3
"""
AMR Genes on Plasmids Analysis

Analyzes which AMR genes are located on plasmid contigs by cross-referencing:
- AMRFinder results (contig locations of AMR genes)
- MOB-suite results (which contigs are plasmids)

Creates visualizations showing:
- % of AMR genes on plasmids vs chromosomal
- Which resistance classes are most commonly plasmid-borne
- Top AMR genes found on plasmids
- Pie chart of AMR-plasmid associations

This helps understand horizontal gene transfer of antibiotic resistance.
"""

import sys
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import Counter

def load_amr_data(base_dir):
    """Load AMRFinder combined data with contig information."""
    amr_path = base_dir / "amr_combined.tsv"

    if not amr_path.exists():
        print(f"❌ Error: {amr_path} not found")
        sys.exit(1)

    print(f"📊 Loading AMR data from {amr_path}")
    df = pd.read_csv(amr_path, sep='\t')
    print(f"✅ Loaded {len(df)} AMR genes from {df['sample_id'].nunique()} samples")

    return df

def identify_plasmid_contigs(base_dir):
    """Identify which contigs are plasmids from MOB-suite results."""
    print("\n🧬 Identifying plasmid contigs from MOB-suite...")

    mobsuite_dir = base_dir / "mobsuite"
    plasmid_contigs = {}  # sample_id -> set of plasmid contig names

    if not mobsuite_dir.exists():
        print(f"❌ Error: MOB-suite directory not found: {mobsuite_dir}")
        return plasmid_contigs

    for sample_dir in sorted(mobsuite_dir.glob("*_mobsuite")):
        sample_id = sample_dir.name.replace('_mobsuite', '')

        # MOB-suite creates plasmid FASTA files: plasmid_*.fasta
        sample_plasmid_contigs = set()

        for plasmid_fasta in sample_dir.glob("plasmid_*.fasta"):
            # Read FASTA headers to get contig names
            try:
                with open(plasmid_fasta) as f:
                    for line in f:
                        if line.startswith('>'):
                            # Extract contig name (everything after '>' until first space)
                            contig_name = line[1:].split()[0]
                            sample_plasmid_contigs.add(contig_name)
            except Exception as e:
                print(f"    ⚠️  Warning: Could not parse {plasmid_fasta.name}: {e}")

        if sample_plasmid_contigs:
            plasmid_contigs[sample_id] = sample_plasmid_contigs

    total_samples_with_plasmids = len(plasmid_contigs)
    total_plasmid_contigs = sum(len(contigs) for contigs in plasmid_contigs.values())

    print(f"  📊 Found {total_plasmid_contigs} plasmid contigs across {total_samples_with_plasmids} samples")

    return plasmid_contigs

def analyze_amr_plasmid_association(amr_df, plasmid_contigs):
    """Determine which AMR genes are on plasmid contigs."""
    print("\n🔬 Analyzing AMR-plasmid associations...")

    amr_on_plasmids = []
    amr_on_chromosome = []

    for _, row in amr_df.iterrows():
        sample_id = row['sample_id']
        contig = row['Contig id']
        gene = row['Gene symbol']
        gene_class = row['Class']

        # Check if this contig is a plasmid
        is_plasmid = False
        if sample_id in plasmid_contigs:
            if contig in plasmid_contigs[sample_id]:
                is_plasmid = True

        if is_plasmid:
            amr_on_plasmids.append({
                'sample_id': sample_id,
                'gene': gene,
                'class': gene_class,
                'contig': contig
            })
        else:
            amr_on_chromosome.append({
                'sample_id': sample_id,
                'gene': gene,
                'class': gene_class,
                'contig': contig
            })

    print(f"\n  📊 AMR Gene Locations:")
    print(f"    • AMR genes on plasmids: {len(amr_on_plasmids)}")
    print(f"    • AMR genes on chromosomes: {len(amr_on_chromosome)}")

    total_amr = len(amr_on_plasmids) + len(amr_on_chromosome)
    if total_amr > 0:
        plasmid_pct = len(amr_on_plasmids) / total_amr * 100
        print(f"    • Percentage on plasmids: {plasmid_pct:.1f}%")

    return amr_on_plasmids, amr_on_chromosome

def create_amr_plasmid_overview(amr_on_plasmids, amr_on_chromosome, output_dir):
    """Create overview visualizations of AMR-plasmid associations."""
    print("\n📊 Creating AMR-plasmid visualization...")

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('AMR Genes on Plasmids Analysis\nKansas 2021-2025 NARMS Dataset',
                 fontsize=16, fontweight='bold', y=0.98)

    # 1. Overall AMR location (pie chart)
    location_data = [len(amr_on_plasmids), len(amr_on_chromosome)]
    location_labels = ['Plasmid-borne', 'Chromosomal']
    colors_location = ['#FF6B6B', '#4ECDC4']

    wedges, texts, autotexts = ax1.pie(
        location_data,
        labels=location_labels,
        autopct='%1.1f%%',
        colors=colors_location,
        startangle=90,
        textprops={'fontsize': 11, 'weight': 'bold'}
    )

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)

    total = sum(location_data)
    ax1.set_title(
        f'AMR Gene Location (n={total})',
        fontsize=12,
        fontweight='bold',
        pad=10
    )

    # 2. Resistance classes on plasmids vs chromosomal
    if amr_on_plasmids:
        plasmid_classes = Counter(item['class'] for item in amr_on_plasmids if item['class'])
        chrom_classes = Counter(item['class'] for item in amr_on_chromosome if item['class'])

        # Get top 10 classes overall
        all_classes = plasmid_classes + chrom_classes
        top_classes = [cls for cls, count in all_classes.most_common(10)]

        # Prepare data for grouped bar chart
        plasmid_counts = [plasmid_classes.get(cls, 0) for cls in top_classes]
        chrom_counts = [chrom_classes.get(cls, 0) for cls in top_classes]

        x = range(len(top_classes))
        width = 0.35

        ax2.bar([i - width/2 for i in x], plasmid_counts, width, label='Plasmid', color='#FF6B6B')
        ax2.bar([i + width/2 for i in x], chrom_counts, width, label='Chromosomal', color='#4ECDC4')

        ax2.set_xlabel('Resistance Class', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Number of Genes', fontsize=11, fontweight='bold')
        ax2.set_title('Top Resistance Classes: Plasmid vs Chromosomal', fontsize=12, fontweight='bold', pad=10)
        ax2.set_xticks(x)
        ax2.set_xticklabels(top_classes, rotation=45, ha='right', fontsize=9)
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)
    else:
        ax2.text(0.5, 0.5, 'No plasmid-borne AMR genes found',
                ha='center', va='center', transform=ax2.transAxes)

    # 3. Top plasmid-borne AMR genes (horizontal bar)
    if amr_on_plasmids:
        plasmid_genes = Counter(item['gene'] for item in amr_on_plasmids if item['gene'])
        top_genes = plasmid_genes.most_common(15)

        if top_genes:
            genes = [x[0] for x in top_genes]
            counts = [x[1] for x in top_genes]

            # Sort by count
            sorted_pairs = sorted(zip(genes, counts), key=lambda x: x[1])
            genes_sorted = [x[0] for x in sorted_pairs]
            counts_sorted = [x[1] for x in sorted_pairs]

            bars = ax3.barh(range(len(genes_sorted)), counts_sorted, color='#9966FF')
            ax3.set_yticks(range(len(genes_sorted)))
            ax3.set_yticklabels(genes_sorted, fontsize=9)
            ax3.set_xlabel('Number of Occurrences', fontsize=11, fontweight='bold')
            ax3.set_title('Top 15 Plasmid-borne AMR Genes', fontsize=12, fontweight='bold', pad=10)
            ax3.grid(axis='x', alpha=0.3)

            # Add value labels
            for i, (bar, count) in enumerate(zip(bars, counts_sorted)):
                ax3.text(bar.get_width() + max(counts_sorted)*0.01, bar.get_y() + bar.get_height()/2,
                        f'{count}', va='center', fontsize=9)
        else:
            ax3.text(0.5, 0.5, 'No plasmid-borne AMR genes found',
                    ha='center', va='center', transform=ax3.transAxes)
    else:
        ax3.text(0.5, 0.5, 'No plasmid-borne AMR genes found',
                ha='center', va='center', transform=ax3.transAxes)

    # 4. Samples with plasmid-borne AMR
    if amr_on_plasmids:
        samples_with_plasmid_amr = len(set(item['sample_id'] for item in amr_on_plasmids))
        samples_with_any_amr = len(set(item['sample_id'] for item in amr_on_plasmids + amr_on_chromosome))
        samples_without_plasmid_amr = samples_with_any_amr - samples_with_plasmid_amr

        sample_data = [samples_with_plasmid_amr, samples_without_plasmid_amr]
        sample_labels = ['With plasmid-borne AMR', 'Without plasmid-borne AMR']
        colors_sample = ['#FFD93D', '#E8E8E8']

        wedges, texts, autotexts = ax4.pie(
            sample_data,
            labels=sample_labels,
            autopct='%1.1f%%',
            colors=colors_sample,
            startangle=90,
            textprops={'fontsize': 10, 'weight': 'bold'}
        )

        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(9)

        ax4.set_title(
            f'Samples with Plasmid-borne AMR (n={samples_with_any_amr})',
            fontsize=12,
            fontweight='bold',
            pad=10
        )
    else:
        ax4.text(0.5, 0.5, 'No plasmid-borne AMR genes found',
                ha='center', va='center', transform=ax4.transAxes)

    plt.tight_layout()

    # Save figure
    output_file = output_dir / "amr_on_plasmids.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✅ Visualization saved to: {output_file}")
    return output_file

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 visualize_amr_on_plasmids.py <base_directory>")
        print("  base_directory should contain amr_combined.tsv and mobsuite/")
        sys.exit(1)

    base_dir = Path(sys.argv[1])

    if not base_dir.exists():
        print(f"❌ Error: Directory not found: {base_dir}")
        sys.exit(1)

    print("=" * 80)
    print("🧬 AMR GENES ON PLASMIDS ANALYSIS")
    print("=" * 80)
    print(f"Data directory: {base_dir}")
    print()

    # Load AMR data
    amr_df = load_amr_data(base_dir)

    # Identify plasmid contigs
    plasmid_contigs = identify_plasmid_contigs(base_dir)

    if not plasmid_contigs:
        print("\n❌ No plasmid contigs found. Cannot perform analysis.")
        print("   Make sure MOB-suite has been run and results are in mobsuite/ directory")
        sys.exit(1)

    # Analyze AMR-plasmid associations
    amr_on_plasmids, amr_on_chromosome = analyze_amr_plasmid_association(amr_df, plasmid_contigs)

    # Create visualization
    overview_file = create_amr_plasmid_overview(amr_on_plasmids, amr_on_chromosome, base_dir)

    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"\nGenerated files:")
    print(f"  📊 {overview_file}")
    print()
    print("Key findings:")
    total = len(amr_on_plasmids) + len(amr_on_chromosome)
    if total > 0:
        pct = len(amr_on_plasmids) / total * 100
        print(f"  • {pct:.1f}% of AMR genes are on plasmids (horizontally transferable)")
        print(f"  • {100-pct:.1f}% are chromosomal (vertically inherited)")
    print()

if __name__ == "__main__":
    main()
