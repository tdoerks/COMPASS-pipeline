#!/usr/bin/env python3
"""
Generate Venn Diagrams for AMR-Prophage Shared Spaces

Visualizes overlaps between:
1. Samples with AMR genes only
2. Samples with Prophages only
3. Samples with both AMR + Prophages
4. Drug class overlaps
5. Temporal overlaps (by year)

Outputs:
- Venn diagrams (PNG)
- Overlap statistics (CSV)
- Interactive HTML report
"""

import csv
import os
from collections import defaultdict, Counter
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn3, venn2_circles, venn3_circles
import seaborn as sns

def load_colocation_data(colocation_csv):
    """Load AMR-prophage co-location data"""
    print(f"Loading data from {colocation_csv}...")

    samples_with_amr = set()
    samples_with_prophage = set()
    samples_with_both = set()

    # Drug class data
    drug_classes = set()
    sample_drug_classes = defaultdict(set)

    # Prophage data
    prophage_ids = set()
    sample_prophages = defaultdict(set)

    with open(colocation_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample = row['sample']
            amr_gene = row.get('amr_gene', '')
            drug_class = row.get('drug_class', '')
            prophage_id = row.get('prophage_id', '')

            if amr_gene and amr_gene != 'None':
                samples_with_amr.add(sample)
                if drug_class and drug_class != 'None':
                    drug_classes.add(drug_class)
                    sample_drug_classes[sample].add(drug_class)

            if prophage_id and prophage_id != 'None' and prophage_id != '':
                samples_with_prophage.add(sample)
                prophage_ids.add(prophage_id)
                sample_prophages[sample].add(prophage_id)

            if amr_gene and prophage_id and amr_gene != 'None' and prophage_id != '' and prophage_id != 'None':
                samples_with_both.add(sample)

    print(f"  Samples with AMR: {len(samples_with_amr)}")
    print(f"  Samples with Prophage: {len(samples_with_prophage)}")
    print(f"  Samples with both: {len(samples_with_both)}")
    print(f"  Drug classes: {len(drug_classes)}")
    print(f"  Prophages: {len(prophage_ids)}")

    return {
        'samples_with_amr': samples_with_amr,
        'samples_with_prophage': samples_with_prophage,
        'samples_with_both': samples_with_both,
        'drug_classes': drug_classes,
        'sample_drug_classes': sample_drug_classes,
        'sample_prophages': sample_prophages
    }


def load_metadata(base_dir):
    """Load sample metadata"""
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
                metadata[srr_id] = {
                    'year': year,
                    'organism': row.get('organism', 'Unknown')
                }

    print(f"  Loaded {len(metadata)} samples")
    return metadata


def plot_amr_prophage_venn(data, output_file):
    """Generate Venn diagram for AMR vs Prophage samples"""
    print(f"\nGenerating AMR-Prophage Venn diagram: {output_file}")

    amr_only = data['samples_with_amr'] - data['samples_with_prophage']
    prophage_only = data['samples_with_prophage'] - data['samples_with_amr']
    both = data['samples_with_both']

    fig, ax = plt.subplots(figsize=(10, 8))

    venn = venn2(
        subsets=(len(amr_only), len(prophage_only), len(both)),
        set_labels=('AMR Genes', 'Prophages'),
        ax=ax
    )

    # Styling
    venn.get_patch_by_id('10').set_color('#f59e0b')
    venn.get_patch_by_id('01').set_color('#3b82f6')
    venn.get_patch_by_id('11').set_color('#10b981')

    venn_circles = venn2_circles(
        subsets=(len(amr_only), len(prophage_only), len(both)),
        ax=ax,
        linewidth=2
    )

    ax.set_title('Sample Distribution: AMR Genes vs Prophages', fontsize=16, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_file}")
    plt.close()

    return {
        'amr_only': len(amr_only),
        'prophage_only': len(prophage_only),
        'both': len(both),
        'total': len(amr_only) + len(prophage_only) + len(both)
    }


def plot_temporal_venn(data, metadata, output_dir):
    """Generate Venn diagrams by year"""
    print(f"\nGenerating temporal Venn diagrams...")

    yearly_stats = {}

    for year in [2021, 2022, 2023, 2024, 2025]:
        # Get samples for this year
        year_samples = {s for s, m in metadata.items() if m['year'] == year}

        amr_year = data['samples_with_amr'] & year_samples
        prophage_year = data['samples_with_prophage'] & year_samples
        both_year = data['samples_with_both'] & year_samples

        if not amr_year and not prophage_year:
            continue

        amr_only = amr_year - prophage_year
        prophage_only = prophage_year - amr_year

        fig, ax = plt.subplots(figsize=(8, 6))

        venn = venn2(
            subsets=(len(amr_only), len(prophage_only), len(both_year)),
            set_labels=('AMR', 'Prophage'),
            ax=ax
        )

        if venn.get_patch_by_id('10'):
            venn.get_patch_by_id('10').set_color('#f59e0b')
        if venn.get_patch_by_id('01'):
            venn.get_patch_by_id('01').set_color('#3b82f6')
        if venn.get_patch_by_id('11'):
            venn.get_patch_by_id('11').set_color('#10b981')

        ax.set_title(f'AMR-Prophage Distribution: {year}', fontsize=14, fontweight='bold')

        output_file = f"{output_dir}/venn_{year}.png"
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"  ✅ Saved: {output_file}")
        plt.close()

        yearly_stats[year] = {
            'amr_only': len(amr_only),
            'prophage_only': len(prophage_only),
            'both': len(both_year),
            'total': len(year_samples)
        }

    return yearly_stats


