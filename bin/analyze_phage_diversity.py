#!/usr/bin/env python3
"""
Prophage Diversity Analysis + PCoA

Analyzes:
1. Prophage diversity over time
2. Prophage diversity by geography (Kansas - if coord data available)
3. AMR + Phage diversity together
4. PCoA (Principal Coordinates Analysis) for phage diversity
5. Shannon/Simpson diversity indices

Outputs:
- Diversity metrics report (HTML)
- PCoA plot (PNG)
- Diversity over time plots
- Combined AMR-phage diversity analysis
"""

import csv
import os
import sys
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
from scipy.spatial.distance import pdist, squareform
from sklearn.manifold import MDS
import matplotlib.pyplot as plt
import seaborn as sns

def load_prophage_data(colocation_csv):
    """Load prophage presence/absence data"""
    print(f"Loading prophage data from {colocation_csv}...")

    # sample -> set of prophages
    sample_prophages = defaultdict(set)

    # prophage -> set of samples
    prophage_samples = defaultdict(set)

    with open(colocation_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample = row['sample']
            prophage_id = row.get('prophage_id', '')

            if prophage_id and prophage_id != 'None' and prophage_id != '':
                sample_prophages[sample].add(prophage_id)
                prophage_samples[prophage_id].add(sample)

    print(f"  {len(sample_prophages)} samples with prophages")
    print(f"  {len(prophage_samples)} unique prophages")

    return sample_prophages, prophage_samples


def load_amr_data(colocation_csv):
    """Load AMR gene data"""
    print("Loading AMR data...")

    # sample -> set of AMR genes
    sample_amr = defaultdict(set)

    with open(colocation_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample = row['sample']
            amr_gene = row['amr_gene']
            sample_amr[sample].add(amr_gene)

    print(f"  AMR data loaded for {len(sample_amr)} samples")
    return sample_amr


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


def calculate_diversity_metrics(sample_prophages, metadata):
    """
    Calculate diversity metrics by year

    Shannon diversity: H = -sum(p_i * log(p_i))
    Simpson diversity: D = 1 - sum(p_i^2)
    Richness: Number of unique prophages
    """
    print("\nCalculating diversity metrics...")

    yearly_diversity = {}

    # Group by year
    samples_by_year = defaultdict(list)
    for sample in sample_prophages:
        if sample in metadata:
            year = metadata[sample]['year']
            samples_by_year[year].append(sample)

    for year in sorted(samples_by_year.keys()):
        samples = samples_by_year[year]

        # Collect all prophages for this year
        all_prophages = []
        for sample in samples:
            all_prophages.extend(list(sample_prophages[sample]))

        if not all_prophages:
            continue

        # Calculate metrics
        prophage_counts = Counter(all_prophages)
        total = sum(prophage_counts.values())
        proportions = np.array([count/total for count in prophage_counts.values()])

        # Shannon diversity
        shannon = -np.sum(proportions * np.log(proportions))

        # Simpson diversity
        simpson = 1 - np.sum(proportions ** 2)

        # Richness (number of unique prophages)
        richness = len(prophage_counts)

        # Evenness
        evenness = shannon / np.log(richness) if richness > 1 else 0

        yearly_diversity[year] = {
            'shannon': shannon,
            'simpson': simpson,
            'richness': richness,
            'evenness': evenness,
            'total_prophages': total,
            'sample_count': len(samples)
        }

    return yearly_diversity


def calculate_amr_phage_diversity(sample_prophages, sample_amr, metadata):
    """Calculate combined AMR + Phage diversity"""
    print("\nCalculating combined AMR-Phage diversity...")

    yearly_combined = {}

    samples_by_year = defaultdict(list)
    for sample in sample_prophages:
        if sample in metadata:
            year = metadata[sample]['year']
            samples_by_year[year].append(sample)

    for year in sorted(samples_by_year.keys()):
        samples = samples_by_year[year]

        phage_richness = len(set(p for s in samples for p in sample_prophages.get(s, [])))
        amr_richness = len(set(a for s in samples for a in sample_amr.get(s, [])))

        # Samples with both
        both_count = sum(1 for s in samples if s in sample_prophages and s in sample_amr and sample_prophages[s] and sample_amr[s])

        yearly_combined[year] = {
            'phage_richness': phage_richness,
            'amr_richness': amr_richness,
            'both_count': both_count,
            'sample_count': len(samples)
        }

    return yearly_combined


def create_presence_absence_matrix(sample_prophages, prophage_samples):
    """
    Create presence/absence matrix for PCoA

    Rows: Samples
    Columns: Prophages
    Values: 1 if prophage present, 0 if absent
    """
    print("\nCreating presence/absence matrix for PCoA...")

    # Filter to prophages in at least 2 samples (reduce noise)
    common_prophages = [p for p, samples in prophage_samples.items() if len(samples) >= 2]

    samples = list(sample_prophages.keys())

    # Create matrix
    matrix = np.zeros((len(samples), len(common_prophages)))

    for i, sample in enumerate(samples):
        for j, prophage in enumerate(common_prophages):
            if prophage in sample_prophages[sample]:
                matrix[i, j] = 1

    print(f"  Matrix: {len(samples)} samples × {len(common_prophages)} prophages")

    return matrix, samples, common_prophages


def perform_pcoa(matrix, samples, metadata):
    """
    Perform Principal Coordinates Analysis (PCoA)
    Using MDS with Jaccard distance
    """
    print("\nPerforming PCoA...")

    # Calculate Jaccard distance
    # Jaccard = 1 - (intersection / union)
    distances = pdist(matrix, metric='jaccard')
    distance_matrix = squareform(distances)

    # Perform MDS (metric multidimensional scaling)
    mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
    coords = mds.fit_transform(distance_matrix)

    # Add metadata
    pcoa_data = []
    for i, sample in enumerate(samples):
        year = metadata.get(sample, {}).get('year', 'Unknown')
        organism = metadata.get(sample, {}).get('organism', 'Unknown')

        pcoa_data.append({
            'sample': sample,
            'pc1': coords[i, 0],
            'pc2': coords[i, 1],
            'year': year,
            'organism': organism
        })

    return pcoa_data


def plot_pcoa(pcoa_data, output_file):
    """Generate PCoA plot"""
    print(f"\nGenerating PCoA plot: {output_file}")

    fig, ax = plt.subplots(figsize=(12, 8))

    # Color by year
    years = sorted(set(d['year'] for d in pcoa_data if d['year'] != 'Unknown'))
    colors = plt.cm.viridis(np.linspace(0, 1, len(years)))
    year_colors = {year: colors[i] for i, year in enumerate(years)}

    for year in years:
        year_data = [d for d in pcoa_data if d['year'] == year]
        x = [d['pc1'] for d in year_data]
        y = [d['pc2'] for d in year_data]

        ax.scatter(x, y, c=[year_colors[year]], label=year, s=100, alpha=0.7, edgecolors='black')

    ax.set_xlabel('PC1', fontsize=14, fontweight='bold')
    ax.set_ylabel('PC2', fontsize=14, fontweight='bold')
    ax.set_title('PCoA of Prophage Diversity (Colored by Year)', fontsize=16, fontweight='bold')
    ax.legend(title='Year', fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_file}")
    plt.close()


def plot_diversity_over_time(yearly_diversity, output_file):
    """Plot diversity metrics over time"""
    print(f"\nGenerating diversity over time plot: {output_file}")

    years = sorted(yearly_diversity.keys())

    shannon = [yearly_diversity[y]['shannon'] for y in years]
    richness = [yearly_diversity[y]['richness'] for y in years]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Shannon diversity
    ax1.plot(years, shannon, marker='o', markersize=10, linewidth=3, color='#667eea')
    ax1.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Shannon Diversity Index', fontsize=14, fontweight='bold')
    ax1.set_title('Prophage Diversity Over Time', fontsize=16, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # Richness
    ax2.plot(years, richness, marker='s', markersize=10, linewidth=3, color='#764ba2')
    ax2.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Richness (Unique Prophages)', fontsize=14, fontweight='bold')
    ax2.set_title('Prophage Richness Over Time', fontsize=16, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_file}")
    plt.close()


def generate_html_report(yearly_diversity, yearly_combined, output_file):
    """Generate HTML report"""

    print(f"\nGenerating HTML report: {output_file}")

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Prophage Diversity Analysis</title>
    <style>
        body {{ font-family: sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 15px; padding: 40px; }}
        h2 {{ color: #667eea; border-bottom: 3px solid #667eea; padding-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        thead {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }}
        th, td {{ padding: 15px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        img {{ max-width: 100%; height: auto; margin: 20px 0; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <div class="container">
        <h1 style="text-align: center; color: #667eea;">🦠 Prophage Diversity Analysis</h1>

        <h2>📊 Diversity Metrics by Year</h2>
        <table>
            <thead>
                <tr>
                    <th>Year</th>
                    <th>Shannon</th>
                    <th>Simpson</th>
                    <th>Richness</th>
                    <th>Evenness</th>
                    <th>Samples</th>
                </tr>
            </thead>
            <tbody>
"""

    for year in sorted(yearly_diversity.keys()):
        d = yearly_diversity[year]
        html += f"""
                <tr>
                    <td><strong>{year}</strong></td>
                    <td>{d['shannon']:.3f}</td>
                    <td>{d['simpson']:.3f}</td>
                    <td>{d['richness']}</td>
                    <td>{d['evenness']:.3f}</td>
                    <td>{d['sample_count']}</td>
                </tr>
"""

    html += """
            </tbody>
        </table>

        <h2>📈 Diversity Over Time</h2>
        <img src="../figures/diversity_over_time.png" alt="Diversity Over Time">

        <h2>🔬 PCoA Analysis</h2>
        <img src="../figures/pcoa_phage_diversity.png" alt="PCoA">

        <h2>🧬 Combined AMR + Phage Diversity</h2>
        <table>
            <thead>
                <tr>
                    <th>Year</th>
                    <th>Phage Richness</th>
                    <th>AMR Richness</th>
                    <th>Samples with Both</th>
                </tr>
            </thead>
            <tbody>
"""

    for year in sorted(yearly_combined.keys()):
        c = yearly_combined[year]
        html += f"""
                <tr>
                    <td><strong>{year}</strong></td>
                    <td>{c['phage_richness']}</td>
                    <td>{c['amr_richness']}</td>
                    <td>{c['both_count']}</td>
                </tr>
"""

    html += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"  ✅ Saved: {output_file}")


def main():
    base_dir = os.path.expanduser('~/compass_kansas_results')
    colocation_csv = os.path.expanduser('~/compass_kansas_results/publication_analysis/tables/kansas_ALL_years_amr_phage_colocation.csv')
    figures_dir = os.path.expanduser('~/compass_kansas_results/publication_analysis/figures')
    reports_dir = os.path.expanduser('~/compass_kansas_results/publication_analysis/reports')

    Path(figures_dir).mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Prophage Diversity Analysis + PCoA")
    print("=" * 70)

    # Load data
    sample_prophages, prophage_samples = load_prophage_data(colocation_csv)
    sample_amr = load_amr_data(colocation_csv)
    metadata = load_metadata(base_dir)

    # Calculate diversity
    yearly_diversity = calculate_diversity_metrics(sample_prophages, metadata)
    yearly_combined = calculate_amr_phage_diversity(sample_prophages, sample_amr, metadata)

    # PCoA
    matrix, samples, common_prophages = create_presence_absence_matrix(sample_prophages, prophage_samples)
    pcoa_data = perform_pcoa(matrix, samples, metadata)

    # Generate plots
    plot_pcoa(pcoa_data, f"{figures_dir}/pcoa_phage_diversity.png")
    plot_diversity_over_time(yearly_diversity, f"{figures_dir}/diversity_over_time.png")

    # Generate report
    generate_html_report(yearly_diversity, yearly_combined, f"{reports_dir}/PHAGE_DIVERSITY_ANALYSIS.html")

    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
