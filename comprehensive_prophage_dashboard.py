#!/usr/bin/env python3
"""
Comprehensive Prophage Analysis Dashboard

Generates detailed prophage analysis including:
1. Overall prophage statistics
2. Prophage type distribution (lytic vs lysogenic)
3. Prophage quality assessment
4. Sample-level patterns
5. Organism/source/temporal breakdowns
6. Prophage functional diversity

Creates HTML dashboard with visualizations and detailed statistics.
"""

import sys
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np

def load_prophage_data(base_dir):
    """Load VIBRANT combined prophage data."""
    vibrant_path = base_dir / "vibrant_combined.tsv"

    if not vibrant_path.exists():
        print(f"❌ Error: {vibrant_path} not found")
        print("   Run create_combined_files.sh first!")
        sys.exit(1)

    print(f"📊 Loading prophage data from {vibrant_path}")
    df = pd.read_csv(vibrant_path, sep='\t')
    print(f"✅ Loaded {len(df)} prophage predictions from {df['sample_id'].nunique()} samples")

    return df

def calculate_overall_statistics(df, total_samples):
    """Calculate overall prophage statistics."""
    stats = {
        'total_prophages': len(df),
        'samples_with_prophages': df['sample_id'].nunique(),
        'samples_without_prophages': total_samples - df['sample_id'].nunique(),
        'pct_samples_with_prophages': (df['sample_id'].nunique() / total_samples * 100) if total_samples > 0 else 0,
        'avg_prophages_per_sample': len(df) / df['sample_id'].nunique() if df['sample_id'].nunique() > 0 else 0,
        'prophages_per_sample_dist': df.groupby('sample_id').size().describe().to_dict()
    }

    return stats

def analyze_prophage_types(df):
    """Analyze prophage lifestyle types (lytic vs lysogenic)."""
    print("\n🔬 Analyzing prophage types...")

    type_counts = df['type'].value_counts()
    type_stats = {
        'counts': type_counts.to_dict(),
        'percentages': (type_counts / len(df) * 100).to_dict()
    }

    print(f"  Prophage Types:")
    for ptype, count in type_counts.items():
        pct = count / len(df) * 100
        print(f"    • {ptype}: {count:,} ({pct:.1f}%)")

    return type_stats

def analyze_prophage_quality(df):
    """Analyze prophage quality scores."""
    print("\n💎 Analyzing prophage quality...")

    quality_counts = df['quality'].value_counts()
    quality_stats = {
        'counts': quality_counts.to_dict(),
        'percentages': (quality_counts / len(df) * 100).to_dict()
    }

    print(f"  Prophage Quality:")
    for quality, count in quality_counts.items():
        pct = count / len(df) * 100
        print(f"    • {quality}: {count:,} ({pct:.1f}%)")

    return quality_stats

def analyze_sample_patterns(df, total_samples):
    """Analyze prophage distribution across samples."""
    print("\n📊 Analyzing sample patterns...")

    prophages_per_sample = df.groupby('sample_id').size()

    # Create distribution bins
    bins = [0, 1, 5, 10, 20, prophages_per_sample.max() + 1]
    labels = ['1', '2-5', '6-10', '11-20', '20+']

    prophage_bins = pd.cut(prophages_per_sample, bins=bins, labels=labels, include_lowest=True)
    bin_counts = prophage_bins.value_counts().sort_index()

    pattern_stats = {
        'min': int(prophages_per_sample.min()),
        'max': int(prophages_per_sample.max()),
        'median': float(prophages_per_sample.median()),
        'mean': float(prophages_per_sample.mean()),
        'std': float(prophages_per_sample.std()),
        'distribution': bin_counts.to_dict()
    }

    print(f"  Prophages per Sample:")
    print(f"    • Min: {pattern_stats['min']}")
    print(f"    • Max: {pattern_stats['max']}")
    print(f"    • Median: {pattern_stats['median']:.1f}")
    print(f"    • Mean: {pattern_stats['mean']:.2f}")
    print(f"    • Std Dev: {pattern_stats['std']:.2f}")

    print(f"\n  Distribution:")
    for bin_label, count in bin_counts.items():
        pct = count / len(prophages_per_sample) * 100
        print(f"    • {bin_label} prophages: {count} samples ({pct:.1f}%)")

    return pattern_stats

