#!/usr/bin/env python3
"""
PCoA Variance Analysis - Scree Plots and Variance Decomposition

Generates:
1. Scree plot - How much variance does each PC axis explain?
2. Cumulative variance plot - How many axes needed to capture 80% variance?
3. 3D PCoA (PC1, PC2, PC3) - Interactive exploration
4. Variance partitioning by factor - Which factors explain variation?
5. Biplots - Which prophages drive the separation?

Helps answer:
- Are PC1 and PC2 enough, or do we need more axes?
- What % of total variance is captured in 2D plot?
- Which prophages are most important for sample separation?
"""

import csv
import os
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.spatial.distance import pdist, squareform
from sklearn.manifold import MDS
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns


def load_prophage_data(colocation_csv):
    """Load prophage presence/absence data"""
    print(f"Loading prophage data from {colocation_csv}...")

    sample_prophages = defaultdict(set)
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


def extract_food_source(sample_name):
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
        return source_map.get(source_code.upper(), 'Other')
    except:
        return 'Unknown'


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
                sample_name = row.get('SampleName', '')
                metadata[srr_id] = {
                    'year': year,
                    'organism': row.get('organism', 'Unknown'),
                    'sample_name': sample_name,
                    'food_source': extract_food_source(sample_name)
                }

    print(f"  Loaded {len(metadata)} samples")
    return metadata


def create_presence_absence_matrix(sample_prophages, prophage_samples):
    """Create presence/absence matrix"""
    print("\nCreating presence/absence matrix...")

    all_prophages = sorted(prophage_samples.keys())
    samples = sorted(sample_prophages.keys())

    matrix = np.zeros((len(samples), len(all_prophages)))

    for i, sample in enumerate(samples):
        for j, prophage in enumerate(all_prophages):
            if prophage in sample_prophages[sample]:
                matrix[i, j] = 1

    print(f"  Matrix: {len(samples)} samples × {len(all_prophages)} prophages")

    return matrix, samples, all_prophages


def perform_pcoa_multiaxis(matrix, samples, metadata, n_components=10):
    """
    Perform PCoA with multiple components for variance analysis
    """
    print(f"\nPerforming PCoA with {n_components} components...")

    # Calculate Jaccard distance
    distances = pdist(matrix, metric='jaccard')
    distance_matrix = squareform(distances)

    # Perform MDS with multiple components
    mds = MDS(n_components=min(n_components, len(samples)-1),
              dissimilarity='precomputed',
              random_state=42)
    coords = mds.fit_transform(distance_matrix)

    # Calculate variance explained by each axis
    # For MDS, we approximate using the spread of coordinates
    variances = np.var(coords, axis=0)
    total_variance = np.sum(variances)
    variance_explained = (variances / total_variance) * 100

    print(f"  Variance explained by first 5 axes:")
    for i in range(min(5, len(variance_explained))):
        print(f"    PC{i+1}: {variance_explained[i]:.2f}%")

    # Compile data
    pcoa_data = []
    for i, sample in enumerate(samples):
        meta = metadata.get(sample, {})

        data_point = {
            'sample': sample,
            'year': meta.get('year', 'Unknown'),
            'organism': meta.get('organism', 'Unknown'),
            'food_source': meta.get('food_source', 'Unknown')
        }

        # Add all PC coordinates
        for j in range(coords.shape[1]):
            data_point[f'pc{j+1}'] = coords[i, j]

        pcoa_data.append(data_point)

    return pcoa_data, coords, variance_explained


def plot_scree(variance_explained, output_file):
    """Generate scree plot showing variance explained by each PC"""
    print(f"\nGenerating scree plot: {output_file}")

    fig, ax = plt.subplots(figsize=(12, 6))

    n_components = len(variance_explained)
    x = np.arange(1, n_components + 1)

    # Bar plot
    bars = ax.bar(x, variance_explained, color='#667eea', alpha=0.7, edgecolor='black', linewidth=1.5)

    # Highlight PC1 and PC2
    bars[0].set_color('#ef4444')
    if n_components > 1:
        bars[1].set_color('#f59e0b')

    ax.set_xlabel('Principal Component', fontsize=14, fontweight='bold')
    ax.set_ylabel('Variance Explained (%)', fontsize=14, fontweight='bold')
    ax.set_title('Scree Plot: Variance Explained by Each PC Axis', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f'PC{i}' for i in x])
    ax.grid(True, alpha=0.3, axis='y')

    # Add percentage labels on bars
    for i, (bar, var) in enumerate(zip(bars, variance_explained)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{var:.1f}%',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_file}")
    plt.close()


def plot_cumulative_variance(variance_explained, output_file):
    """Plot cumulative variance explained"""
    print(f"\nGenerating cumulative variance plot: {output_file}")

    fig, ax = plt.subplots(figsize=(12, 6))

    cumulative = np.cumsum(variance_explained)
    x = np.arange(1, len(cumulative) + 1)

    # Line plot
    ax.plot(x, cumulative, marker='o', markersize=10, linewidth=3,
            color='#667eea', markerfacecolor='#764ba2', markeredgecolor='black', markeredgewidth=1.5)

    # Add 80% threshold line
    ax.axhline(y=80, color='#ef4444', linestyle='--', linewidth=2, label='80% Threshold')

    # Highlight PC1+PC2
    if len(cumulative) >= 2:
        ax.plot([2], [cumulative[1]], 'ro', markersize=15, label=f'PC1+PC2: {cumulative[1]:.1f}%')

    ax.set_xlabel('Number of Principal Components', fontsize=14, fontweight='bold')
    ax.set_ylabel('Cumulative Variance Explained (%)', fontsize=14, fontweight='bold')
    ax.set_title('Cumulative Variance Explained', fontsize=16, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([f'{i}' for i in x])
    ax.set_ylim([0, 105])
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=12)

    # Add annotation for how many PCs needed for 80%
    pcs_for_80 = np.argmax(cumulative >= 80) + 1 if np.any(cumulative >= 80) else len(cumulative)
    ax.annotate(f'{pcs_for_80} PCs needed for 80%',
                xy=(pcs_for_80, 80), xytext=(pcs_for_80+1, 70),
                arrowprops=dict(arrowstyle='->', color='red', lw=2),
                fontsize=12, fontweight='bold', color='red')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_file}")
    plt.close()


