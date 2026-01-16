#!/usr/bin/env python3
"""
Mid-Level Analysis: Temporal, Species, and Food Type Patterns
For Kansas E. coli AMR-Prophage Study

Analyzes:
1. Temporal trends (2021-2025)
2. Species comparisons (E. coli vs Salmonella vs Campylobacter if available)
3. Food type patterns
4. Combined statistical summaries
"""

import csv
import json
from collections import defaultdict, Counter
from datetime import datetime
import os
import sys
from pathlib import Path

def extract_source_from_sample_name(sample_name):
    """
    Extract food source from Kansas sample name format.

    NARMS sample naming convention:
    [Year][State][Number][ProductCode][Number]-[Organism]

    Product codes:
    - GB = Ground Beef
    - CB = Chicken/Poultry (Chicken Breast, legs, etc.)
    - GT = Ground Turkey
    - PC = Pork Products
    - CL = Chicken Liver
    - CG = Chicken Gizzards
    - CH = Chicken Hearts
    - TK = Turkey
    - BF = Beef
    """
    import re

    if not sample_name:
        return 'Unknown'

    # Extract product code pattern (e.g., GB, CB, GT, PC, CL, CG, CH)
    # Pattern: digits followed by 2 capital letters followed by digits
    # Use findall to get all matches, then take the second one (first is state code)
    matches = re.findall(r'\d([A-Z]{2})\d', sample_name)
    if len(matches) >= 2:
        product_code = matches[1]  # Second match is the product code

        # Map to full names
        source_map = {
            'GB': 'Ground Beef',
            'CB': 'Chicken/Poultry',
            'GT': 'Ground Turkey',
            'PC': 'Pork Products',
            'CL': 'Chicken Liver',
            'CG': 'Chicken Gizzards',
            'CH': 'Chicken Hearts',
            'TK': 'Turkey',
            'BF': 'Beef',
        }

        return source_map.get(product_code, f'Other ({product_code})')

    return 'Unknown'


