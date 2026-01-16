#!/usr/bin/env python3
"""
AMR Gene Classes Visualization

Creates visualizations showing the distribution of AMR resistance classes:
- Pie chart of overall resistance class distribution
- Bar chart of top resistance classes
- Stacked bar chart by year (if year data available)

Parses AMRFinder combined results to extract resistance classes.
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
    """Load AMRFinder combined data."""
    amr_path = base_dir / "amr_combined.tsv"

    if not amr_path.exists():
        print(f"❌ Error: {amr_path} not found")
        print("   Run create_combined_files.sh first!")
        sys.exit(1)

    print(f"📊 Loading AMR data from {amr_path}")
    df = pd.read_csv(amr_path, sep='\t')
    print(f"✅ Loaded {len(df)} AMR genes from {df['sample_id'].nunique()} samples")

    return df

def analyze_amr_classes(df):
    """Analyze AMR resistance classes."""
    print("\n💊 Analyzing AMR resistance classes...")

    # Get class distribution
    class_counts = Counter()

    for class_str in df['Class'].dropna():
        # AMRFinder can have multiple classes separated by '/'
        classes = str(class_str).split('/')
        for cls in classes:
            cls = cls.strip()
            if cls and cls != 'nan':
                class_counts[cls] += 1

    print(f"\n  📊 AMR Resistance Classes Found:")
    for cls, count in class_counts.most_common():
        pct = count / len(df) * 100
        print(f"    • {cls}: {count:,} ({pct:.1f}%)")

    return class_counts

def create_amr_class_pie_chart(class_counts, output_dir):
    """Create a pie chart of AMR resistance classes."""
    print("\n📊 Creating AMR class pie chart...")

    if not class_counts:
        print("  ❌ No AMR class data to visualize")
        return None

    # Prepare data - show top 10 classes, group rest as "Other"
    top_n = 10
    sorted_classes = class_counts.most_common()

    if len(sorted_classes) > top_n:
        top_classes = dict(sorted_classes[:top_n])
        other_count = sum(count for cls, count in sorted_classes[top_n:])
        top_classes['Other'] = other_count
    else:
        top_classes = dict(sorted_classes)

    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Pie chart
    colors = plt.cm.Set3(range(len(top_classes)))
    wedges, texts, autotexts = ax1.pie(
        top_classes.values(),
        labels=top_classes.keys(),
        autopct='%1.1f%%',
        colors=colors,
        startangle=90,
        textprops={'fontsize': 10, 'weight': 'bold'}
    )

    # Make percentage text more visible
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(9)
        autotext.set_weight('bold')

    ax1.set_title(
        f'AMR Resistance Class Distribution\n(Top {top_n} classes)',
        fontsize=14,
        fontweight='bold',
        pad=20
    )

    # Horizontal bar chart
    classes = list(top_classes.keys())
    counts = list(top_classes.values())

    # Sort by count
    sorted_pairs = sorted(zip(classes, counts), key=lambda x: x[1])
    classes_sorted = [x[0] for x in sorted_pairs]
    counts_sorted = [x[1] for x in sorted_pairs]

    bars = ax2.barh(range(len(classes_sorted)), counts_sorted, color=colors)
    ax2.set_yticks(range(len(classes_sorted)))
    ax2.set_yticklabels(classes_sorted, fontsize=10)
    ax2.set_xlabel('Number of Genes', fontsize=12, fontweight='bold')
    ax2.set_title(
        'AMR Genes by Resistance Class',
        fontsize=14,
        fontweight='bold',
        pad=20
    )
    ax2.grid(axis='x', alpha=0.3)

    # Add value labels on bars
    for i, (bar, count) in enumerate(zip(bars, counts_sorted)):
        ax2.text(bar.get_width() + max(counts_sorted)*0.01, bar.get_y() + bar.get_height()/2,
                f'{count:,}', va='center', fontsize=9)

    plt.tight_layout()

    # Save figure
    output_file = output_dir / "amr_resistance_classes.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✅ Chart saved to: {output_file}")
    return output_file

def analyze_amr_classes_by_year(df):
    """Analyze AMR classes by year if sample names contain year info."""
    print("\n📅 Analyzing AMR classes by year...")

    # Try to extract year from sample_id (Kansas NARMS format: YYKSnnXXnn)
    years = []
    for sample_id in df['sample_id']:
        try:
            # Extract first 2 digits and convert to 20YY format
            year_code = str(sample_id)[:2]
            if year_code.isdigit():
                year = 2000 + int(year_code)
                if 2020 <= year <= 2030:  # Reasonable range
                    years.append(year)
                else:
                    years.append(None)
            else:
                years.append(None)
        except:
            years.append(None)

    df['year'] = years

    # Check if we have year data
    if df['year'].isna().all():
        print("  ⚠️  Could not extract year information from sample IDs")
        return None

    years_found = df['year'].dropna().unique()
    print(f"  📊 Years found: {sorted(years_found)}")

    # Create year x class matrix
    year_class_data = {}
    for year in sorted(years_found):
        year_df = df[df['year'] == year]
        class_counts = Counter()

        for class_str in year_df['Class'].dropna():
            classes = str(class_str).split('/')
            for cls in classes:
                cls = cls.strip()
                if cls and cls != 'nan':
                    class_counts[cls] += 1

        year_class_data[year] = class_counts

    return year_class_data

def create_amr_class_temporal_chart(year_class_data, output_dir):
    """Create stacked bar chart showing AMR classes over time."""
    print("\n📊 Creating temporal AMR class chart...")

    if not year_class_data:
        print("  ⚠️  No year data available")
        return None

    # Get all unique classes across all years
    all_classes = set()
    for year_counts in year_class_data.values():
        all_classes.update(year_counts.keys())

    # Keep top 8 classes, group rest as "Other"
    total_counts = Counter()
    for year_counts in year_class_data.values():
        total_counts.update(year_counts)

    top_classes = [cls for cls, count in total_counts.most_common(8)]

    # Prepare data for stacked bar
    years = sorted(year_class_data.keys())
    data_matrix = {cls: [] for cls in top_classes}
    data_matrix['Other'] = []

    for year in years:
        year_counts = year_class_data[year]

        for cls in top_classes:
            data_matrix[cls].append(year_counts.get(cls, 0))

        # Sum "Other" classes
        other_count = sum(count for cls, count in year_counts.items() if cls not in top_classes)
        data_matrix['Other'].append(other_count)

    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(12, 8))

    # Create stacked bars
    bottom = [0] * len(years)
    colors = plt.cm.Set3(range(len(top_classes) + 1))

    for i, cls in enumerate(top_classes + ['Other']):
        ax.bar(years, data_matrix[cls], bottom=bottom, label=cls, color=colors[i])
        bottom = [b + v for b, v in zip(bottom, data_matrix[cls])]

    ax.set_xlabel('Year', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of AMR Genes', fontsize=12, fontweight='bold')
    ax.set_title(
        'AMR Resistance Classes Over Time\nKansas 2021-2025 NARMS Dataset',
        fontsize=14,
        fontweight='bold',
        pad=20
    )
    ax.legend(title='Resistance Class', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()

    # Save figure
    output_file = output_dir / "amr_classes_temporal.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✅ Temporal chart saved to: {output_file}")
    return output_file

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 visualize_amr_classes.py <base_directory>")
        print("  base_directory should contain amr_combined.tsv")
        sys.exit(1)

    base_dir = Path(sys.argv[1])

    if not base_dir.exists():
        print(f"❌ Error: Directory not found: {base_dir}")
        sys.exit(1)

    print("=" * 80)
    print("💊 AMR RESISTANCE CLASSES VISUALIZATION")
    print("=" * 80)
    print(f"Data directory: {base_dir}")
    print()

    # Load AMR data
    df = load_amr_data(base_dir)

    # Analyze resistance classes
    class_counts = analyze_amr_classes(df)

    if not class_counts:
        print("\n❌ No AMR class data found")
        sys.exit(1)

    # Create pie/bar chart
    pie_chart_file = create_amr_class_pie_chart(class_counts, base_dir)

    # Analyze and visualize by year
    year_class_data = analyze_amr_classes_by_year(df)
    temporal_file = None
    if year_class_data:
        temporal_file = create_amr_class_temporal_chart(year_class_data, base_dir)

    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"\nGenerated files:")
    print(f"  📊 {pie_chart_file}")
    if temporal_file:
        print(f"  📅 {temporal_file}")
    print()

if __name__ == "__main__":
    main()