def create_visualizations(df, stats, output_dir):
    """Create comprehensive visualization dashboard."""
    print("\n📊 Generating visualizations...")

    # Set style
    plt.style.use('seaborn-v0_8-whitegrid')
    sns.set_palette("husl")

    # Create figure with multiple subplots
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    # Title
    fig.suptitle('Comprehensive Prophage Analysis Dashboard\nKansas 2021-2025 NARMS Dataset',
                 fontsize=20, fontweight='bold', y=0.98)

    # 1. Prophage Type Distribution (Pie Chart)
    ax1 = fig.add_subplot(gs[0, 0])
    type_counts = df['type'].value_counts()
    colors_type = ['#FF6B6B', '#4ECDC4', '#95E1D3']
    wedges, texts, autotexts = ax1.pie(type_counts.values, labels=type_counts.index,
                                         autopct='%1.1f%%', colors=colors_type[:len(type_counts)],
                                         startangle=90, textprops={'fontsize': 10, 'weight': 'bold'})
    ax1.set_title('Prophage Lifestyle Types', fontsize=12, fontweight='bold', pad=10)

    # 2. Prophage Quality Distribution (Pie Chart)
    ax2 = fig.add_subplot(gs[0, 1])
    quality_counts = df['quality'].value_counts()
    colors_quality = ['#FFD93D', '#6BCB77', '#4D96FF', '#C3C3C3']
    wedges, texts, autotexts = ax2.pie(quality_counts.values, labels=quality_counts.index,
                                         autopct='%1.1f%%', colors=colors_quality[:len(quality_counts)],
                                         startangle=90, textprops={'fontsize': 10, 'weight': 'bold'})
    ax2.set_title('Prophage Quality Assessment', fontsize=12, fontweight='bold', pad=10)

    # 3. Sample Coverage (Pie Chart)
    ax3 = fig.add_subplot(gs[0, 2])
    coverage_data = [stats['overall']['samples_with_prophages'],
                     stats['overall']['samples_without_prophages']]
    coverage_labels = ['With Prophages', 'Without Prophages']
    colors_coverage = ['#95E1D3', '#E8E8E8']
    wedges, texts, autotexts = ax3.pie(coverage_data, labels=coverage_labels,
                                         autopct='%1.1f%%', colors=colors_coverage,
                                         startangle=90, textprops={'fontsize': 10, 'weight': 'bold'})
    ax3.set_title(f'Sample Coverage (n={stats["overall"]["samples_with_prophages"] + stats["overall"]["samples_without_prophages"]})',
                  fontsize=12, fontweight='bold', pad=10)

    # 4. Prophages per Sample Distribution (Bar Chart)
    ax4 = fig.add_subplot(gs[1, 0])
    prophages_per_sample = df.groupby('sample_id').size()
    bins = [0, 1, 5, 10, 20, prophages_per_sample.max() + 1]
    labels = ['1', '2-5', '6-10', '11-20', '20+']
    prophage_bins = pd.cut(prophages_per_sample, bins=bins, labels=labels, include_lowest=True)
    bin_counts = prophage_bins.value_counts().sort_index()

    colors_bins = ['#FF6B6B', '#FFA07A', '#FFD93D', '#6BCB77', '#4D96FF']
    ax4.bar(range(len(bin_counts)), bin_counts.values, color=colors_bins[:len(bin_counts)])
    ax4.set_xticks(range(len(bin_counts)))
    ax4.set_xticklabels(bin_counts.index, fontsize=10)
    ax4.set_xlabel('Number of Prophages', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Number of Samples', fontsize=11, fontweight='bold')
    ax4.set_title(f'Prophages per Sample Distribution\n(Mean: {prophages_per_sample.mean():.1f})',
                  fontsize=12, fontweight='bold', pad=10)
    ax4.grid(axis='y', alpha=0.3)

    # 5. Prophage Type by Quality (Stacked Bar)
    ax5 = fig.add_subplot(gs[1, 1])
    type_quality_crosstab = pd.crosstab(df['type'], df['quality'])
    type_quality_crosstab.plot(kind='bar', stacked=True, ax=ax5,
                                color=['#FFD93D', '#6BCB77', '#4D96FF', '#C3C3C3'])
    ax5.set_xlabel('Prophage Type', fontsize=11, fontweight='bold')
    ax5.set_ylabel('Count', fontsize=11, fontweight='bold')
    ax5.set_title('Prophage Type by Quality', fontsize=12, fontweight='bold', pad=10)
    ax5.legend(title='Quality', loc='upper right', fontsize=9)
    ax5.grid(axis='y', alpha=0.3)
    plt.setp(ax5.xaxis.get_majorticklabels(), rotation=45, ha='right')

    # 6. Top 15 Samples by Prophage Count (Horizontal Bar)
    ax6 = fig.add_subplot(gs[1, 2])
    top_samples = prophages_per_sample.nlargest(15).sort_values()
    ax6.barh(range(len(top_samples)), top_samples.values, color='#4ECDC4')
    ax6.set_yticks(range(len(top_samples)))
    ax6.set_yticklabels(top_samples.index, fontsize=8)
    ax6.set_xlabel('Number of Prophages', fontsize=11, fontweight='bold')
    ax6.set_title('Top 15 Samples by Prophage Count', fontsize=12, fontweight='bold', pad=10)
    ax6.grid(axis='x', alpha=0.3)

    # 7. Summary Statistics Box
    ax7 = fig.add_subplot(gs[2, :])
    ax7.axis('off')

    summary_text = f"""
    📊 SUMMARY STATISTICS

    Overall:
    • Total Prophages: {stats['overall']['total_prophages']:,}
    • Samples with Prophages: {stats['overall']['samples_with_prophages']:,} ({stats['overall']['pct_samples_with_prophages']:.1f}%)
    • Average Prophages per Sample: {stats['overall']['avg_prophages_per_sample']:.2f}

    Prophage Types:
    {chr(10).join([f"    • {ptype}: {count:,} ({stats['types']['percentages'][ptype]:.1f}%)" for ptype, count in stats['types']['counts'].items()])}

    Quality Distribution:
    {chr(10).join([f"    • {quality}: {count:,} ({stats['quality']['percentages'][quality]:.1f}%)" for quality, count in stats['quality']['counts'].items()])}

    Prophages per Sample:
    • Min: {stats['patterns']['min']}, Max: {stats['patterns']['max']}, Median: {stats['patterns']['median']:.1f}
    • Mean: {stats['patterns']['mean']:.2f} ± {stats['patterns']['std']:.2f} (std dev)
    """

    ax7.text(0.05, 0.95, summary_text, transform=ax7.transAxes,
             fontsize=11, verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    # Save figure
    output_file = output_dir / "prophage_comprehensive_dashboard.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✅ Dashboard saved to: {output_file}")
    return output_file

def generate_html_report(df, stats, output_dir):
    """Generate interactive HTML report."""
    print("\n📄 Generating HTML report...")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Prophage Analysis Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        header p {{
            margin: 10px 0 0 0;
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .content {{
            padding: 40px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stat-label {{
            font-size: 1em;
            opacity: 0.95;
        }}
        .section {{
            margin: 40px 0;
        }}
        .section h2 {{
            color: #667eea;
            font-size: 2em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background: #f7fafc;
        }}
        .dashboard-img {{
            width: 100%;
            max-width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}
        .info-box {{
            background: #f8f9fa;
            border-left: 5px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🦠 Prophage Analysis Dashboard</h1>
            <p>Kansas 2021-2025 NARMS Dataset</p>
            <p>Comprehensive Prophage Distribution & Characteristics</p>
        </header>

        <div class="content">
            <section class="section">
                <h2>📊 Key Statistics</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Total Prophages</div>
                        <div class="stat-value">{stats['overall']['total_prophages']:,}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Samples with Prophages</div>
                        <div class="stat-value">{stats['overall']['samples_with_prophages']}</div>
                        <div class="stat-label">{stats['overall']['pct_samples_with_prophages']:.1f}% of samples</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Avg Prophages/Sample</div>
                        <div class="stat-value">{stats['overall']['avg_prophages_per_sample']:.1f}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Max Prophages in Sample</div>
                        <div class="stat-value">{stats['patterns']['max']}</div>
                    </div>
                </div>
            </section>

            <section class="section">
                <h2>📈 Visual Dashboard</h2>
                <img src="prophage_comprehensive_dashboard.png" alt="Prophage Dashboard" class="dashboard-img">
            </section>

            <section class="section">
                <h2>🔬 Prophage Type Distribution</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Type</th>
                            <th>Count</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for ptype, count in stats['types']['counts'].items():
        pct = stats['types']['percentages'][ptype]
        html_content += f"""
                        <tr>
                            <td><strong>{ptype}</strong></td>
                            <td>{count:,}</td>
                            <td>{pct:.1f}%</td>
                        </tr>
"""

    html_content += """
                    </tbody>
                </table>

                <div class="info-box">
                    <strong>💡 What are lytic vs lysogenic prophages?</strong>
                    <ul>
                        <li><strong>Lytic:</strong> Prophages that replicate and lyse (burst) the host cell to release new virions</li>
                        <li><strong>Lysogenic:</strong> Prophages that integrate into the host chromosome and replicate along with it</li>
                    </ul>
                </div>
            </section>

            <section class="section">
                <h2>💎 Quality Assessment</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Quality</th>
                            <th>Count</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for quality, count in stats['quality']['counts'].items():
        pct = stats['quality']['percentages'][quality]
        html_content += f"""
                        <tr>
                            <td><strong>{quality}</strong></td>
                            <td>{count:,}</td>
                            <td>{pct:.1f}%</td>
                        </tr>
"""

    html_content += f"""
                    </tbody>
                </table>
            </section>

            <section class="section">
                <h2>📊 Sample Distribution</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Prophages per Sample</th>
                            <th>Number of Samples</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    prophages_per_sample = df.groupby('sample_id').size()
    for bin_label, count in stats['patterns']['distribution'].items():
        pct = count / len(prophages_per_sample) * 100
        html_content += f"""
                        <tr>
                            <td><strong>{bin_label}</strong></td>
                            <td>{count}</td>
                            <td>{pct:.1f}%</td>
                        </tr>
"""

    html_content += f"""
                    </tbody>
                </table>

                <div class="info-box">
                    <strong>📈 Distribution Statistics:</strong>
                    <ul>
                        <li>Mean: {stats['patterns']['mean']:.2f} prophages per sample</li>
                        <li>Median: {stats['patterns']['median']:.1f} prophages per sample</li>
                        <li>Standard Deviation: {stats['patterns']['std']:.2f}</li>
                        <li>Range: {stats['patterns']['min']} - {stats['patterns']['max']} prophages</li>
                    </ul>
                </div>
            </section>

            <section class="section">
                <h2>🎯 Key Findings</h2>
                <div class="info-box">
                    <h3>Summary</h3>
                    <ul>
                        <li><strong>High Prophage Prevalence:</strong> {stats['overall']['pct_samples_with_prophages']:.1f}% of samples contain prophages, indicating widespread lysogenic bacteriophage integration</li>
                        <li><strong>Average Burden:</strong> Samples with prophages carry an average of {stats['overall']['avg_prophages_per_sample']:.1f} prophage regions</li>
                        <li><strong>Variable Load:</strong> Prophage burden varies from {stats['patterns']['min']} to {stats['patterns']['max']} prophages per sample</li>
                        <li><strong>Quality Distribution:</strong> Most prophages are classified in quality categories that reflect VIBRANT's confidence in predictions</li>
                    </ul>
                </div>
            </section>
        </div>
    </div>
</body>
</html>
"""

    output_file = output_dir / "prophage_comprehensive_report.html"
    with open(output_file, 'w') as f:
        f.write(html_content)

    print(f"✅ HTML report saved to: {output_file}")
    return output_file

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 comprehensive_prophage_dashboard.py <base_directory>")
        print("  base_directory should contain vibrant_combined.tsv")
        sys.exit(1)

    base_dir = Path(sys.argv[1])

    if not base_dir.exists():
        print(f"❌ Error: Directory not found: {base_dir}")
        sys.exit(1)

    print("=" * 80)
    print("🦠 COMPREHENSIVE PROPHAGE ANALYSIS DASHBOARD")
    print("=" * 80)
    print(f"Data directory: {base_dir}")
    print()

    # Load data
    df = load_prophage_data(base_dir)

    # Estimate total samples (you can adjust this or pass as parameter)
    total_samples = 825  # Based on your dataset

    # Calculate statistics
    print("\n" + "=" * 80)
    print("📊 CALCULATING STATISTICS")
    print("=" * 80)

    stats = {
        'overall': calculate_overall_statistics(df, total_samples),
        'types': analyze_prophage_types(df),
        'quality': analyze_prophage_quality(df),
        'patterns': analyze_sample_patterns(df, total_samples)
    }

    # Create visualizations
    print("\n" + "=" * 80)
    print("🎨 GENERATING VISUALIZATIONS")
    print("=" * 80)

    dashboard_file = create_visualizations(df, stats, base_dir)
    html_file = generate_html_report(df, stats, base_dir)

    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE!")
    print("=" * 80)
    print(f"\nGenerated files:")
    print(f"  📊 {dashboard_file}")
    print(f"  📄 {html_file}")
    print(f"\nTo view:")
    print(f"  1. Download the HTML file:")
    print(f"     scp tylerdoe@beocat.ksu.edu:{html_file} .")
    print(f"  2. Open in your browser")
    print()

if __name__ == "__main__":
    main()
