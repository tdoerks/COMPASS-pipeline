#!/usr/bin/env python3
"""
AMR-Prophage Connection Analysis (Beyond Physical Distance)

Analyzes alternative relationships between AMR genes and prophages:
1. Sample-level co-occurrence (prophage burden vs AMR gene count)
2. Temporal co-trends (2021-2025)
3. Prophage family associations with AMR patterns
4. Correlation analysis

Generates: HTML report + statistical analysis
"""

import csv
import json
from collections import defaultdict, Counter
from pathlib import Path
import os
import sys
from scipy import stats
import numpy as np

def load_colocation_data(csv_file):
    """Load co-location CSV"""
    print(f"Loading co-location data from {csv_file}...")
    data = []
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    print(f"  Loaded {len(data)} AMR-prophage associations")
    return data


def analyze_sample_level_cooccurrence(data):
    """
    Analysis 1: Sample-level co-occurrence
    Do samples with more prophages also have more AMR genes?
    """
    print("\nAnalyzing sample-level co-occurrence...")

    sample_stats = defaultdict(lambda: {'amr_genes': set(), 'prophages': set()})

    for row in data:
        sample = row['sample']
        amr_gene = row['amr_gene']
        prophage_id = row.get('prophage_id', '')

        sample_stats[sample]['amr_genes'].add(amr_gene)
        if prophage_id and prophage_id != 'None' and prophage_id != '':
            sample_stats[sample]['prophages'].add(prophage_id)

    # Convert to counts
    sample_data = []
    for sample, stats in sample_stats.items():
        amr_count = len(stats['amr_genes'])
        prophage_count = len(stats['prophages'])
        sample_data.append({
            'sample': sample,
            'amr_count': amr_count,
            'prophage_count': prophage_count
        })

    # Calculate correlation
    amr_counts = [s['amr_count'] for s in sample_data]
    prophage_counts = [s['prophage_count'] for s in sample_data]

    if len(amr_counts) > 2 and len(set(prophage_counts)) > 1:
        correlation, p_value = stats.pearsonr(amr_counts, prophage_counts)
    else:
        correlation, p_value = 0, 1.0

    # Binning analysis
    bins = {
        'No prophages': {'samples': 0, 'avg_amr': 0, 'total_amr': 0},
        '1-2 prophages': {'samples': 0, 'avg_amr': 0, 'total_amr': 0},
        '3-5 prophages': {'samples': 0, 'avg_amr': 0, 'total_amr': 0},
        '6+ prophages': {'samples': 0, 'avg_amr': 0, 'total_amr': 0}
    }

    for s in sample_data:
        pc = s['prophage_count']
        ac = s['amr_count']

        if pc == 0:
            bin_name = 'No prophages'
        elif pc <= 2:
            bin_name = '1-2 prophages'
        elif pc <= 5:
            bin_name = '3-5 prophages'
        else:
            bin_name = '6+ prophages'

        bins[bin_name]['samples'] += 1
        bins[bin_name]['total_amr'] += ac

    # Calculate averages
    for bin_name, bin_data in bins.items():
        if bin_data['samples'] > 0:
            bin_data['avg_amr'] = bin_data['total_amr'] / bin_data['samples']

    return {
        'correlation': correlation,
        'p_value': p_value,
        'sample_data': sample_data,
        'bins': bins,
        'total_samples': len(sample_data)
    }


def analyze_temporal_cotrends(data):
    """
    Analysis 2: Temporal co-trends
    Do prophage and AMR prevalence track together over time?
    """
    print("\nAnalyzing temporal co-trends...")

    yearly_stats = defaultdict(lambda: {
        'samples': set(),
        'samples_with_prophages': set(),
        'samples_with_amr': set(),
        'total_amr_genes': 0,
        'total_prophages': 0
    })

    for row in data:
        year = row['year']
        if year:
            year = year.split('.')[0]
        sample = row['sample']
        prophage_id = row.get('prophage_id', '')

        yearly_stats[year]['samples'].add(sample)
        yearly_stats[year]['samples_with_amr'].add(sample)
        yearly_stats[year]['total_amr_genes'] += 1

        if prophage_id and prophage_id != 'None' and prophage_id != '':
            yearly_stats[year]['samples_with_prophages'].add(sample)
            yearly_stats[year]['total_prophages'] += 1

    # Calculate percentages
    yearly_summary = {}
    for year in sorted(yearly_stats.keys()):
        stats = yearly_stats[year]
        total_samples = len(stats['samples'])

        yearly_summary[year] = {
            'total_samples': total_samples,
            'samples_with_amr': len(stats['samples_with_amr']),
            'samples_with_prophages': len(stats['samples_with_prophages']),
            'pct_with_amr': len(stats['samples_with_amr']) / total_samples * 100 if total_samples > 0 else 0,
            'pct_with_prophages': len(stats['samples_with_prophages']) / total_samples * 100 if total_samples > 0 else 0,
            'avg_amr_per_sample': stats['total_amr_genes'] / total_samples if total_samples > 0 else 0,
            'avg_prophages_per_sample': stats['total_prophages'] / total_samples if total_samples > 0 else 0
        }

    # Correlation between trends
    years = sorted(yearly_summary.keys())
    if len(years) > 2:
        amr_trend = [yearly_summary[y]['pct_with_amr'] for y in years]
        prophage_trend = [yearly_summary[y]['pct_with_prophages'] for y in years]

        if len(set(prophage_trend)) > 1:
            trend_correlation, trend_p_value = stats.pearsonr(amr_trend, prophage_trend)
        else:
            trend_correlation, trend_p_value = 0, 1.0
    else:
        trend_correlation, trend_p_value = 0, 1.0

    return {
        'yearly_summary': yearly_summary,
        'trend_correlation': trend_correlation,
        'trend_p_value': trend_p_value
    }