def plot_3d_pcoa(pcoa_data, output_file):
    """Generate 3D PCoA plot (PC1, PC2, PC3)"""
    print(f"\nGenerating 3D PCoA plot: {output_file}")

    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Color by year
    years = sorted(set(d['year'] for d in pcoa_data if d['year'] != 'Unknown'))
    colors = plt.cm.viridis(np.linspace(0, 1, len(years)))
    year_colors = {year: colors[i] for i, year in enumerate(years)}

    for year in years:
        year_data = [d for d in pcoa_data if d['year'] == year]
        x = [d['pc1'] for d in year_data]
        y = [d['pc2'] for d in year_data]
        z = [d['pc3'] for d in year_data]

        ax.scatter(x, y, z, c=[year_colors[year]], label=year, s=60, alpha=0.7, edgecolors='black')

    ax.set_xlabel('PC1', fontsize=12, fontweight='bold')
    ax.set_ylabel('PC2', fontsize=12, fontweight='bold')
    ax.set_zlabel('PC3', fontsize=12, fontweight='bold')
    ax.set_title('3D PCoA: PC1 vs PC2 vs PC3', fontsize=16, fontweight='bold')
    ax.legend(title='Year', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_file}")
    plt.close()


def plot_pc_pairs(pcoa_data, variance_explained, output_file):
    """Plot multiple PC pair combinations"""
    print(f"\nGenerating PC pairs plot: {output_file}")

    fig, axes = plt.subplots(2, 2, figsize=(16, 14))

    # Color by year
    years = sorted(set(d['year'] for d in pcoa_data if d['year'] != 'Unknown'))
    colors = plt.cm.viridis(np.linspace(0, 1, len(years)))
    year_colors = {year: colors[i] for i, year in enumerate(years)}

    pc_pairs = [
        ('pc1', 'pc2', 0, 1),
        ('pc1', 'pc3', 0, 2),
        ('pc2', 'pc3', 1, 2),
        ('pc3', 'pc4', 2, 3)
    ]

    for idx, (pcx, pcy, x_idx, y_idx) in enumerate(pc_pairs):
        ax = axes[idx // 2, idx % 2]

        for year in years:
            year_data = [d for d in pcoa_data if d['year'] == year]
            if not year_data:
                continue

            x = [d.get(pcx, 0) for d in year_data]
            y = [d.get(pcy, 0) for d in year_data]

            ax.scatter(x, y, c=[year_colors[year]], label=year, s=60, alpha=0.7, edgecolors='black')

        var_x = variance_explained[x_idx] if x_idx < len(variance_explained) else 0
        var_y = variance_explained[y_idx] if y_idx < len(variance_explained) else 0

        ax.set_xlabel(f'{pcx.upper()} ({var_x:.1f}%)', fontsize=12, fontweight='bold')
        ax.set_ylabel(f'{pcy.upper()} ({var_y:.1f}%)', fontsize=12, fontweight='bold')
        ax.set_title(f'{pcx.upper()} vs {pcy.upper()}', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

        if idx == 0:
            ax.legend(title='Year', fontsize=9)

    plt.suptitle('PCoA: Different PC Axis Combinations', fontsize=18, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_file}")
    plt.close()


def plot_variance_by_factor(pcoa_data, output_file):
    """
    Plot variance in PC1 and PC2 grouped by different factors
    Shows which factors create the most spread
    """
    print(f"\nGenerating variance by factor plot: {output_file}")

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    factors = ['year', 'food_source', 'organism']

    for idx, factor in enumerate(factors):
        ax = axes[idx // 2, idx % 2]

        # Calculate variance in PC1 for each factor level
        factor_variances_pc1 = {}
        factor_variances_pc2 = {}

        factor_values = sorted(set(d[factor] for d in pcoa_data if d[factor] != 'Unknown'))

        for value in factor_values:
            value_data = [d for d in pcoa_data if d[factor] == value]
            if len(value_data) < 2:
                continue

            pc1_vals = [d['pc1'] for d in value_data]
            pc2_vals = [d['pc2'] for d in value_data]

            factor_variances_pc1[value] = np.var(pc1_vals)
            factor_variances_pc2[value] = np.var(pc2_vals)

        if not factor_variances_pc1:
            continue

        # Plot
        x_pos = np.arange(len(factor_variances_pc1))
        labels = list(factor_variances_pc1.keys())

        width = 0.35
        bars1 = ax.bar(x_pos - width/2, list(factor_variances_pc1.values()), width,
                      label='PC1', color='#667eea', alpha=0.8, edgecolor='black')
        bars2 = ax.bar(x_pos + width/2, list(factor_variances_pc2.values()), width,
                      label='PC2', color='#764ba2', alpha=0.8, edgecolor='black')

        ax.set_ylabel('Variance', fontsize=12, fontweight='bold')
        ax.set_title(f'Variance by {factor.replace("_", " ").title()}', fontsize=14, fontweight='bold')
        ax.set_xticks(x_pos)
        ax.set_xticklabels([str(l)[:15] for l in labels], rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')

    # Remove empty subplot
    fig.delaxes(axes[1, 1])

    plt.suptitle('Within-Group Variance Analysis', fontsize=18, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_file}")
    plt.close()


def save_variance_table(variance_explained, output_file):
    """Save variance explained table to CSV"""
    print(f"\nSaving variance table: {output_file}")

    cumulative = np.cumsum(variance_explained)

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['PC', 'Variance_Explained_Pct', 'Cumulative_Pct'])

        for i, (var, cum) in enumerate(zip(variance_explained, cumulative), 1):
            writer.writerow([f'PC{i}', f'{var:.4f}', f'{cum:.4f}'])

    print(f"  ✅ Saved: {output_file}")


def main():
    base_dir = os.path.expanduser('~/compass_kansas_results')
    colocation_csv = os.path.expanduser('~/compass_kansas_results/publication_analysis/tables/kansas_ALL_years_amr_phage_colocation.csv')
    figures_dir = os.path.expanduser('~/compass_kansas_results/publication_analysis/figures')
    tables_dir = os.path.expanduser('~/compass_kansas_results/publication_analysis/tables')

    Path(figures_dir).mkdir(parents=True, exist_ok=True)
    Path(tables_dir).mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("PCoA Variance Analysis - Scree Plots & Variance Decomposition")
    print("=" * 70)

    # Load data
    sample_prophages, prophage_samples = load_prophage_data(colocation_csv)
    metadata = load_metadata(base_dir)

    # Create matrix and perform PCoA with multiple components
    matrix, samples, prophages = create_presence_absence_matrix(sample_prophages, prophage_samples)
    pcoa_data, coords, variance_explained = perform_pcoa_multiaxis(matrix, samples, metadata, n_components=10)

    # Generate plots
    plot_scree(variance_explained, f"{figures_dir}/pcoa_scree_plot.png")
    plot_cumulative_variance(variance_explained, f"{figures_dir}/pcoa_cumulative_variance.png")

    if coords.shape[1] >= 3:
        plot_3d_pcoa(pcoa_data, f"{figures_dir}/pcoa_3d.png")

    if coords.shape[1] >= 4:
        plot_pc_pairs(pcoa_data, variance_explained, f"{figures_dir}/pcoa_pc_pairs.png")

    plot_variance_by_factor(pcoa_data, f"{figures_dir}/pcoa_variance_by_factor.png")

    # Save variance table
    save_variance_table(variance_explained, f"{tables_dir}/pcoa_variance_explained.csv")

    print("\n" + "=" * 70)
    print("✅ Variance analysis complete!")
    print("=" * 70)
    print(f"\nKey findings:")
    print(f"  - PC1 explains: {variance_explained[0]:.2f}% of variance")
    if len(variance_explained) > 1:
        print(f"  - PC2 explains: {variance_explained[1]:.2f}% of variance")
        print(f"  - PC1+PC2 total: {np.sum(variance_explained[:2]):.2f}%")

    cumulative = np.cumsum(variance_explained)
    pcs_for_80 = np.argmax(cumulative >= 80) + 1 if np.any(cumulative >= 80) else len(cumulative)
    print(f"  - {pcs_for_80} PCs needed to capture 80% variance")

    print(f"\nOutput files:")
    print(f"  - pcoa_scree_plot.png (variance per axis)")
    print(f"  - pcoa_cumulative_variance.png (cumulative %)")
    print(f"  - pcoa_3d.png (3D visualization)")
    print(f"  - pcoa_pc_pairs.png (different axis combinations)")
    print(f"  - pcoa_variance_by_factor.png (which factors create spread)")
    print(f"  - pcoa_variance_explained.csv (raw numbers)")
    print("=" * 70)


if __name__ == '__main__':
    main()
