#!/usr/bin/env python3
"""
Enhanced PCoA Analysis with Multiple Variables + PERMANOVA

Generates multiple PCoA plots colored by different factors:
1. Year (temporal)
2. Organism/Species
3. Food source
4. AMR presence/absence

Plus statistical testing (PERMANOVA) to determine which factor
explains the most variation in prophage composition.

PERMANOVA answers: "Which variable (year, food, species) is most
responsible for differences in prophage profiles?"
"""

import csv
import os
import re
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np
from scipy.spatial.distance import pdist, squareform
from sklearn.manifold import MDS
import matplotlib.pyplot as plt
import seaborn as sns

# Try to import scikit-bio for PERMANOVA
try:
    from skbio.stats.distance import DistanceMatrix
    from skbio.stats.distance import permanova
    HAS_SKBIO = True
except ImportError:
    print("⚠️  Warning: scikit-bio not available. PERMANOVA will be skipped.")
    print("   Install with: pip install --user scikit-bio")
    HAS_SKBIO = False


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


def load_amr_data(colocation_csv):
    """Load AMR presence/absence per sample"""
    print("Loading AMR data...")

    sample_amr = defaultdict(set)

    with open(colocation_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample = row['sample']
            amr_gene = row.get('amr_gene', '')
            if amr_gene and amr_gene != 'None':
                sample_amr[sample].add(amr_gene)

    print(f"  AMR data loaded for {len(sample_amr)} samples")
    return sample_amr


def extract_food_source(sample_name):
    """Extract food source from Kansas sample name"""
    if not sample_name or len(sample_name) < 8:
        return 'Unknown'

    try:
        # Format: YYKSXXTTNN-XX where TT = product code
        without_year = sample_name[2:]  # Remove YY
        without_state = without_year[2:]  # Remove KS
        without_num = without_state[2:]  # Remove XX
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
    """Load sample metadata with food source"""
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
                food_source = extract_food_source(sample_name)

                metadata[srr_id] = {
                    'year': year,
                    'organism': row.get('organism', 'Unknown'),
                    'sample_name': sample_name,
                    'food_source': food_source
                }

    print(f"  Loaded {len(metadata)} samples")
    return metadata


def create_presence_absence_matrix(sample_prophages, prophage_samples):
    """Create presence/absence matrix for PCoA"""
    print("\nCreating presence/absence matrix...")

    # Use all prophages (not just common ones) for better differentiation
    all_prophages = sorted(prophage_samples.keys())
    samples = sorted(sample_prophages.keys())

    matrix = np.zeros((len(samples), len(all_prophages)))

    for i, sample in enumerate(samples):
        for j, prophage in enumerate(all_prophages):
            if prophage in sample_prophages[sample]:
                matrix[i, j] = 1

    print(f"  Matrix: {len(samples)} samples × {len(all_prophages)} prophages")

    return matrix, samples, all_prophages


def perform_pcoa(matrix, samples, metadata):
    """Perform PCoA using MDS with Jaccard distance"""
    print("\nPerforming PCoA...")

    # Calculate Jaccard distance
    distances = pdist(matrix, metric='jaccard')
    distance_matrix = squareform(distances)

    # Perform MDS
    mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
    coords = mds.fit_transform(distance_matrix)

    # Compile data with metadata
    pcoa_data = []
    for i, sample in enumerate(samples):
        meta = metadata.get(sample, {})
        pcoa_data.append({
            'sample': sample,
            'pc1': coords[i, 0],
            'pc2': coords[i, 1],
            'year': meta.get('year', 'Unknown'),
            'organism': meta.get('organism', 'Unknown'),
            'food_source': meta.get('food_source', 'Unknown')
        })

    return pcoa_data, distance_matrix, samples


def perform_permanova(distance_matrix, samples, metadata, sample_amr):
    """
    Perform PERMANOVA to test which factors explain prophage variation

    Tests:
    - Year (temporal)
    - Organism (species)
    - Food source
    - AMR presence
    """
    if not HAS_SKBIO:
        print("\n⚠️  Skipping PERMANOVA (scikit-bio not installed)")
        return None

    print("\n" + "=" * 70)
    print("PERMANOVA Analysis - Testing Which Factors Explain Prophage Diversity")
    print("=" * 70)

    results = {}

    # Prepare grouping variables
    grouping_vars = {}

    for var_name in ['year', 'organism', 'food_source']:
        groups = []
        for sample in samples:
            meta = metadata.get(sample, {})
            value = meta.get(var_name, 'Unknown')
            groups.append(str(value))
        grouping_vars[var_name] = groups

    # AMR presence/absence
    amr_groups = []
    for sample in samples:
        amr_status = 'AMR_positive' if sample in sample_amr and sample_amr[sample] else 'AMR_negative'
        amr_groups.append(amr_status)
    grouping_vars['amr_status'] = amr_groups

    # Convert distance matrix to skbio format
    dm = DistanceMatrix(distance_matrix, ids=samples)

    # Run PERMANOVA for each variable
    for var_name, groups in grouping_vars.items():
        try:
            # Remove samples with Unknown values
            valid_indices = [i for i, g in enumerate(groups) if g != 'Unknown']
            if len(valid_indices) < len(samples) * 0.5:  # Skip if too many unknowns
                print(f"\n⚠️  Skipping {var_name}: too many unknown values")
                continue

            valid_samples = [samples[i] for i in valid_indices]
            valid_groups = [groups[i] for i in valid_indices]

            # Check if we have multiple groups
            unique_groups = set(valid_groups)
            if len(unique_groups) < 2:
                print(f"\n⚠️  Skipping {var_name}: only one group")
                continue

            # Subset distance matrix
            dm_subset = dm.filter(valid_samples)

            # Run PERMANOVA
            result = permanova(dm_subset, valid_groups, permutations=999)

            results[var_name] = {
                'test_statistic': result['test statistic'],
                'p_value': result['p-value'],
                'n_groups': len(unique_groups),
                'sample_size': result['sample size']
            }

            print(f"\n{var_name.upper()}:")
            print(f"  R² = {result['test statistic']:.4f}")
            print(f"  p-value = {result['p-value']:.4f}")
            print(f"  Groups: {len(unique_groups)}")
            print(f"  Samples: {result['sample size']}")

        except Exception as e:
            print(f"\n⚠️  Error in PERMANOVA for {var_name}: {e}")

    # Rank by R² (effect size)
    if results:
        print("\n" + "=" * 70)
        print("RANKING: Which factor explains the most variation?")
        print("=" * 70)

        ranked = sorted(results.items(), key=lambda x: x[1]['test_statistic'], reverse=True)

        for rank, (var_name, stats) in enumerate(ranked, 1):
            significance = "***" if stats['p_value'] < 0.001 else "**" if stats['p_value'] < 0.01 else "*" if stats['p_value'] < 0.05 else "ns"
            print(f"{rank}. {var_name:15s}  R²={stats['test_statistic']:.4f}  p={stats['p_value']:.4f} {significance}")

        print("\n*** p<0.001  ** p<0.01  * p<0.05  ns = not significant")
        print("=" * 70)

    return results


def plot_pcoa_by_year(pcoa_data, output_file):
    """PCoA colored by year"""
    print(f"\nGenerating PCoA (by year): {output_file}")

    fig, ax = plt.subplots(figsize=(12, 8))

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
    ax.set_title('PCoA: Prophage Diversity by Year', fontsize=16, fontweight='bold')
    ax.legend(title='Year', fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_file}")
    plt.close()


def plot_pcoa_by_organism(pcoa_data, output_file):
    """PCoA colored by organism/species"""
    print(f"\nGenerating PCoA (by organism): {output_file}")

    fig, ax = plt.subplots(figsize=(12, 8))

    organisms = sorted(set(d['organism'] for d in pcoa_data if d['organism'] != 'Unknown'))
    colors = plt.cm.Set3(np.linspace(0, 1, len(organisms)))
    organism_colors = {org: colors[i] for i, org in enumerate(organisms)}

    for organism in organisms:
        org_data = [d for d in pcoa_data if d['organism'] == organism]
        x = [d['pc1'] for d in org_data]
        y = [d['pc2'] for d in org_data]
        ax.scatter(x, y, c=[organism_colors[organism]], label=organism, s=100, alpha=0.7, edgecolors='black')

    ax.set_xlabel('PC1', fontsize=14, fontweight='bold')
    ax.set_ylabel('PC2', fontsize=14, fontweight='bold')
    ax.set_title('PCoA: Prophage Diversity by Organism', fontsize=16, fontweight='bold')
    ax.legend(title='Organism', fontsize=10, loc='best')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_file}")
    plt.close()