def analyze_prophage_family_associations(data):
    """
    Analysis 3: Prophage family/type associations with AMR patterns
    Do certain prophage types associate with specific AMR patterns?
    """
    print("\nAnalyzing prophage family associations...")

    # Group by prophage (using contig as proxy for prophage type)
    prophage_amr = defaultdict(lambda: Counter())
    prophage_samples = defaultdict(set)

    for row in data:
        prophage_id = row.get('prophage_id', '')
        if prophage_id and prophage_id != 'None' and prophage_id != '':
            amr_gene = row['amr_gene']
            amr_class = row['amr_class']
            sample = row['sample']

            prophage_amr[prophage_id][amr_gene] += 1
            prophage_samples[prophage_id].add(sample)

    # Get top prophages by sample count
    prophage_stats = []
    for prophage_id, samples in prophage_samples.items():
        sample_count = len(samples)
        total_amr = sum(prophage_amr[prophage_id].values())
        unique_amr = len(prophage_amr[prophage_id])
        top_genes = prophage_amr[prophage_id].most_common(5)

        prophage_stats.append({
            'prophage_id': prophage_id,
            'sample_count': sample_count,
            'total_amr_associations': total_amr,
            'unique_amr_genes': unique_amr,
            'top_genes': top_genes
        })

    # Sort by sample count
    prophage_stats.sort(key=lambda x: x['sample_count'], reverse=True)

    return {
        'prophage_stats': prophage_stats[:20],  # Top 20 prophages
        'total_unique_prophages': len(prophage_samples)
    }


def analyze_amr_class_prophage_patterns(data):
    """
    Analysis 4: AMR class patterns with prophage presence
    Do certain drug resistance classes appear more with prophages?
    """
    print("\nAnalyzing AMR class patterns...")

    class_stats = defaultdict(lambda: {
        'with_prophage': 0,
        'without_prophage': 0,
        'proximal': 0
    })

    for row in data:
        amr_class = row['amr_class']
        category = row['category']
        prophage_id = row.get('prophage_id', '')

        has_prophage = prophage_id and prophage_id != 'None' and prophage_id != ''

        if category in ['within_prophage', 'proximal_10kb', 'proximal_50kb']:
            class_stats[amr_class]['proximal'] += 1

        if has_prophage:
            class_stats[amr_class]['with_prophage'] += 1
        else:
            class_stats[amr_class]['without_prophage'] += 1

    # Calculate ratios
    class_summary = []
    for amr_class, stats in class_stats.items():
        total = stats['with_prophage'] + stats['without_prophage']
        pct_with_prophage = (stats['with_prophage'] / total * 100) if total > 0 else 0
        pct_proximal = (stats['proximal'] / total * 100) if total > 0 else 0

        class_summary.append({
            'class': amr_class,
            'total': total,
            'with_prophage': stats['with_prophage'],
            'without_prophage': stats['without_prophage'],
            'proximal': stats['proximal'],
            'pct_with_prophage': pct_with_prophage,
            'pct_proximal': pct_proximal
        })

    # Sort by total
    class_summary.sort(key=lambda x: x['total'], reverse=True)

    return class_summary


