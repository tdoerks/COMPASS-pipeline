#!/usr/bin/env python3
"""
Plasmid Distribution Visualization

Creates visualizations showing plasmid distribution and characteristics:
- Pie chart of sample plasmid status (with/without plasmids)
- Bar chart of plasmids per sample distribution
- Pie chart of incompatibility (Inc) groups
- Bar chart of top Inc groups
- Temporal trends (if year data available)

Parses MOB-suite plasmid detection results.
"""

import sys
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import Counter

def parse_mobsuite_results(base_dir):
    """Parse MOB-suite plasmid detection results."""
    print("\n🧬 Parsing MOB-suite plasmid results...")

    mobsuite_dir = base_dir / "mobsuite"
    if not mobsuite_dir.exists():
        print(f"❌ Error: MOB-suite directory not found: {mobsuite_dir}")
        sys.exit(1)

    plasmid_data = []
    samples_with_plasmids = 0
    samples_without_plasmids = 0
    total_plasmids = 0

    # Process each MOB-suite result directory
    for sample_dir in sorted(mobsuite_dir.glob("*_mobsuite")):
        sample_id = sample_dir.name.replace('_mobsuite', '')

        # Look for MOB-typer results file
        mobtyper_file = sample_dir / "mobtyper_results.txt"

        if not mobtyper_file.exists():
            samples_without_plasmids += 1
            continue

        try:
            df = pd.read_csv(mobtyper_file, sep='\t')

            if df.empty:
                samples_without_plasmids += 1
                continue

            samples_with_plasmids += 1
            num_plasmids = len(df)
            total_plasmids += num_plasmids

            # Extract Inc groups and MOB types
            for _, row in df.iterrows():
                inc_types = str(row.get('rep_type(s)', '-')).split(',') if 'rep_type(s)' in row else ['-']
                mob_type = str(row.get('predicted_mobility', '-'))

                for inc in inc_types:
                    inc = inc.strip()
                    if inc and inc != '-' and inc != 'nan':
                        plasmid_data.append({
                            'sample_id': sample_id,
                            'inc_group': inc,
                            'mob_type': mob_type
                        })

        except Exception as e:
            print(f"    ⚠️  Warning: Could not parse {mobtyper_file.name}: {e}")
            samples_without_plasmids += 1
            continue

    print(f"\n  📊 Plasmid Statistics:")
    print(f"    • Samples with plasmids: {samples_with_plasmids}")
    print(f"    • Samples without plasmids: {samples_without_plasmids}")
    print(f"    • Total plasmids detected: {total_plasmids}")
    print(f"    • Average plasmids per sample: {total_plasmids / (samples_with_plasmids + samples_without_plasmids):.2f}")

    return {
        'plasmid_data': plasmid_data,
        'samples_with_plasmids': samples_with_plasmids,
        'samples_without_plasmids': samples_without_plasmids,
        'total_plasmids': total_plasmids
    }

def count_plasmids_per_sample(base_dir):
    """Count number of plasmids in each sample."""
    print("\n📊 Counting plasmids per sample...")

    mobsuite_dir = base_dir / "mobsuite"
    plasmid_counts = Counter()

    for sample_dir in sorted(mobsuite_dir.glob("*_mobsuite")):
        sample_id = sample_dir.name.replace('_mobsuite', '')
        mobtyper_file = sample_dir / "mobtyper_results.txt"

        if mobtyper_file.exists():
            try:
                df = pd.read_csv(mobtyper_file, sep='\t')
                plasmid_counts[len(df)] += 1
            except:
                plasmid_counts[0] += 1
        else:
            plasmid_counts[0] += 1

    return plasmid_counts

