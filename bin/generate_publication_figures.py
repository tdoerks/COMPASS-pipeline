#!/usr/bin/env python3
"""
Generate Publication-Quality Figures for Kansas E. coli AMR-Prophage Analysis

Creates:
1. Temporal trends line graph (2021-2025)
2. Food source comparison bar chart
3. Drug class temporal heatmap

Outputs: PNG files in ~/compass_kansas_results/publication_analysis/figures/
"""

import csv
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import numpy as np
from collections import defaultdict, Counter
from pathlib import Path
import os
import sys

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_metadata_files(base_dir):
    """Load metadata from all year directories"""
    print("Loading metadata...")
    metadata = {}
    base_path = Path(base_dir)

    for year in [2021, 2022, 2023, 2024, 2025]:
        metadata_file = base_path / f"results_kansas_{year}" / "filtered_samples" / "filtered_samples.csv"
        if not metadata_file.exists():
            continue

        with open(metadata_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                srr_id = row['Run']
                sample_name = row.get('SampleName', '')

                # Extract food source
                food_source = extract_source_from_sample_name(sample_name)

                metadata[srr_id] = {
                    'food_source': food_source,
                    'year': str(year)
                }

    print(f"  Loaded {len(metadata)} samples")
    return metadata


def extract_source_from_sample_name(sample_name):
    """Extract food source from Kansas sample name"""
    if not sample_name or len(sample_name) < 8:
        return 'Unknown'

    try:
        without_year = sample_name[2:]
        without_state = without_year[2:]
        without_num = without_state[2:]
        source_code = without_num[:2]

        source_map = {
            'GT': 'Ground Turkey',
            'CB': 'Chicken',
            'GB': 'Ground Beef',
            'PC': 'Pork',
            'CL': 'Chicken Liver',
            'CG': 'Chicken Gizzard',
            'CH': 'Chicken Heart',
        }

        return source_map.get(source_code.upper(), f'Other ({source_code})')
    except:
        return 'Unknown'


def load_colocation_data(csv_file):
    """Load co-location CSV"""
    print(f"Loading {csv_file}...")
    data = []
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    print(f"  Loaded {len(data)} associations")
    return data


def figure1_temporal_trends(data, output_file):
    """
    Figure 1: Temporal Trends (2021-2025)
    Line graph showing proximal association rates over time
    """
    print("\nGenerating Figure 1: Temporal Trends...")

    # Analyze by year
    yearly_stats = defaultdict(lambda: {'total': 0, 'proximal': 0})

    for row in data:
        year = row['year']
        if year:
            year = year.split('.')[0]  # Remove .0 if present
            category = row['category']

            yearly_stats[year]['total'] += 1
            if category in ['within_prophage', 'proximal_10kb', 'proximal_50kb']:
                yearly_stats[year]['proximal'] += 1

    # Calculate percentages
    years = sorted(yearly_stats.keys())
    proximal_pcts = []
    total_counts = []

    for year in years:
        total = yearly_stats[year]['total']
        proximal = yearly_stats[year]['proximal']
        pct = (proximal / total * 100) if total > 0 else 0
        proximal_pcts.append(pct)
        total_counts.append(total)

    # Create figure
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Line plot for percentage
    color = 'tab:blue'
    ax1.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Proximal Association Rate (%)', fontsize=14, fontweight='bold', color=color)
    line1 = ax1.plot(years, proximal_pcts, color=color, marker='o', markersize=10,
                     linewidth=3, label='Proximal Rate (%)')
    ax1.tick_params(axis='y', labelcolor=color, labelsize=12)
    ax1.tick_params(axis='x', labelsize=12)
    ax1.set_ylim(0, max(proximal_pcts) * 1.2)

    # Add data labels
    for i, (year, pct) in enumerate(zip(years, proximal_pcts)):
        ax1.text(i, pct + 0.05, f'{pct:.1f}%', ha='center', va='bottom',
                fontsize=10, fontweight='bold')

    # Second y-axis for sample counts
    ax2 = ax1.twinx()
    color = 'tab:orange'
    ax2.set_ylabel('Total Associations', fontsize=14, fontweight='bold', color=color)
    bars = ax2.bar(years, total_counts, alpha=0.3, color=color, label='Total Associations')
    ax2.tick_params(axis='y', labelcolor=color, labelsize=12)

    # Add value labels on bars
    for i, (year, count) in enumerate(zip(years, total_counts)):
        ax2.text(i, count + 20, f'{count:,}', ha='center', va='bottom',
                fontsize=9, color=color, fontweight='bold')

    # Title and legend
    plt.title('Kansas E. coli AMR-Prophage Temporal Trends (2021-2025)',
             fontsize=16, fontweight='bold', pad=20)

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + [bars], labels1 + labels2, loc='upper left', fontsize=11)

    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_file}")
    plt.close()