def plot_pcoa_by_food_source(pcoa_data, output_file):
    """PCoA colored by food source"""
    print(f"\nGenerating PCoA (by food source): {output_file}")

    fig, ax = plt.subplots(figsize=(12, 8))

    food_sources = sorted(set(d['food_source'] for d in pcoa_data if d['food_source'] != 'Unknown'))
    colors = plt.cm.tab10(np.linspace(0, 1, len(food_sources)))
    food_colors = {food: colors[i] for i, food in enumerate(food_sources)}

    for food in food_sources:
        food_data = [d for d in pcoa_data if d['food_source'] == food]
        x = [d['pc1'] for d in food_data]
        y = [d['pc2'] for d in food_data]
        ax.scatter(x, y, c=[food_colors[food]], label=food, s=100, alpha=0.7, edgecolors='black')

    ax.set_xlabel('PC1', fontsize=14, fontweight='bold')
    ax.set_ylabel('PC2', fontsize=14, fontweight='bold')
    ax.set_title('PCoA: Prophage Diversity by Food Source', fontsize=16, fontweight='bold')
    ax.legend(title='Food Source', fontsize=10, loc='best')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_file}")
    plt.close()


def plot_pcoa_by_amr(pcoa_data, sample_amr, output_file):
    """PCoA colored by AMR presence/absence"""
    print(f"\nGenerating PCoA (by AMR status): {output_file}")

    fig, ax = plt.subplots(figsize=(12, 8))

    # Classify samples
    amr_positive = [d for d in pcoa_data if d['sample'] in sample_amr and sample_amr[d['sample']]]
    amr_negative = [d for d in pcoa_data if d['sample'] not in sample_amr or not sample_amr[d['sample']]]

    # Plot
    if amr_positive:
        x = [d['pc1'] for d in amr_positive]
        y = [d['pc2'] for d in amr_positive]
        ax.scatter(x, y, c='#ef4444', label='AMR Positive', s=100, alpha=0.7, edgecolors='black')

    if amr_negative:
        x = [d['pc1'] for d in amr_negative]
        y = [d['pc2'] for d in amr_negative]
        ax.scatter(x, y, c='#3b82f6', label='AMR Negative', s=100, alpha=0.7, edgecolors='black')

    ax.set_xlabel('PC1', fontsize=14, fontweight='bold')
    ax.set_ylabel('PC2', fontsize=14, fontweight='bold')
    ax.set_title('PCoA: Prophage Diversity by AMR Status', fontsize=16, fontweight='bold')
    ax.legend(title='AMR Status', fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_file}")
    plt.close()