def plot_drug_class_overlap(data, output_file, top_n=10):
    """Plot overlap of top drug classes"""
    print(f"\nGenerating drug class overlap plot: {output_file}")

    # Count samples per drug class
    drug_class_counts = Counter()
    for sample, classes in data['sample_drug_classes'].items():
        for dc in classes:
            drug_class_counts[dc] += 1

    # Get top N drug classes
    top_classes = [dc for dc, count in drug_class_counts.most_common(top_n)]

    if len(top_classes) < 2:
        print("  ⚠️  Not enough drug classes for overlap plot")
        return {}

    # Calculate pairwise overlaps
    overlap_matrix = []
    for dc1 in top_classes:
        row = []
        samples_dc1 = {s for s, classes in data['sample_drug_classes'].items() if dc1 in classes}

        for dc2 in top_classes:
            samples_dc2 = {s for s, classes in data['sample_drug_classes'].items() if dc2 in classes}
            overlap = len(samples_dc1 & samples_dc2)
            row.append(overlap)

        overlap_matrix.append(row)

    # Plot heatmap
    fig, ax = plt.subplots(figsize=(12, 10))

    sns.heatmap(
        overlap_matrix,
        xticklabels=top_classes,
        yticklabels=top_classes,
        annot=True,
        fmt='d',
        cmap='YlOrRd',
        ax=ax,
        cbar_kws={'label': 'Shared Samples'}
    )

    ax.set_title(f'Drug Class Co-occurrence (Top {top_n})', fontsize=16, fontweight='bold')
    ax.set_xlabel('Drug Class', fontsize=12, fontweight='bold')
    ax.set_ylabel('Drug Class', fontsize=12, fontweight='bold')

    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_file}")
    plt.close()

    return {'top_classes': top_classes, 'overlap_matrix': overlap_matrix}


