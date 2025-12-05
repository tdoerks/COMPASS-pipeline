#!/usr/bin/env python3
"""
Generate pie charts and visualizations for prophage distribution analysis.
Shows prophage types, quality, and distribution across samples.
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import Counter

def load_vibrant_data(base_dir):
    """Load VIBRANT combined data."""
    vibrant_path = base_dir / "vibrant_combined.tsv"

    if not vibrant_path.exists():
        print(f"❌ Error: {vibrant_path} not found")
        print("   Run create_combined_files.sh first!")
        sys.exit(1)

    print(f"📊 Loading prophage data from {vibrant_path}")
    df = pd.read_csv(vibrant_path, sep='\t')
    print(f"✅ Loaded {len(df)} prophage predictions from {df['sample_id'].nunique()} samples")

    return df

def create_prophage_pie_charts(df, output_dir):
    """Create pie charts for prophage characteristics."""

    # Set style
    plt.style.use('seaborn-v0_8-darkgrid')
    colors_type = ['#FF6B6B', '#4ECDC4', '#95E1D3']
    colors_quality = ['#FFD93D', '#6BCB77', '#4D96FF', '#C3C3C3']

    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    fig.suptitle('Prophage Distribution Analysis - Kansas 2021-2025 NARMS',
                 fontsize=18, fontweight='bold', y=0.995)

    # 1. Prophage Type Distribution
    ax1 = axes[0, 0]
    type_counts = df['type'].value_counts()
    wedges1, texts1, autotexts1 = ax1.pie(type_counts.values,
                                            labels=type_counts.index,
                                            autopct='%1.1f%%',
                                            colors=colors_type[:len(type_counts)],
                                            startangle=90,
                                            textprops={'fontsize': 12, 'weight': 'bold'})
    ax1.set_title('Prophage Lifestyle Types\n(Lytic vs Lysogenic)',
                  fontsize=14, fontweight='bold', pad=20)

    # Add counts to legend
    legend_labels = [f'{idx}: {count:,} prophages' for idx, count in type_counts.items()]
    ax1.legend(legend_labels, loc='upper left', bbox_to_anchor=(1.0, 1.0))

    # 2. Prophage Quality Distribution
    ax2 = axes[0, 1]
    quality_counts = df['quality'].value_counts()
    wedges2, texts2, autotexts2 = ax2.pie(quality_counts.values,
                                            labels=quality_counts.index,
                                            autopct='%1.1f%%',
                                            colors=colors_quality[:len(quality_counts)],
                                            startangle=90,
                                            textprops={'fontsize': 12, 'weight': 'bold'})
    ax2.set_title('Prophage Quality Assessment\n(VIBRANT Predictions)',
                  fontsize=14, fontweight='bold', pad=20)

    legend_labels = [f'{idx}: {count:,} prophages' for idx, count in quality_counts.items()]
    ax2.legend(legend_labels, loc='upper left', bbox_to_anchor=(1.0, 1.0))

    # 3. Samples with Prophages
    ax3 = axes[1, 0]
    total_samples = df['sample_id'].nunique()
    samples_with_prophages = total_samples
    # Estimate total samples (you may want to adjust this)
    estimated_total = 825  # From your dataset
    samples_without = estimated_total - samples_with_prophages

    sample_data = [samples_with_prophages, samples_without]
    sample_labels = ['With Prophages', 'Without Prophages']
    colors_samples = ['#95E1D3', '#E8E8E8']

    wedges3, texts3, autotexts3 = ax3.pie(sample_data,
                                            labels=sample_labels,
                                            autopct='%1.1f%%',
                                            colors=colors_samples,
                                            startangle=90,
                                            textprops={'fontsize': 12, 'weight': 'bold'})
    ax3.set_title(f'Sample Coverage\n(n={estimated_total} total samples)',
                  fontsize=14, fontweight='bold', pad=20)

    legend_labels = [f'{label}: {count:,} samples' for label, count in zip(sample_labels, sample_data)]
    ax3.legend(legend_labels, loc='upper left', bbox_to_anchor=(1.0, 1.0))

    # 4. Prophages per Sample Distribution
    ax4 = axes[1, 1]
    prophages_per_sample = df.groupby('sample_id').size()

    # Create bins for prophage counts
    bins = [0, 1, 5, 10, 20, prophages_per_sample.max()+1]
    labels = ['1', '2-5', '6-10', '11-20', '20+']
    prophage_bins = pd.cut(prophages_per_sample, bins=bins, labels=labels, include_lowest=True)
    bin_counts = prophage_bins.value_counts().sort_index()

    colors_bins = ['#FF6B6B', '#FFA07A', '#FFD93D', '#6BCB77', '#4D96FF']

    wedges4, texts4, autotexts4 = ax4.pie(bin_counts.values,
                                            labels=bin_counts.index,
                                            autopct='%1.1f%%',
                                            colors=colors_bins[:len(bin_counts)],
                                            startangle=90,
                                            textprops={'fontsize': 12, 'weight': 'bold'})
    ax4.set_title(f'Prophages per Sample Distribution\n(Mean: {prophages_per_sample.mean():.1f})',
                  fontsize=14, fontweight='bold', pad=20)

    legend_labels = [f'{idx} prophages: {count:,} samples' for idx, count in bin_counts.items()]
    ax4.legend(legend_labels, loc='upper left', bbox_to_anchor=(1.0, 1.0))

    plt.tight_layout()

    # Save figure
    output_file = output_dir / "prophage_pie_charts.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✅ Pie charts saved to: {output_file}")

    return output_file

def create_organism_breakdown(df, output_dir):
    """Create pie chart showing prophage distribution by organism."""

    fig, ax = plt.subplots(figsize=(10, 8))

    # Extract organism from sample_id if available, or use a default
    # This assumes organism info might be in metadata
    # For now, we'll use the data as-is

    # Count unique samples per organism (if organism column exists)
    if 'organism' in df.columns:
        organism_counts = df.groupby('organism')['sample_id'].nunique()
    else:
        # Alternative: try to infer from sample names or show total
        print("⚠️  Organism information not found in VIBRANT data")
        return None

    colors = ['#FF6B6B', '#4ECDC4', '#95E1D3', '#FFD93D']

    wedges, texts, autotexts = ax.pie(organism_counts.values,
                                        labels=organism_counts.index,
                                        autopct='%1.1f%%',
                                        colors=colors[:len(organism_counts)],
                                        startangle=90,
                                        textprops={'fontsize': 12, 'weight': 'bold'})

    ax.set_title('Samples with Prophages by Organism\nKansas 2021-2025 NARMS',
                 fontsize=14, fontweight='bold', pad=20)

    legend_labels = [f'{org}: {count:,} samples' for org, count in organism_counts.items()]
    ax.legend(legend_labels, loc='upper left', bbox_to_anchor=(1.0, 1.0))

    plt.tight_layout()

    output_file = output_dir / "prophage_by_organism.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Organism breakdown saved to: {output_file}")

    return output_file

def print_summary_stats(df):
    """Print summary statistics."""

    print("\n" + "="*80)
    print("📊 PROPHAGE SUMMARY STATISTICS")
    print("="*80)

    total_prophages = len(df)
    total_samples = df['sample_id'].nunique()

    print(f"\n🦠 Overall:")
    print(f"  Total prophages detected: {total_prophages:,}")
    print(f"  Samples with prophages: {total_samples:,}")
    print(f"  Average prophages per sample: {total_prophages/total_samples:.2f}")

    print(f"\n🔬 By Type:")
    for ptype, count in df['type'].value_counts().items():
        pct = count/total_prophages*100
        print(f"  {ptype}: {count:,} ({pct:.1f}%)")

    print(f"\n💎 By Quality:")
    for quality, count in df['quality'].value_counts().items():
        pct = count/total_prophages*100
        print(f"  {quality}: {count:,} ({pct:.1f}%)")

    # Prophages per sample stats
    prophages_per_sample = df.groupby('sample_id').size()
    print(f"\n📈 Prophages per Sample:")
    print(f"  Min: {prophages_per_sample.min()}")
    print(f"  Max: {prophages_per_sample.max()}")
    print(f"  Median: {prophages_per_sample.median():.0f}")
    print(f"  Mean: {prophages_per_sample.mean():.2f}")

    print("\n" + "="*80)

def main():
    if len(sys.argv) < 2:
        print("Usage: visualize_prophages.py <base_directory>")
        print("  base_directory should contain vibrant_combined.tsv")
        sys.exit(1)

    base_dir = Path(sys.argv[1])

    if not base_dir.exists():
        print(f"❌ Error: Directory not found: {base_dir}")
        sys.exit(1)

    print("="*80)
    print("🦠 PROPHAGE VISUALIZATION ANALYSIS")
    print("="*80)
    print(f"Data directory: {base_dir}")
    print()

    # Load data
    df = load_vibrant_data(base_dir)

    # Print summary stats
    print_summary_stats(df)

    # Create visualizations
    print("\n📊 Generating visualizations...")
    output_dir = base_dir

    pie_chart_file = create_prophage_pie_charts(df, output_dir)
    organism_file = create_organism_breakdown(df, output_dir)

    print("\n" + "="*80)
    print("✅ VISUALIZATION COMPLETE!")
    print("="*80)
    print(f"\nGenerated files:")
    print(f"  📊 {pie_chart_file}")
    if organism_file:
        print(f"  📊 {organism_file}")
    print(f"\nTo view:")
    print(f"  Open the PNG files in an image viewer")
    print(f"  Or download to your computer:")
    print(f"    scp tylerdoe@icr-helios:{pie_chart_file} .")
    print()

if __name__ == "__main__":
    main()
