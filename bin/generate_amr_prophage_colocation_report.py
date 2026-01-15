#!/usr/bin/env python3
"""
Generate Interactive HTML Report for AMR-Prophage Co-location Analysis
======================================================================

Creates a beautiful, interactive HTML report showing which AMR genes
are physically located within prophage regions.

Usage:
    ./bin/generate_amr_prophage_colocation_report.py \
        --csv colocation_results.csv \
        --outfile report.html
"""

import argparse
import sys
from pathlib import Path
from collections import Counter, defaultdict
import pandas as pd

def generate_html_report(csv_file: Path, output_file: Path):
    """Generate comprehensive HTML report from colocation CSV"""

    # Load CSV data
    try:
        df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        sys.exit(1)

    # Filter to only within-prophage hits
    df_within = df[df['category'] == 'within_prophage'].copy()

    # Calculate statistics
    total_amr = len(df)
    total_within = len(df_within)
    pct_within = (total_within / total_amr * 100) if total_amr > 0 else 0

    # Top genes
    top_genes = df_within['amr_gene'].value_counts().head(15)

    # Top drug classes
    top_classes = df_within['amr_class'].value_counts().head(10)

    # By organism
    organism_stats = []
    for organism in df['organism'].unique():
        org_df = df[df['organism'] == organism]
        org_within = len(org_df[org_df['category'] == 'within_prophage'])
        org_total = len(org_df)
        org_pct = (org_within / org_total * 100) if org_total > 0 else 0
        organism_stats.append({
            'organism': organism,
            'within': org_within,
            'total': org_total,
            'percentage': org_pct
        })
    organism_stats = sorted(organism_stats, key=lambda x: x['within'], reverse=True)

    # By year
    year_stats = []
    for year in sorted(df['year'].unique()):
        year_df = df[df['year'] == year]
        year_within = len(year_df[year_df['category'] == 'within_prophage'])
        year_total = len(year_df)
        year_pct = (year_within / year_total * 100) if year_total > 0 else 0
        year_stats.append({
            'year': year,
            'within': year_within,
            'total': year_total,
            'percentage': year_pct
        })

    # Unique samples with prophage-carried AMR
    samples_with_coloc = df_within['sample'].nunique()
    total_samples = df['sample'].nunique()

    # Start building HTML
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AMR-Prophage Co-location Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }

        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }

        .header p {
            font-size: 1.2em;
            opacity: 0.95;
        }

        .nav-tabs {
            display: flex;
            background: #f8f9fa;
            border-bottom: 2px solid #dee2e6;
            padding: 0 20px;
            overflow-x: auto;
        }

        .nav-tab {
            padding: 15px 25px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 1em;
            font-weight: 600;
            color: #6c757d;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
            white-space: nowrap;
        }

        .nav-tab:hover {
            color: #495057;
            background: rgba(0, 0, 0, 0.02);
        }

        .nav-tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }

        .content {
            padding: 40px;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
            animation: fadeIn 0.3s;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .section {
            margin-bottom: 40px;
        }

        .section h2 {
            color: #2c3e50;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }

        .section h3 {
            color: #34495e;
            font-size: 1.4em;
            margin: 30px 0 15px 0;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }

        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }

        .stat-card .number {
            font-size: 2.5em;
            font-weight: 700;
            margin-bottom: 5px;
        }

        .stat-card .label {
            font-size: 1em;
            opacity: 0.95;
        }

        .highlight-box {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin: 30px 0;
            text-align: center;
            box-shadow: 0 4px 12px rgba(240, 147, 251, 0.3);
        }

        .highlight-box h2 {
            color: white;
            border: none;
            margin: 0 0 10px 0;
            font-size: 2em;
        }

        .highlight-box p {
            font-size: 1.2em;
            opacity: 0.95;
        }

        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.9em;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            border-radius: 5px;
            overflow: hidden;
        }

        .data-table thead tr {
            background: #667eea;
            color: white;
            text-align: left;
        }

        .data-table th,
        .data-table td {
            padding: 12px 15px;
        }

        .data-table tbody tr {
            border-bottom: 1px solid #dee2e6;
        }

        .data-table tbody tr:hover {
            background: #f8f9fa;
        }

        .data-table tbody tr:nth-of-type(even) {
            background: #f8f9fa;
        }

        .bar-chart {
            margin: 20px 0;
        }

        .bar-row {
            display: flex;
            align-items: center;
            margin: 10px 0;
        }

        .bar-label {
            width: 150px;
            font-weight: 600;
            color: #34495e;
            font-size: 0.9em;
        }

        .bar-container {
            flex: 1;
            background: #e9ecef;
            border-radius: 5px;
            overflow: hidden;
            height: 30px;
            position: relative;
        }

        .bar-fill {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 10px;
            color: white;
            font-weight: 600;
            font-size: 0.85em;
            transition: width 0.5s ease;
        }

        .alert {
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }

        .alert-info {
            background: #d1ecf1;
            border-color: #17a2b8;
            color: #0c5460;
        }

        .alert-success {
            background: #d4edda;
            border-color: #28a745;
            color: #155724;
        }

        .footer {
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
        }

        .percentage-badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 5px;
            font-weight: 600;
            font-size: 0.9em;
        }

        .badge-low {
            background: #d4edda;
            color: #155724;
        }

        .badge-medium {
            background: #fff3cd;
            color: #856404;
        }

        .badge-high {
            background: #f8d7da;
            color: #721c24;
        }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8em;
            }

            .content {
                padding: 20px;
            }

            .stats-grid {
                grid-template-columns: 1fr;
            }

            .bar-label {
                width: 100px;
                font-size: 0.8em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🦠 AMR-Prophage Co-location Analysis</h1>
            <p>Resistance Genes Carried by Mobile Prophage Elements</p>
        </div>

        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('overview')">📊 Overview</button>
            <button class="nav-tab" onclick="showTab('genes')">🧬 Genes</button>
            <button class="nav-tab" onclick="showTab('organisms')">🦠 Organisms</button>
            <button class="nav-tab" onclick="showTab('temporal')">📅 Temporal</button>
            <button class="nav-tab" onclick="showTab('data')">📁 Data</button>
        </div>

        <div class="content">
"""

    # Overview Tab
    html += f"""
            <div id="overview" class="tab-content active">
                <div class="section">
                    <h2>Analysis Summary</h2>

                    <div class="highlight-box">
                        <h2>{total_within:,}</h2>
                        <p>AMR genes physically located inside prophage regions</p>
                        <p style="margin-top: 10px; font-size: 1.1em;">
                            {pct_within:.2f}% of all {total_amr:,} AMR genes detected
                        </p>
                    </div>

                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="number">{total_samples:,}</div>
                            <div class="label">Total Samples</div>
                        </div>
                        <div class="stat-card">
                            <div class="number">{samples_with_coloc:,}</div>
                            <div class="label">Samples with Prophage-Carried AMR</div>
                        </div>
                        <div class="stat-card">
                            <div class="number">{len(top_genes)}</div>
                            <div class="label">Unique AMR Genes in Prophages</div>
                        </div>
                        <div class="stat-card">
                            <div class="number">{len(top_classes)}</div>
                            <div class="label">Drug Classes Affected</div>
                        </div>
                    </div>

                    <div class="alert alert-info">
                        <strong>ℹ️ About This Analysis</strong><br>
                        This report identifies AMR genes that are physically located <strong>within</strong> prophage
                        region boundaries based on genomic coordinates. These genes are potentially mobile - they can
                        be transferred to other bacteria when the prophage becomes active and infects new hosts.
                    </div>
                </div>
            </div>
"""

    # Genes Tab
    html += """
            <div id="genes" class="tab-content">
                <div class="section">
                    <h2>AMR Genes Inside Prophages</h2>

                    <h3>Top AMR Genes</h3>
                    <div class="bar-chart">
"""

    max_count = top_genes.max() if len(top_genes) > 0 else 1
    for gene, count in top_genes.items():
        width_pct = (count / max_count * 100)
        html += f"""
                        <div class="bar-row">
                            <div class="bar-label">{gene}</div>
                            <div class="bar-container">
                                <div class="bar-fill" style="width: {width_pct}%">{count}</div>
                            </div>
                        </div>
"""

    html += """
                    </div>

                    <h3>Drug Resistance Classes</h3>
                    <div class="bar-chart">
"""

    max_class_count = top_classes.max() if len(top_classes) > 0 else 1
    for drug_class, count in top_classes.items():
        width_pct = (count / max_class_count * 100)
        html += f"""
                        <div class="bar-row">
                            <div class="bar-label" style="width: 250px;">{drug_class}</div>
                            <div class="bar-container">
                                <div class="bar-fill" style="width: {width_pct}%">{count}</div>
                            </div>
                        </div>
"""

    html += """
                    </div>
                </div>
            </div>
"""

    # Organisms Tab
    html += """
            <div id="organisms" class="tab-content">
                <div class="section">
                    <h2>Prophage-Carried AMR by Organism</h2>

                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Organism</th>
                                <th>AMR in Prophages</th>
                                <th>Total AMR Genes</th>
                                <th>Percentage</th>
                            </tr>
                        </thead>
                        <tbody>
"""

    for org in organism_stats:
        badge_class = 'badge-low' if org['percentage'] < 5 else 'badge-medium' if org['percentage'] < 15 else 'badge-high'
        html += f"""
                            <tr>
                                <td><strong>{org['organism']}</strong></td>
                                <td>{org['within']:,}</td>
                                <td>{org['total']:,}</td>
                                <td><span class="percentage-badge {badge_class}">{org['percentage']:.2f}%</span></td>
                            </tr>
"""

    html += """
                        </tbody>
                    </table>

                    <div class="alert alert-success">
                        <strong>✅ Key Finding</strong><br>
                        Organisms with higher percentages have more of their AMR genes associated with mobile
                        prophage elements, potentially indicating greater horizontal gene transfer activity.
                    </div>
                </div>
            </div>
"""

    # Temporal Tab
    html += """
            <div id="temporal" class="tab-content">
                <div class="section">
                    <h2>Temporal Trends</h2>

                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Year</th>
                                <th>AMR in Prophages</th>
                                <th>Total AMR Genes</th>
                                <th>Percentage</th>
                            </tr>
                        </thead>
                        <tbody>
"""

    for year_data in year_stats:
        badge_class = 'badge-low' if year_data['percentage'] < 5 else 'badge-medium' if year_data['percentage'] < 15 else 'badge-high'
        html += f"""
                            <tr>
                                <td><strong>{year_data['year']}</strong></td>
                                <td>{year_data['within']:,}</td>
                                <td>{year_data['total']:,}</td>
                                <td><span class="percentage-badge {badge_class}">{year_data['percentage']:.2f}%</span></td>
                            </tr>
"""

    html += """
                        </tbody>
                    </table>

                    <div class="bar-chart">
"""

    max_year_count = max([y['within'] for y in year_stats]) if year_stats else 1
    for year_data in year_stats:
        width_pct = (year_data['within'] / max_year_count * 100)
        html += f"""
                        <div class="bar-row">
                            <div class="bar-label">{year_data['year']}</div>
                            <div class="bar-container">
                                <div class="bar-fill" style="width: {width_pct}%">{year_data['within']}</div>
                            </div>
                        </div>
"""

    html += """
                    </div>
                </div>
            </div>
"""

    # Data Tab
    html += """
            <div id="data" class="tab-content">
                <div class="section">
                    <h2>Detailed Data</h2>

                    <h3>Prophage-Associated AMR Genes (Preview)</h3>
"""

    # Show preview of within-prophage data
    preview_df = df_within[['sample', 'organism', 'year', 'amr_gene', 'amr_class', 'contig', 'distance']].head(50)
    html += preview_df.to_html(classes='data-table', index=False, border=0)

    html += f"""
                    <div class="alert alert-info" style="margin-top: 30px;">
                        <strong>📊 Full Dataset</strong><br>
                        Showing first 50 of {len(df_within):,} prophage-associated AMR genes.
                        Download the complete CSV file for full analysis.
                    </div>
                </div>
            </div>
"""

    # Close content and add footer
    html += """
        </div>

        <div class="footer">
            <p><strong>AMR-Prophage Co-location Analysis Report</strong></p>
            <p>Generated from COMPASS pipeline results | Physical coordinate-based analysis</p>
            <p style="margin-top: 10px; font-size: 0.9em;">
                🤖 Report generated with <a href="https://claude.com/claude-code" style="color: #667eea;">Claude Code</a>
            </p>
        </div>
    </div>

    <script>
        function showTab(tabName) {
            // Hide all tabs
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.classList.remove('active'));

            // Remove active from all nav tabs
            const navTabs = document.querySelectorAll('.nav-tab');
            navTabs.forEach(tab => tab.classList.remove('active'));

            // Show selected tab
            document.getElementById(tabName).classList.add('active');

            // Activate nav tab
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
"""

    # Write HTML file
    with open(output_file, 'w') as f:
        f.write(html)

    print(f"✅ Generated interactive HTML report: {output_file}")
    print(f"📊 Total AMR genes: {total_amr:,}")
    print(f"🦠 Prophage-carried AMR: {total_within:,} ({pct_within:.2f}%)")
    print(f"🌐 Open in browser: file://{output_file.absolute()}")

def main():
    parser = argparse.ArgumentParser(
        description='Generate interactive HTML report from AMR-prophage co-location CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--csv', required=True, type=Path,
                       help='Path to co-location CSV file')
    parser.add_argument('--outfile', default='amr_prophage_colocation_report.html', type=Path,
                       help='Output HTML file (default: amr_prophage_colocation_report.html)')

    args = parser.parse_args()

    if not args.csv.exists():
        print(f"❌ Error: CSV file not found: {args.csv}")
        sys.exit(1)

    generate_html_report(args.csv, args.outfile)

if __name__ == '__main__':
    main()