def plot_combined_pcoa(pcoa_data, sample_amr, output_file):
    """Create 2x2 grid of all PCoA plots"""
    print(f"\nGenerating combined PCoA plot: {output_file}")

    fig, axes = plt.subplots(2, 2, figsize=(16, 14))

    # Year
    ax = axes[0, 0]
    years = sorted(set(d['year'] for d in pcoa_data if d['year'] != 'Unknown'))
    colors = plt.cm.viridis(np.linspace(0, 1, len(years)))
    year_colors = {year: colors[i] for i, year in enumerate(years)}
    for year in years:
        year_data = [d for d in pcoa_data if d['year'] == year]
        x = [d['pc1'] for d in year_data]
        y = [d['pc2'] for d in year_data]
        ax.scatter(x, y, c=[year_colors[year]], label=year, s=60, alpha=0.7, edgecolors='black')
    ax.set_xlabel('PC1', fontsize=12, fontweight='bold')
    ax.set_ylabel('PC2', fontsize=12, fontweight='bold')
    ax.set_title('By Year', fontsize=14, fontweight='bold')
    ax.legend(title='Year', fontsize=9)
    ax.grid(True, alpha=0.3)

    # Organism
    ax = axes[0, 1]
    organisms = sorted(set(d['organism'] for d in pcoa_data if d['organism'] != 'Unknown'))[:8]  # Top 8
    colors = plt.cm.Set3(np.linspace(0, 1, len(organisms)))
    organism_colors = {org: colors[i] for i, org in enumerate(organisms)}
    for organism in organisms:
        org_data = [d for d in pcoa_data if d['organism'] == organism]
        x = [d['pc1'] for d in org_data]
        y = [d['pc2'] for d in org_data]
        ax.scatter(x, y, c=[organism_colors[organism]], label=organism[:30], s=60, alpha=0.7, edgecolors='black')
    ax.set_xlabel('PC1', fontsize=12, fontweight='bold')
    ax.set_ylabel('PC2', fontsize=12, fontweight='bold')
    ax.set_title('By Organism', fontsize=14, fontweight='bold')
    ax.legend(title='Organism', fontsize=8)
    ax.grid(True, alpha=0.3)

    # Food Source
    ax = axes[1, 0]
    food_sources = sorted(set(d['food_source'] for d in pcoa_data if d['food_source'] != 'Unknown'))
    colors = plt.cm.tab10(np.linspace(0, 1, len(food_sources)))
    food_colors = {food: colors[i] for i, food in enumerate(food_sources)}
    for food in food_sources:
        food_data = [d for d in pcoa_data if d['food_source'] == food]
        x = [d['pc1'] for d in food_data]
        y = [d['pc2'] for d in food_data]
        ax.scatter(x, y, c=[food_colors[food]], label=food, s=60, alpha=0.7, edgecolors='black')
    ax.set_xlabel('PC1', fontsize=12, fontweight='bold')
    ax.set_ylabel('PC2', fontsize=12, fontweight='bold')
    ax.set_title('By Food Source', fontsize=14, fontweight='bold')
    ax.legend(title='Food Source', fontsize=9)
    ax.grid(True, alpha=0.3)

    # AMR Status
    ax = axes[1, 1]
    amr_positive = [d for d in pcoa_data if d['sample'] in sample_amr and sample_amr[d['sample']]]
    amr_negative = [d for d in pcoa_data if d['sample'] not in sample_amr or not sample_amr[d['sample']]]
    if amr_positive:
        x = [d['pc1'] for d in amr_positive]
        y = [d['pc2'] for d in amr_positive]
        ax.scatter(x, y, c='#ef4444', label='AMR Positive', s=60, alpha=0.7, edgecolors='black')
    if amr_negative:
        x = [d['pc1'] for d in amr_negative]
        y = [d['pc2'] for d in amr_negative]
        ax.scatter(x, y, c='#3b82f6', label='AMR Negative', s=60, alpha=0.7, edgecolors='black')
    ax.set_xlabel('PC1', fontsize=12, fontweight='bold')
    ax.set_ylabel('PC2', fontsize=12, fontweight='bold')
    ax.set_title('By AMR Status', fontsize=14, fontweight='bold')
    ax.legend(title='AMR Status', fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.suptitle('PCoA: Prophage Diversity Analysis', fontsize=18, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"  ✅ Saved: {output_file}")
    plt.close()


def save_permanova_results(results, output_file):
    """Save PERMANOVA results to CSV"""
    if not results:
        return

    print(f"\nSaving PERMANOVA results: {output_file}")

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Variable', 'R_squared', 'P_value', 'N_groups', 'Sample_size', 'Significance'])

        ranked = sorted(results.items(), key=lambda x: x[1]['test_statistic'], reverse=True)

        for var_name, stats in ranked:
            if stats['p_value'] < 0.001:
                sig = '***'
            elif stats['p_value'] < 0.01:
                sig = '**'
            elif stats['p_value'] < 0.05:
                sig = '*'
            else:
                sig = 'ns'

            writer.writerow([
                var_name,
                f"{stats['test_statistic']:.4f}",
                f"{stats['p_value']:.4f}",
                stats['n_groups'],
                stats['sample_size'],
                sig
            ])

    print(f"  ✅ Saved: {output_file}")


def main():
    base_dir = os.path.expanduser('~/compass_kansas_results')
    colocation_csv = os.path.expanduser('~/compass_kansas_results/publication_analysis/tables/kansas_ALL_years_amr_phage_colocation.csv')
    figures_dir = os.path.expanduser('~/compass_kansas_results/publication_analysis/figures')
    tables_dir = os.path.expanduser('~/compass_kansas_results/publication_analysis/tables')

    Path(figures_dir).mkdir(parents=True, exist_ok=True)
    Path(tables_dir).mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Enhanced PCoA Analysis + PERMANOVA")
    print("=" * 70)

    # Load data
    sample_prophages, prophage_samples = load_prophage_data(colocation_csv)
    sample_amr = load_amr_data(colocation_csv)
    metadata = load_metadata(base_dir)

    # Create matrix and perform PCoA
    matrix, samples, prophages = create_presence_absence_matrix(sample_prophages, prophage_samples)
    pcoa_data, distance_matrix, samples = perform_pcoa(matrix, samples, metadata)

    # PERMANOVA - determine which factor explains variation
    permanova_results = perform_permanova(distance_matrix, samples, metadata, sample_amr)

    # Save PERMANOVA results
    if permanova_results:
        save_permanova_results(permanova_results, f"{tables_dir}/permanova_results.csv")

    # Generate PCoA plots
    plot_pcoa_by_year(pcoa_data, f"{figures_dir}/pcoa_by_year.png")
    plot_pcoa_by_organism(pcoa_data, f"{figures_dir}/pcoa_by_organism.png")
    plot_pcoa_by_food_source(pcoa_data, f"{figures_dir}/pcoa_by_food_source.png")
    plot_pcoa_by_amr(pcoa_data, sample_amr, f"{figures_dir}/pcoa_by_amr.png")
    plot_combined_pcoa(pcoa_data, sample_amr, f"{figures_dir}/pcoa_combined_4panel.png")

    print("\n" + "=" * 70)
    print("✅ Enhanced PCoA analysis complete!")
    print("=" * 70)
    print(f"\nOutput files:")
    print(f"  - pcoa_by_year.png")
    print(f"  - pcoa_by_organism.png")
    print(f"  - pcoa_by_food_source.png")
    print(f"  - pcoa_by_amr.png")
    print(f"  - pcoa_combined_4panel.png (ALL IN ONE)")
    if permanova_results:
        print(f"  - permanova_results.csv")
    print("=" * 70)


if __name__ == '__main__':
    main()