def figure2_food_source_comparison(data, metadata, output_file):
    """
    Figure 2: Food Source Comparison
    Bar chart showing proximal rates by food type
    """
    print("\nGenerating Figure 2: Food Source Comparison...")

    # Analyze by food source
    food_stats = defaultdict(lambda: {'total': 0, 'proximal': 0})

    for row in data:
        srr_id = row['sample']
        category = row['category']

        food_source = metadata.get(srr_id, {}).get('food_source', 'Unknown')

        food_stats[food_source]['total'] += 1
        if category in ['within_prophage', 'proximal_10kb', 'proximal_50kb']:
            food_stats[food_source]['proximal'] += 1

    # Calculate percentages and sort by total count
    food_data = []
    for food_source, stats in food_stats.items():
        total = stats['total']
        proximal = stats['proximal']
        pct = (proximal / total * 100) if total > 0 else 0
        food_data.append({
            'food': food_source,
            'pct': pct,
            'proximal': proximal,
            'total': total
        })

    # Sort by total count
    food_data.sort(key=lambda x: x['total'], reverse=True)

    # Take top 10 food sources
    top_foods = food_data[:10]

    # Create horizontal bar chart
    fig, ax = plt.subplots(figsize=(12, 8))

    foods = [f['food'] for f in top_foods]
    pcts = [f['pct'] for f in top_foods]
    totals = [f['total'] for f in top_foods]

    # Color bars by percentage
    colors = plt.cm.YlOrRd([p/max(pcts) if max(pcts) > 0 else 0 for p in pcts])

    bars = ax.barh(foods, pcts, color=colors, edgecolor='black', linewidth=1.5)

    # Add value labels
    for i, (bar, pct, total) in enumerate(zip(bars, pcts, totals)):
        width = bar.get_width()
        ax.text(width + 0.05, bar.get_y() + bar.get_height()/2,
               f'{pct:.2f}% (n={total:,})',
               ha='left', va='center', fontsize=10, fontweight='bold')

    ax.set_xlabel('Proximal Association Rate (%)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Food Source', fontsize=14, fontweight='bold')
    ax.set_title('AMR-Prophage Proximal Associations by Food Source\n(Top 10 by Sample Count)',
                fontsize=16, fontweight='bold', pad=20)

    ax.tick_params(labelsize=11)
    ax.set_xlim(0, max(pcts) * 1.15 if max(pcts) > 0 else 5)

    plt.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_file}")
    plt.close()


def figure3_drug_class_heatmap(data, output_file):
    """
    Figure 3: Drug Class Temporal Heatmap
    Shows drug class distribution over years
    """
    print("\nGenerating Figure 3: Drug Class Temporal Heatmap...")

    # Analyze drug classes by year
    yearly_classes = defaultdict(lambda: Counter())

    for row in data:
        year = row['year']
        if year:
            year = year.split('.')[0]
            drug_class = row['amr_class']
            category = row['category']

            # Only count proximal associations
            if category in ['within_prophage', 'proximal_10kb', 'proximal_50kb']:
                yearly_classes[year][drug_class] += 1

    # Get top drug classes overall
    all_classes = Counter()
    for year_data in yearly_classes.values():
        all_classes.update(year_data)

    top_classes = [dc for dc, _ in all_classes.most_common(15)]
    years = sorted(yearly_classes.keys())

    # Build matrix
    matrix = []
    for drug_class in top_classes:
        row = [yearly_classes[year][drug_class] for year in years]
        matrix.append(row)

    matrix = np.array(matrix)

    # Create heatmap
    fig, ax = plt.subplots(figsize=(12, 10))

    im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')

    # Set ticks
    ax.set_xticks(np.arange(len(years)))
    ax.set_yticks(np.arange(len(top_classes)))
    ax.set_xticklabels(years, fontsize=12)
    ax.set_yticklabels(top_classes, fontsize=11)

    # Rotate x labels
    plt.setp(ax.get_xticklabels(), rotation=0, ha="center")

    # Add values in cells
    for i in range(len(top_classes)):
        for j in range(len(years)):
            text = ax.text(j, i, matrix[i, j],
                          ha="center", va="center", color="black", fontsize=9, fontweight='bold')

    ax.set_title('Proximal AMR-Prophage Associations by Drug Class and Year\n(Top 15 Drug Classes)',
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax.set_ylabel('Drug Resistance Class', fontsize=14, fontweight='bold')

    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Count of Proximal Associations', rotation=270, labelpad=25,
                   fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_file}")
    plt.close()


def main():
    # Paths
    base_dir = os.path.expanduser('~/compass_kansas_results')
    colocation_csv = os.path.expanduser('~/compass_kansas_results/publication_analysis/tables/kansas_ALL_years_amr_phage_colocation.csv')
    figures_dir = os.path.expanduser('~/compass_kansas_results/publication_analysis/figures')

    # Create figures directory
    Path(figures_dir).mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Kansas E. coli - Publication Figure Generator")
    print("=" * 70)

    # Load data
    metadata = load_metadata_files(base_dir)
    colocation_data = load_colocation_data(colocation_csv)

    # Generate figures
    figure1_temporal_trends(
        colocation_data,
        f"{figures_dir}/figure1_temporal_trends.png"
    )

    figure2_food_source_comparison(
        colocation_data,
        metadata,
        f"{figures_dir}/figure2_food_source_comparison.png"
    )

    figure3_drug_class_heatmap(
        colocation_data,
        f"{figures_dir}/figure3_drug_class_heatmap.png"
    )

    print("\n" + "=" * 70)
    print("✅ All figures generated successfully!")
    print("=" * 70)
    print(f"\n📁 Output directory: {figures_dir}")
    print("\nGenerated files:")
    print("  1. figure1_temporal_trends.png")
    print("  2. figure2_food_source_comparison.png")
    print("  3. figure3_drug_class_heatmap.png")
    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