def generate_html_report(overall_stats, yearly_stats, output_file):
    """Generate HTML report with all Venn diagrams"""
    print(f"\nGenerating HTML report: {output_file}")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AMR-Prophage Venn Diagram Analysis</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
            border-radius: 15px 15px 0 0;
        }}
        .content {{ padding: 40px; }}
        h2 {{
            color: #667eea;
            font-size: 2em;
            margin: 30px 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-card .value {{ font-size: 3em; font-weight: bold; margin: 10px 0; }}
        .venn-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin: 30px 0;
        }}
        .venn-card {{
            background: #f7fafc;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .venn-card img {{
            width: 100%;
            height: auto;
            border-radius: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        tbody tr:hover {{ background: #f7fafc; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧬 AMR-Prophage Venn Diagram Analysis</h1>
            <p>Shared Spaces in Kansas E. coli Samples</p>
        </header>

        <div class="content">
            <h2>📊 Overall Statistics</h2>

            <div class="stats-grid">
                <div class="stat-card">
                    <h4>AMR Only</h4>
                    <div class="value">{overall_stats['amr_only']}</div>
                    <p>samples</p>
                </div>
                <div class="stat-card">
                    <h4>Prophage Only</h4>
                    <div class="value">{overall_stats['prophage_only']}</div>
                    <p>samples</p>
                </div>
                <div class="stat-card">
                    <h4>Both AMR + Prophage</h4>
                    <div class="value">{overall_stats['both']}</div>
                    <p>samples</p>
                </div>
                <div class="stat-card">
                    <h4>Overlap %</h4>
                    <div class="value">{overall_stats['both']/overall_stats['total']*100:.1f}%</div>
                    <p>of total samples</p>
                </div>
            </div>

            <h2>🎯 Overall AMR-Prophage Distribution</h2>
            <div class="venn-container">
                <div class="venn-card">
                    <img src="../figures/venn_amr_prophage_overall.png" alt="Overall Venn">
                </div>
            </div>

            <h2>📅 Temporal Distribution (By Year)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Year</th>
                        <th>AMR Only</th>
                        <th>Prophage Only</th>
                        <th>Both</th>
                        <th>Total Samples</th>
                        <th>Overlap %</th>
                    </tr>
                </thead>
                <tbody>
"""

    for year in sorted(yearly_stats.keys()):
        stats = yearly_stats[year]
        overlap_pct = stats['both'] / stats['total'] * 100 if stats['total'] > 0 else 0
        html += f"""
                    <tr>
                        <td><strong>{year}</strong></td>
                        <td>{stats['amr_only']}</td>
                        <td>{stats['prophage_only']}</td>
                        <td>{stats['both']}</td>
                        <td>{stats['total']}</td>
                        <td>{overlap_pct:.1f}%</td>
                    </tr>
"""

    html += """
                </tbody>
            </table>

            <h2>📈 Yearly Venn Diagrams</h2>
            <div class="venn-container">
"""

    for year in sorted(yearly_stats.keys()):
        html += f"""
                <div class="venn-card">
                    <h3 style="text-align: center; color: #667eea;">{year}</h3>
                    <img src="../figures/venn_{year}.png" alt="{year} Venn">
                </div>
"""

    html += """
            </div>

            <h2>💊 Drug Class Co-occurrence</h2>
            <div class="venn-container">
                <div class="venn-card">
                    <img src="../figures/drug_class_overlap_heatmap.png" alt="Drug Class Overlap">
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"  ✅ Saved: {output_file}")


def save_overlap_csv(overall_stats, yearly_stats, output_file):
    """Save overlap statistics to CSV"""
    print(f"\nSaving overlap statistics: {output_file}")

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Year', 'AMR_Only', 'Prophage_Only', 'Both', 'Total', 'Overlap_Pct'])

        # Overall
        overlap_pct = overall_stats['both'] / overall_stats['total'] * 100
        writer.writerow(['ALL', overall_stats['amr_only'], overall_stats['prophage_only'],
                        overall_stats['both'], overall_stats['total'], f"{overlap_pct:.2f}"])

        # By year
        for year in sorted(yearly_stats.keys()):
            stats = yearly_stats[year]
            overlap_pct = stats['both'] / stats['total'] * 100 if stats['total'] > 0 else 0
            writer.writerow([year, stats['amr_only'], stats['prophage_only'],
                           stats['both'], stats['total'], f"{overlap_pct:.2f}"])

    print(f"  ✅ Saved: {output_file}")


def main():
    base_dir = os.path.expanduser('~/compass_kansas_results')
    colocation_csv = os.path.expanduser('~/compass_kansas_results/publication_analysis/tables/kansas_ALL_years_amr_phage_colocation.csv')
    figures_dir = os.path.expanduser('~/compass_kansas_results/publication_analysis/figures')
    reports_dir = os.path.expanduser('~/compass_kansas_results/publication_analysis/reports')
    tables_dir = os.path.expanduser('~/compass_kansas_results/publication_analysis/tables')

    Path(figures_dir).mkdir(parents=True, exist_ok=True)
    Path(reports_dir).mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("AMR-Prophage Venn Diagram Analysis")
    print("=" * 70)

    # Load data
    data = load_colocation_data(colocation_csv)
    metadata = load_metadata(base_dir)

    # Generate Venn diagrams
    overall_stats = plot_amr_prophage_venn(data, f"{figures_dir}/venn_amr_prophage_overall.png")
    yearly_stats = plot_temporal_venn(data, metadata, figures_dir)

    # Drug class overlap
    plot_drug_class_overlap(data, f"{figures_dir}/drug_class_overlap_heatmap.png")

    # Generate reports
    generate_html_report(overall_stats, yearly_stats, f"{reports_dir}/VENN_DIAGRAM_ANALYSIS.html")
    save_overlap_csv(overall_stats, yearly_stats, f"{tables_dir}/venn_overlap_statistics.csv")

    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