def create_plasmid_overview_chart(stats, output_dir):
    """Create overview charts for plasmid distribution."""
    print("\n📊 Creating plasmid overview charts...")

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Plasmid Distribution Overview\nKansas 2021-2025 NARMS Dataset',
                 fontsize=16, fontweight='bold', y=0.98)

    # 1. Sample plasmid status (pie chart)
    status_data = [stats['samples_with_plasmids'], stats['samples_without_plasmids']]
    status_labels = ['With Plasmids', 'Without Plasmids']
    colors_status = ['#4ECDC4', '#E8E8E8']

    wedges, texts, autotexts = ax1.pie(
        status_data,
        labels=status_labels,
        autopct='%1.1f%%',
        colors=colors_status,
        startangle=90,
        textprops={'fontsize': 11, 'weight': 'bold'}
    )

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(10)

    total = sum(status_data)
    ax1.set_title(
        f'Sample Plasmid Status (n={total})',
        fontsize=12,
        fontweight='bold',
        pad=10
    )

    # 2. Plasmids per sample distribution (bar chart)
    plasmid_counts = count_plasmids_per_sample(output_dir)

    # Create bins
    bins = {}
    for count, samples in plasmid_counts.items():
        if count == 0:
            bins['0'] = samples
        elif count == 1:
            bins['1'] = samples
        elif count <= 3:
            bins['2-3'] = bins.get('2-3', 0) + samples
        elif count <= 5:
            bins['4-5'] = bins.get('4-5', 0) + samples
        else:
            bins['6+'] = bins.get('6+', 0) + samples

    # Plot
    bin_labels = ['0', '1', '2-3', '4-5', '6+']
    bin_values = [bins.get(label, 0) for label in bin_labels]

    colors_bars = ['#FF6B6B', '#FFA07A', '#FFD93D', '#6BCB77', '#4D96FF']
    ax2.bar(range(len(bin_labels)), bin_values, color=colors_bars)
    ax2.set_xticks(range(len(bin_labels)))
    ax2.set_xticklabels(bin_labels, fontsize=11)
    ax2.set_xlabel('Number of Plasmids', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Number of Samples', fontsize=11, fontweight='bold')
    ax2.set_title('Plasmids per Sample Distribution', fontsize=12, fontweight='bold', pad=10)
    ax2.grid(axis='y', alpha=0.3)

    # 3. Inc group distribution (pie chart - top 10)
    if stats['plasmid_data']:
        inc_counts = Counter(p['inc_group'] for p in stats['plasmid_data'])

        # Top 10 Inc groups
        top_inc = dict(inc_counts.most_common(10))
        if len(inc_counts) > 10:
            other_count = sum(count for inc, count in inc_counts.items() if inc not in top_inc)
            top_inc['Other'] = other_count

        colors_inc = plt.cm.Set3(range(len(top_inc)))
        wedges, texts, autotexts = ax3.pie(
            top_inc.values(),
            labels=top_inc.keys(),
            autopct='%1.1f%%',
            colors=colors_inc,
            startangle=90,
            textprops={'fontsize': 9, 'weight': 'bold'}
        )

        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(8)

        ax3.set_title(
            f'Incompatibility (Inc) Groups (Top 10)\n{sum(top_inc.values())} plasmids',
            fontsize=12,
            fontweight='bold',
            pad=10
        )

        # 4. Top Inc groups (horizontal bar)
        sorted_inc = sorted(inc_counts.most_common(15), key=lambda x: x[1])
        inc_labels = [x[0] for x in sorted_inc]
        inc_values = [x[1] for x in sorted_inc]

        bars = ax4.barh(range(len(inc_labels)), inc_values, color='#4BC0C0')
        ax4.set_yticks(range(len(inc_labels)))
        ax4.set_yticklabels(inc_labels, fontsize=9)
        ax4.set_xlabel('Number of Plasmids', fontsize=11, fontweight='bold')
        ax4.set_title('Top 15 Incompatibility Groups', fontsize=12, fontweight='bold', pad=10)
        ax4.grid(axis='x', alpha=0.3)

        # Add value labels
        for i, (bar, val) in enumerate(zip(bars, inc_values)):
            ax4.text(bar.get_width() + max(inc_values)*0.01, bar.get_y() + bar.get_height()/2,
                    f'{val}', va='center', fontsize=9)
    else:
        ax3.text(0.5, 0.5, 'No Inc group data available',
                ha='center', va='center', transform=ax3.transAxes)
        ax4.text(0.5, 0.5, 'No Inc group data available',
                ha='center', va='center', transform=ax4.transAxes)

    plt.tight_layout()

    # Save figure
    output_file = output_dir / "plasmid_distribution.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✅ Overview chart saved to: {output_file}")
    return output_file

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 visualize_plasmids.py <base_directory>")
        print("  base_directory should contain mobsuite/ subdirectory")
        sys.exit(1)

    base_dir = Path(sys.argv[1])

    if not base_dir.exists():
        print(f"❌ Error: Directory not found: {base_dir}")
        sys.exit(1)

    print("=" * 80)
    print("🧬 PLASMID DISTRIBUTION VISUALIZATION")
    print("=" * 80)
    print(f"Data directory: {base_dir}")
    print()

    # Parse MOB-suite results
    stats = parse_mobsuite_results(base_dir)

    # Create overview chart
    overview_file = create_plasmid_overview_chart(stats, base_dir)

    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"\nGenerated files:")
    print(f"  📊 {overview_file}")
    print()

if __name__ == "__main__":
    main()