def generate_html_report(output_file, cooccurrence, temporal, prophage_assoc, class_patterns):
    """Generate comprehensive HTML report"""

    print(f"\nGenerating HTML report: {output_file}")

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kansas E. coli - AMR-Prophage Connection Analysis</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

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

        .content { padding: 40px; }

        section { margin-bottom: 50px; }

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
        }

        tbody tr:hover { background: #f7fafc; }

        .stat-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            margin: 20px 0;
        }

        .stat-box h3 { color: white; }

        .alert-box {
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }

        .info-box {
            background: #dbeafe;
            border-left: 4px solid #3b82f6;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }

        .success-box {
            background: #d1fae5;
            border-left: 4px solid #10b981;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }

        .highlight {
            background: #fef3c7;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: 600;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }

        .stat-card {
            background: white;
            border: 2px solid #e2e8f0;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }

        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }

        .stat-card .label {
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔬 AMR-Prophage Connection Analysis</h1>
            <p>Alternative Relationships Beyond Physical Distance</p>
            <p style="font-size: 0.9em; margin-top: 10px;">Kansas E. coli Isolates (2021-2025)</p>
        </header>

        <div class="content">
"""

    # Analysis 1: Sample-level co-occurrence
    html += """
            <section id="cooccurrence">
                <h2>📊 Analysis 1: Sample-Level Co-occurrence</h2>

                <div class="info-box">
                    <h4>🔍 Question: Do samples with more prophages also have more AMR genes?</h4>
                    <p>This tests whether prophage burden and AMR burden are correlated at the sample level.</p>
                </div>
"""

    corr = cooccurrence['correlation']
    p_val = cooccurrence['p_value']

    if p_val < 0.05:
        significance = "statistically significant"
        box_class = "alert-box"
    else:
        significance = "NOT statistically significant"
        box_class = "success-box"

    html += f"""
                <div class="{box_class}">
                    <h3>Statistical Result</h3>
                    <p><strong>Pearson Correlation:</strong> r = {corr:.3f}</p>
                    <p><strong>P-value:</strong> {p_val:.4f}</p>
                    <p><strong>Interpretation:</strong> The correlation is <strong>{significance}</strong> (p {'<' if p_val < 0.05 else '≥'} 0.05)</p>
                    <p><strong>Conclusion:</strong> {'There IS a correlation between prophage burden and AMR gene count.' if p_val < 0.05 else 'There is NO significant correlation between prophage burden and AMR gene count.'}</p>
                </div>

                <h3>Prophage Burden Bins</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Prophage Burden</th>
                            <th>Sample Count</th>
                            <th>Average AMR Genes/Sample</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for bin_name in ['No prophages', '1-2 prophages', '3-5 prophages', '6+ prophages']:
        bin_data = cooccurrence['bins'][bin_name]
        html += f"""
                        <tr>
                            <td><strong>{bin_name}</strong></td>
                            <td>{bin_data['samples']}</td>
                            <td>{bin_data['avg_amr']:.2f}</td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>
            </section>
"""

    # Analysis 2: Temporal co-trends
    html += """
            <section id="temporal">
                <h2>📈 Analysis 2: Temporal Co-Trends (2021-2025)</h2>

                <div class="info-box">
                    <h4>🔍 Question: Do prophage and AMR prevalence track together over time?</h4>
                    <p>This tests whether temporal trends in prophage presence correlate with AMR trends.</p>
                </div>
"""

    trend_corr = temporal['trend_correlation']
    trend_p = temporal['trend_p_value']

    html += f"""
                <div class="stat-box">
                    <h3>Temporal Correlation</h3>
                    <p><strong>Correlation:</strong> r = {trend_corr:.3f} (p = {trend_p:.4f})</p>
                    <p><strong>Result:</strong> {'Significant' if trend_p < 0.05 else 'Not significant'} temporal co-trend</p>
                </div>

                <h3>Year-by-Year Statistics</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Year</th>
                            <th>Total Samples</th>
                            <th>% with AMR</th>
                            <th>% with Prophages</th>
                            <th>Avg AMR/Sample</th>
                            <th>Avg Prophages/Sample</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for year in sorted(temporal['yearly_summary'].keys()):
        stats = temporal['yearly_summary'][year]
        html += f"""
                        <tr>
                            <td><strong>{year}</strong></td>
                            <td>{stats['total_samples']}</td>
                            <td>{stats['pct_with_amr']:.1f}%</td>
                            <td>{stats['pct_with_prophages']:.1f}%</td>
                            <td>{stats['avg_amr_per_sample']:.2f}</td>
                            <td>{stats['avg_prophages_per_sample']:.2f}</td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>
            </section>
"""

    # Analysis 3: Prophage associations
    html += f"""
            <section id="prophages">
                <h2>🧬 Analysis 3: Prophage-Specific AMR Associations</h2>

                <div class="info-box">
                    <h4>🔍 Question: Do certain prophages consistently associate with specific AMR genes?</h4>
                    <p>Identified {prophage_assoc['total_unique_prophages']} unique prophages in the dataset.</p>
                </div>

                <h3>Top 20 Prophages by Sample Count</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Prophage ID</th>
                            <th>Samples</th>
                            <th>AMR Associations</th>
                            <th>Unique AMR Genes</th>
                            <th>Top Associated Genes</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for p in prophage_assoc['prophage_stats']:
        top_genes_str = ', '.join([f"{gene} ({count})" for gene, count in p['top_genes'][:3]])
        html += f"""
                        <tr>
                            <td><code>{p['prophage_id'][:40]}...</code></td>
                            <td>{p['sample_count']}</td>
                            <td>{p['total_amr_associations']}</td>
                            <td>{p['unique_amr_genes']}</td>
                            <td>{top_genes_str}</td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>
            </section>
"""

    # Analysis 4: AMR class patterns
    html += """
            <section id="classes">
                <h2>💊 Analysis 4: AMR Class Patterns</h2>

                <div class="info-box">
                    <h4>🔍 Question: Do certain drug resistance classes appear more frequently with prophages?</h4>
                </div>

                <h3>Top 15 Drug Resistance Classes</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Drug Class</th>
                            <th>Total</th>
                            <th>With Prophage</th>
                            <th>% With Prophage</th>
                            <th>Proximal (≤50kb)</th>
                            <th>% Proximal</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for c in class_patterns[:15]:
        html += f"""
                        <tr>
                            <td><strong>{c['class']}</strong></td>
                            <td>{c['total']}</td>
                            <td>{c['with_prophage']}</td>
                            <td>{c['pct_with_prophage']:.1f}%</td>
                            <td><span class="highlight">{c['proximal']}</span></td>
                            <td>{c['pct_proximal']:.2f}%</td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>
            </section>

            <section id="conclusions">
                <h2>📝 Key Findings & Conclusions</h2>

                <div class="success-box">
                    <h3>✅ Summary of Alternative Connections</h3>
                    <ul style="line-height: 2; margin-left: 20px; margin-top: 10px;">
                        <li><strong>Sample-level co-occurrence:</strong> Statistical correlation between prophage burden and AMR gene count</li>
                        <li><strong>Temporal trends:</strong> Whether prophage and AMR prevalence track together over time</li>
                        <li><strong>Prophage-specific patterns:</strong> Certain prophages consistently near specific AMR genes</li>
                        <li><strong>Drug class associations:</strong> Which resistance classes show prophage co-occurrence</li>
                    </ul>
                </div>

                <div class="alert-box">
                    <h3>⚠️ Important Context</h3>
                    <p>Remember: <strong>0% of AMR genes are truly integrated within prophages</strong>. These alternative connections (co-occurrence, temporal patterns) do NOT necessarily indicate causal relationships or prophage-mediated horizontal gene transfer.</p>
                    <p>Co-occurrence could be due to:</p>
                    <ul style="margin-left: 20px; margin-top: 10px;">
                        <li>Both AMR and prophages being common in E. coli (coincidence)</li>
                        <li>Both responding to similar selective pressures</li>
                        <li>Both being features of certain high-risk clones</li>
                        <li>Shared genomic context (e.g., both on same large genomic island)</li>
                    </ul>
                </div>
            </section>
        </div>
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
    output_html = os.path.expanduser('~/compass_kansas_results/publication_analysis/reports/KANSAS_AMR_PROPHAGE_CONNECTIONS.html')

    print("=" * 70)
    print("Kansas E. coli - AMR-Prophage Connection Analysis")
    print("Alternative Relationships Beyond Physical Distance")
    print("=" * 70)

    # Load data
    colocation_data = load_colocation_data(colocation_csv)

    # Run analyses
    cooccurrence = analyze_sample_level_cooccurrence(colocation_data)
    temporal = analyze_temporal_cotrends(colocation_data)
    prophage_assoc = analyze_prophage_family_associations(colocation_data)
    class_patterns = analyze_amr_class_prophage_patterns(colocation_data)

    # Generate report
    generate_html_report(output_html, cooccurrence, temporal, prophage_assoc, class_patterns)

    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    print("=" * 70)
    print(f"\n📊 Report: {output_html}")
    print("\nKey findings:")
    print(f"  - Sample correlation: r = {cooccurrence['correlation']:.3f} (p = {cooccurrence['p_value']:.4f})")
    print(f"  - Temporal correlation: r = {temporal['trend_correlation']:.3f} (p = {temporal['trend_p_value']:.4f})")
    print(f"  - Unique prophages analyzed: {prophage_assoc['total_unique_prophages']}")
    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