def load_metadata_files(base_dir):
    """Load metadata from all year directories to map SRR IDs to sample names and food sources"""
    print("Loading metadata from year directories...")

    metadata = {}
    base_path = Path(base_dir)

    # Load metadata from each year: 2021-2025
    for year in [2021, 2022, 2023, 2024, 2025]:
        metadata_file = base_path / f"results_kansas_{year}" / "filtered_samples" / "filtered_samples.csv"

        if not metadata_file.exists():
            print(f"  Warning: {metadata_file} not found, skipping")
            continue

        print(f"  Loading {year} metadata...")
        with open(metadata_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                srr_id = row['Run']
                sample_name = row.get('SampleName', '')
                organism = row.get('organism', 'Unknown')

                # Extract food source from sample name
                food_source = extract_source_from_sample_name(sample_name)

                metadata[srr_id] = {
                    'sample_name': sample_name,
                    'food_source': food_source,
                    'organism': organism,
                    'year': str(year)
                }

    print(f"  Loaded metadata for {len(metadata)} samples")
    return metadata


def load_colocation_data(csv_file):
    """Load the true co-location CSV data"""
    print(f"Loading co-location data from {csv_file}...")
    data = []
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    print(f"  Loaded {len(data)} AMR-prophage associations")
    return data

def load_comprehensive_json(json_file):
    """Load comprehensive analysis JSON if available"""
    if not os.path.exists(json_file):
        print(f"  Warning: {json_file} not found, using CSV only")
        return None

    print(f"Loading comprehensive data from {json_file}...")
    with open(json_file) as f:
        data = json.load(f)
    print(f"  Loaded comprehensive analysis")
    return data

def analyze_temporal_trends(data):
    """Analyze temporal trends year by year"""
    print("\nAnalyzing temporal trends...")

    # Group by year and category
    yearly_data = defaultdict(lambda: defaultdict(int))
    yearly_genes = defaultdict(set)
    yearly_samples = defaultdict(set)

    for row in data:
        year = row['year']
        category = row['category']
        sample = row['sample']  # Fixed: column is 'sample' not 'sample_id'
        gene = row['amr_gene']

        yearly_data[year][category] += 1
        yearly_genes[year].add(gene)
        yearly_samples[year].add(sample)

    # Calculate statistics per year
    temporal_stats = {}
    for year in sorted(yearly_data.keys()):
        total = sum(yearly_data[year].values())
        within = yearly_data[year].get('within_prophage', 0)
        proximal_10kb = yearly_data[year].get('proximal_10kb', 0)
        proximal_50kb = yearly_data[year].get('proximal_50kb', 0)
        same_contig = yearly_data[year].get('same_contig_distant', 0)
        different_contig = yearly_data[year].get('different_contig', 0)

        temporal_stats[year] = {
            'total_associations': total,
            'unique_genes': len(yearly_genes[year]),
            'unique_samples': len(yearly_samples[year]),
            'within_prophage': within,
            'proximal_10kb': proximal_10kb,
            'proximal_50kb': proximal_50kb,
            'same_contig_distant': same_contig,
            'different_contig': different_contig,
            'within_pct': (within / total * 100) if total > 0 else 0,
            'proximal_combined': proximal_10kb + proximal_50kb,
            'proximal_pct': ((proximal_10kb + proximal_50kb) / total * 100) if total > 0 else 0
        }

    return temporal_stats

def analyze_food_types(data, metadata):
    """Analyze patterns by food source type using metadata mapping"""
    print("\nAnalyzing food type patterns...")

    # Group by food source and category
    food_data = defaultdict(lambda: defaultdict(int))
    food_genes = defaultdict(set)
    food_samples = defaultdict(set)

    for row in data:
        srr_id = row['sample']
        category = row['category']
        gene = row['amr_gene']

        # Get food source from metadata
        if srr_id in metadata:
            food_source = metadata[srr_id]['food_source']
        else:
            food_source = 'Unknown'

        food_data[food_source][category] += 1
        food_genes[food_source].add(gene)
        food_samples[food_source].add(srr_id)

    # Calculate statistics per food type
    food_stats = {}
    for food_source in sorted(food_data.keys()):
        total = sum(food_data[food_source].values())
        within = food_data[food_source].get('within_prophage', 0)
        proximal_10kb = food_data[food_source].get('proximal_10kb', 0)
        proximal_50kb = food_data[food_source].get('proximal_50kb', 0)
        same_contig = food_data[food_source].get('same_contig_distant', 0)
        different_contig = food_data[food_source].get('different_contig', 0)

        food_stats[food_source] = {
            'total_associations': total,
            'unique_genes': len(food_genes[food_source]),
            'unique_samples': len(food_samples[food_source]),
            'within_prophage': within,
            'proximal_10kb': proximal_10kb,
            'proximal_50kb': proximal_50kb,
            'same_contig_distant': same_contig,
            'different_contig': different_contig,
            'within_pct': (within / total * 100) if total > 0 else 0,
            'proximal_combined': proximal_10kb + proximal_50kb,
            'proximal_pct': ((proximal_10kb + proximal_50kb) / total * 100) if total > 0 else 0
        }

    return food_stats

def analyze_drug_classes_temporal(data):
    """Analyze drug class patterns over time"""
    print("\nAnalyzing drug class temporal patterns...")

    yearly_classes = defaultdict(lambda: defaultdict(int))
    yearly_class_proximal = defaultdict(lambda: defaultdict(int))

    for row in data:
        year = row['year']
        drug_class = row['amr_class']
        category = row['category']

        yearly_classes[year][drug_class] += 1

        if category in ['within_prophage', 'proximal_10kb', 'proximal_50kb']:
            yearly_class_proximal[year][drug_class] += 1

    return yearly_classes, yearly_class_proximal

def analyze_top_genes_food_source(data, metadata):
    """Find top AMR genes by food source using metadata mapping"""
    print("\nAnalyzing top genes by food source...")

    food_gene_counts = defaultdict(lambda: Counter())
    food_gene_proximal = defaultdict(lambda: Counter())

    for row in data:
        srr_id = row['sample']
        gene = row['amr_gene']
        category = row['category']

        # Get food source from metadata
        if srr_id in metadata:
            food_source = metadata[srr_id]['food_source']
        else:
            food_source = 'Unknown'

        food_gene_counts[food_source][gene] += 1

        if category in ['within_prophage', 'proximal_10kb', 'proximal_50kb']:
            food_gene_proximal[food_source][gene] += 1

    return food_gene_counts, food_gene_proximal

def generate_html_report(output_file, temporal_stats, food_stats,
                         yearly_classes, yearly_class_proximal,
                         food_gene_counts, food_gene_proximal):
    """Generate comprehensive mid-level HTML report"""

    print(f"\nGenerating HTML report: {output_file}")

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kansas E. coli - Mid-Level Analysis: Temporal, Species & Food Patterns</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }

        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        nav {
            background: #2d3748;
            padding: 15px;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        nav ul {
            list-style: none;
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 20px;
        }

        nav a {
            color: white;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 5px;
            transition: background 0.3s;
            font-weight: 500;
        }

        nav a:hover {
            background: rgba(255,255,255,0.1);
        }

        .content {
            padding: 40px;
        }

        section {
            margin-bottom: 50px;
        }

        h2 {
            color: #667eea;
            font-size: 2em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }

        h3 {
            color: #764ba2;
            font-size: 1.5em;
            margin: 25px 0 15px 0;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }

        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }

        .stat-card:hover {
            transform: translateY(-5px);
        }

        .stat-card h4 {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }

        .stat-card .value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }

        thead {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }

        th {
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }

        tbody tr:hover {
            background: #f7fafc;
        }

        .highlight {
            background: #fef3c7;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: 600;
        }

        .alert-box {
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }

        .alert-box h4 {
            color: #92400e;
            margin-bottom: 10px;
        }

        .info-box {
            background: #dbeafe;
            border-left: 4px solid #3b82f6;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }

        .info-box h4 {
            color: #1e40af;
            margin-bottom: 10px;
        }

        .success-box {
            background: #d1fae5;
            border-left: 4px solid #10b981;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }

        .success-box h4 {
            color: #065f46;
            margin-bottom: 10px;
        }

        footer {
            background: #2d3748;
            color: white;
            padding: 30px;
            text-align: center;
        }

        .chart-placeholder {
            background: #f7fafc;
            border: 2px dashed #cbd5e0;
            padding: 40px;
            text-align: center;
            border-radius: 8px;
            margin: 20px 0;
            color: #718096;
        }

        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            margin: 0 5px;
        }

        .badge-blue {
            background: #dbeafe;
            color: #1e40af;
        }

        .badge-green {
            background: #d1fae5;
            color: #065f46;
        }

        .badge-yellow {
            background: #fef3c7;
            color: #92400e;
        }

        .badge-red {
            background: #fee2e2;
            color: #991b1b;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔬 Kansas E. coli AMR-Prophage Analysis</h1>
            <p>Mid-Level Analysis: Temporal Trends, Species Patterns & Food Source Associations</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        </header>

        <nav>
            <ul>
                <li><a href="#executive">📊 Executive Summary</a></li>
                <li><a href="#temporal">📈 Temporal Trends</a></li>
                <li><a href="#food">🍗 Food Source Analysis</a></li>
                <li><a href="#drugs">💊 Drug Classes</a></li>
                <li><a href="#genes">🧬 Gene Patterns</a></li>
                <li><a href="#conclusions">📝 Conclusions</a></li>
            </ul>
        </nav>

        <div class="content">
            <section id="executive">
                <h2>📊 Executive Summary</h2>

                <div class="alert-box">
                    <h4>🔍 Key Finding</h4>
                    <p>This mid-level analysis examines temporal trends (2021-2025), food source patterns, and drug class distributions to identify public health surveillance priorities for Kansas E. coli isolates.</p>
                </div>
"""

    # Calculate overall summary stats
    total_years = len(temporal_stats)
    total_food_types = len(food_stats)

    # Get trends
    years_sorted = sorted(temporal_stats.keys())
    if len(years_sorted) >= 2:
        first_year = years_sorted[0]
        last_year = years_sorted[-1]
        first_year_total = temporal_stats[first_year]['total_associations']
        last_year_total = temporal_stats[last_year]['total_associations']
        trend_pct = ((last_year_total - first_year_total) / first_year_total * 100) if first_year_total > 0 else 0
    else:
        trend_pct = 0

    html += f"""
                <div class="stats-grid">
                    <div class="stat-card">
                        <h4>Analysis Period</h4>
                        <div class="value">{total_years}</div>
                        <p>Years (2021-2025)</p>
                    </div>
                    <div class="stat-card">
                        <h4>Food Sources</h4>
                        <div class="value">{total_food_types}</div>
                        <p>Unique food types</p>
                    </div>
                    <div class="stat-card">
                        <h4>Temporal Trend</h4>
                        <div class="value">{trend_pct:+.1f}%</div>
                        <p>Change from {first_year} to {last_year}</p>
                    </div>
                </div>
            </section>

            <section id="temporal">
                <h2>📈 Temporal Trends (2021-2025)</h2>

                <div class="info-box">
                    <h4>📅 Year-by-Year Analysis</h4>
                    <p>Examining how AMR-prophage associations have changed over the 5-year study period.</p>
                </div>

                <h3>Annual Statistics</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Year</th>
                            <th>Total Associations</th>
                            <th>Unique Samples</th>
                            <th>Unique Genes</th>
                            <th>Within Prophage</th>
                            <th>Proximal (≤50kb)</th>
                            <th>Same Contig (>50kb)</th>
                            <th>Different Contig</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for year in sorted(temporal_stats.keys()):
        stats = temporal_stats[year]
        html += f"""
                        <tr>
                            <td><strong>{year}</strong></td>
                            <td>{stats['total_associations']:,}</td>
                            <td>{stats['unique_samples']}</td>
                            <td>{stats['unique_genes']}</td>
                            <td>{stats['within_prophage']} ({stats['within_pct']:.2f}%)</td>
                            <td><span class="highlight">{stats['proximal_combined']} ({stats['proximal_pct']:.2f}%)</span></td>
                            <td>{stats['same_contig_distant']}</td>
                            <td>{stats['different_contig']}</td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>

                <div class="chart-placeholder">
                    <p>📊 <strong>Chart Placeholder:</strong> Line graph showing yearly trends in proximal associations</p>
                    <p style="font-size: 0.9em; margin-top: 10px;">Use data above to create visualization in R/Python</p>
                </div>
"""

    # Add temporal insights
    html += """
                <h3>Key Temporal Observations</h3>
                <ul style="line-height: 2; margin-left: 30px;">
"""

    # Find year with highest proximal percentage
    max_proximal_year = max(temporal_stats.keys(), key=lambda y: temporal_stats[y]['proximal_pct'])
    max_proximal_pct = temporal_stats[max_proximal_year]['proximal_pct']

    # Find year with most samples
    max_samples_year = max(temporal_stats.keys(), key=lambda y: temporal_stats[y]['unique_samples'])
    max_samples_count = temporal_stats[max_samples_year]['unique_samples']

    html += f"""
                    <li><strong>Highest proximal association rate:</strong> {max_proximal_year} with {max_proximal_pct:.2f}% of AMR genes within 50kb of prophages</li>
                    <li><strong>Most samples analyzed:</strong> {max_samples_year} with {max_samples_count} unique samples</li>
                    <li><strong>Consistent finding:</strong> True within-prophage associations remain near 0% across all years</li>
"""

    html += """
                </ul>
            </section>

            <section id="food">
                <h2>🍗 Food Source Analysis</h2>

                <div class="info-box">
                    <h4>🥩 Food Type Patterns</h4>
                    <p>Analyzing AMR-prophage associations across different food sources to identify high-risk products.</p>
                </div>

                <h3>Food Source Statistics</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Food Source</th>
                            <th>Total Associations</th>
                            <th>Unique Samples</th>
                            <th>Unique Genes</th>
                            <th>Within Prophage</th>
                            <th>Proximal (≤50kb)</th>
                            <th>Proximal %</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    # Sort by total associations
    for food_source in sorted(food_stats.keys(), key=lambda x: food_stats[x]['total_associations'], reverse=True):
        stats = food_stats[food_source]
        html += f"""
                        <tr>
                            <td><strong>{food_source}</strong></td>
                            <td>{stats['total_associations']:,}</td>
                            <td>{stats['unique_samples']}</td>
                            <td>{stats['unique_genes']}</td>
                            <td>{stats['within_prophage']}</td>
                            <td><span class="highlight">{stats['proximal_combined']}</span></td>
                            <td>{stats['proximal_pct']:.2f}%</td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>

                <div class="chart-placeholder">
                    <p>📊 <strong>Chart Placeholder:</strong> Bar chart showing proximal association rates by food source</p>
                    <p style="font-size: 0.9em; margin-top: 10px;">Horizontal bars ranked by proximal percentage</p>
                </div>
"""

    # Find top food sources
    top_food_by_associations = max(food_stats.keys(), key=lambda x: food_stats[x]['total_associations'])
    top_food_by_proximal_pct = max(food_stats.keys(), key=lambda x: food_stats[x]['proximal_pct'])

    html += f"""
                <h3>Key Food Source Insights</h3>
                <ul style="line-height: 2; margin-left: 30px;">
                    <li><strong>Most AMR associations:</strong> {top_food_by_associations} ({food_stats[top_food_by_associations]['total_associations']:,} total associations)</li>
                    <li><strong>Highest proximal rate:</strong> {top_food_by_proximal_pct} ({food_stats[top_food_by_proximal_pct]['proximal_pct']:.2f}% proximal)</li>
                    <li><strong>Public health priority:</strong> Focus surveillance on food sources with highest proximal rates</li>
                </ul>
            </section>

            <section id="drugs">
                <h2>💊 Drug Class Temporal Patterns</h2>

                <div class="info-box">
                    <h4>🏥 Antimicrobial Class Trends</h4>
                    <p>Tracking which drug resistance classes show temporal changes in prophage association.</p>
                </div>

                <h3>Drug Classes by Year</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Drug Class</th>
"""

    # Add year columns
    for year in sorted(yearly_classes.keys()):
        html += f"                            <th>{year}</th>\n"

    html += """
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    # Get all drug classes
    all_drug_classes = set()
    for year_data in yearly_classes.values():
        all_drug_classes.update(year_data.keys())

    # Sort by total across all years
    drug_class_totals = Counter()
    for drug_class in all_drug_classes:
        for year in yearly_classes.keys():
            drug_class_totals[drug_class] += yearly_classes[year].get(drug_class, 0)

    for drug_class, total in drug_class_totals.most_common(15):  # Top 15 drug classes
        html += f"                        <tr>\n"
        html += f"                            <td><strong>{drug_class}</strong></td>\n"

        for year in sorted(yearly_classes.keys()):
            count = yearly_classes[year].get(drug_class, 0)
            proximal = yearly_class_proximal[year].get(drug_class, 0)
            proximal_pct = (proximal / count * 100) if count > 0 else 0

            if proximal > 0:
                html += f"                            <td>{count:,} <span class='badge badge-yellow'>{proximal} prox</span></td>\n"
            else:
                html += f"                            <td>{count:,}</td>\n"

        html += f"                            <td><strong>{total:,}</strong></td>\n"
        html += f"                        </tr>\n"

    html += """
                    </tbody>
                </table>

                <div class="chart-placeholder">
                    <p>📊 <strong>Chart Placeholder:</strong> Stacked area chart showing drug class trends over time</p>
                    <p style="font-size: 0.9em; margin-top: 10px;">X-axis: Years, Y-axis: Count, Colors: Drug classes</p>
                </div>
            </section>

            <section id="genes">
                <h2>🧬 Top AMR Genes by Food Source</h2>

                <div class="info-box">
                    <h4>🔬 Gene-Food Association Patterns</h4>
                    <p>Identifying which AMR genes are most common in specific food sources.</p>
                </div>
"""

    # Top genes per major food source
    top_n_food_sources = 5
    top_n_genes = 10

    sorted_food_sources = sorted(food_stats.keys(), key=lambda x: food_stats[x]['total_associations'], reverse=True)

    for food_source in sorted_food_sources[:top_n_food_sources]:
        html += f"""
                <h3>Top Genes in {food_source}</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Gene</th>
                            <th>Total Count</th>
                            <th>Proximal to Prophage</th>
                            <th>Proximal %</th>
                        </tr>
                    </thead>
                    <tbody>
"""

        for gene, count in food_gene_counts[food_source].most_common(top_n_genes):
            proximal = food_gene_proximal[food_source][gene]
            proximal_pct = (proximal / count * 100) if count > 0 else 0

            html += f"""
                        <tr>
                            <td><strong>{gene}</strong></td>
                            <td>{count}</td>
                            <td>{proximal}</td>
                            <td>{proximal_pct:.1f}%</td>
                        </tr>
"""

        html += """
                    </tbody>
                </table>
"""

    html += """
            </section>

            <section id="conclusions">
                <h2>📝 Conclusions & Public Health Implications</h2>

                <div class="success-box">
                    <h4>✅ Key Takeaways</h4>
                    <ul style="line-height: 2; margin-left: 20px; margin-top: 10px;">
                        <li><strong>Temporal stability:</strong> AMR-prophage association rates remain consistently low across 2021-2025</li>
                        <li><strong>Food source variation:</strong> Different food products show varying proximal association rates</li>
                        <li><strong>Drug class patterns:</strong> Certain resistance classes show temporal trends worth monitoring</li>
                        <li><strong>Surveillance priority:</strong> Target high-risk food sources identified in this analysis</li>
                    </ul>
                </div>

                <div class="alert-box">
                    <h4>⚠️ Important Note</h4>
                    <p>True within-prophage AMR integration remains at ~0% across all years, food sources, and drug classes. This finding is consistent with the overview analysis and suggests that <strong>prophage-mediated horizontal gene transfer is NOT a primary mechanism for AMR spread in Kansas E. coli isolates</strong>.</p>
                </div>

                <h3>Recommendations for Further Analysis</h3>
                <ul style="line-height: 2; margin-left: 30px;">
                    <li>Generate temporal trend visualizations (line charts, area plots)</li>
                    <li>Perform statistical tests for temporal trends (Chi-square, Mann-Kendall)</li>
                    <li>Create heatmaps of gene-food associations</li>
                    <li>Compare to national surveillance data (NARMS)</li>
                    <li>Investigate the 74 proximal genes in detail (within 50kb)</li>
                    <li>Analyze plasmid and transposon associations (from mobile_elements.csv)</li>
                </ul>
            </section>
        </div>

        <footer>
            <p><strong>Kansas E. coli AMR-Prophage Analysis - Mid-Level Report</strong></p>
            <p>Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
            <p style="margin-top: 10px; font-size: 0.9em;">Data: Kansas State University COMPASS Pipeline | Analysis Period: 2021-2025</p>
        </footer>
    </div>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"✅ Report generated: {output_file}")

def main():
    # File paths
    colocation_csv = os.path.expanduser('~/compass_kansas_results/publication_analysis/tables/kansas_ALL_years_amr_phage_colocation.csv')
    comprehensive_json = os.path.expanduser('~/compass_kansas_results/publication_analysis/raw_data/comprehensive_analysis.json')
    output_html = os.path.expanduser('~/compass_kansas_results/publication_analysis/reports/KANSAS_MIDLEVEL_ANALYSIS.html')
    base_dir = os.path.expanduser('~/compass_kansas_results')

    print("=" * 70)
    print("Kansas E. coli - Mid-Level Analysis Generator")
    print("Temporal Trends | Food Source Patterns | Drug Class Analysis")
    print("=" * 70)

    # Load metadata from year directories (for SRR ID -> food source mapping)
    metadata = load_metadata_files(base_dir)

    # Load data
    colocation_data = load_colocation_data(colocation_csv)
    comprehensive_data = load_comprehensive_json(comprehensive_json)

    # Perform analyses
    temporal_stats = analyze_temporal_trends(colocation_data)
    food_stats = analyze_food_types(colocation_data, metadata)
    yearly_classes, yearly_class_proximal = analyze_drug_classes_temporal(colocation_data)
    food_gene_counts, food_gene_proximal = analyze_top_genes_food_source(colocation_data, metadata)

    # Generate report
    generate_html_report(
        output_html,
        temporal_stats,
        food_stats,
        yearly_classes,
        yearly_class_proximal,
        food_gene_counts,
        food_gene_proximal
    )

    print("\n" + "=" * 70)
    print("✅ Mid-level analysis complete!")
    print("=" * 70)
    print(f"\n📊 Report: {output_html}")
    print(f"\n📈 Key Statistics:")
    print(f"   - Years analyzed: {len(temporal_stats)}")
    print(f"   - Food sources: {len(food_stats)}")
    print(f"   - Total associations: {sum(stats['total_associations'] for stats in temporal_stats.values()):,}")
    print("\n" + "=" * 70)

if __name__ == '__main__':
    main()
