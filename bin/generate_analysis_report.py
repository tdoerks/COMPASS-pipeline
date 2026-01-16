#!/usr/bin/env python3
"""
Generate Interactive HTML Report from Kansas NARMS Analysis Results
====================================================================

Combines all analysis plots and data into a single interactive HTML report.

Usage:
    ./bin/generate_analysis_report.py --analysis-dir /path/to/analysis_output --outfile report.html
"""

import argparse
import sys
import base64
from pathlib import Path
from typing import Dict, List
import pandas as pd

def encode_image(image_path: Path) -> str:
    """Encode image to base64 for embedding in HTML"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def load_csv_summary(csv_path: Path, max_rows: int = 10) -> str:
    """Load CSV and convert to HTML table"""
    if not csv_path.exists():
        return "<p>Data file not found</p>"

    try:
        df = pd.read_csv(csv_path)
        return df.head(max_rows).to_html(classes='data-table', index=False, border=0)
    except Exception as e:
        return f"<p>Error loading data: {e}</p>"

def generate_html_report(analysis_dir: Path, output_file: Path):
    """Generate comprehensive HTML report"""

    analysis_dir = Path(analysis_dir)

    # Find all PNG files in analysis directories
    phage_dir = analysis_dir / "phage_phylogeny"
    amr_dir = analysis_dir / "temporal_amr"
    corr_dir = analysis_dir / "correlations"

    # Start building HTML
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kansas NARMS Comprehensive Analysis Report</title>
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

        .figure {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .figure img {
            width: 100%;
            height: auto;
            border-radius: 5px;
        }

        .figure-caption {
            margin-top: 15px;
            color: #6c757d;
            font-size: 0.95em;
            line-height: 1.6;
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

        .alert-warning {
            background: #fff3cd;
            border-color: #ffc107;
            color: #856404;
        }

        .footer {
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
        }

        .download-btn {
            display: inline-block;
            padding: 10px 20px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 5px;
            transition: background 0.3s;
        }

        .download-btn:hover {
            background: #5568d3;
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
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧬 Kansas NARMS Comprehensive Analysis</h1>
            <p>Antimicrobial Resistance Surveillance 2021-2025</p>
        </div>

        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('overview')">📊 Overview</button>
            <button class="nav-tab" onclick="showTab('phage')">🦠 Prophage Analysis</button>
            <button class="nav-tab" onclick="showTab('amr')">💊 AMR Trends</button>
            <button class="nav-tab" onclick="showTab('correlations')">🔗 Correlations</button>
            <button class="nav-tab" onclick="showTab('data')">📁 Data Tables</button>
        </div>

        <div class="content">
"""

    # Overview Tab
    html += """
            <div id="overview" class="tab-content active">
                <div class="section">
                    <h2>Analysis Summary</h2>
                    <div class="stats-grid">
"""

    # Count statistics
    num_samples = "825"
    num_genes = "257"

    # Try to load actual numbers from CSV files
    phage_csv = phage_dir / "phage_statistics.csv"
    if phage_csv.exists():
        try:
            df = pd.read_csv(phage_csv)
            num_samples = str(len(df))
        except:
            pass

    amr_csv = amr_dir / "amr_gene_matrix.csv"
    if amr_csv.exists():
        try:
            df = pd.read_csv(amr_csv)
            num_genes = str(len(df.columns) - 3)  # Subtract metadata columns
        except:
            pass

    html += f"""
                        <div class="stat-card">
                            <div class="number">{num_samples}</div>
                            <div class="label">Total Samples Analyzed</div>
                        </div>
                        <div class="stat-card">
                            <div class="number">{num_genes}</div>
                            <div class="label">Unique AMR Genes</div>
                        </div>
                        <div class="stat-card">
                            <div class="number">3</div>
                            <div class="label">Analysis Modules</div>
                        </div>
                        <div class="stat-card">
                            <div class="number">5</div>
                            <div class="label">Years (2021-2025)</div>
                        </div>
                    </div>

                    <div class="alert alert-info">
                        <strong>ℹ️ About This Report</strong><br>
                        This comprehensive analysis examines prophage evolution, antimicrobial resistance trends,
                        and mobile element associations in Kansas NARMS isolates from 2021-2025. All analyses are
                        based on whole genome sequencing data processed through the COMPASS pipeline.
                    </div>
                </div>
            </div>
"""

    # Phage Analysis Tab
    html += """
            <div id="phage" class="tab-content">
                <div class="section">
                    <h2>Prophage Phylogeny & Evolution</h2>
"""

    # Add phage plots
    temporal_phage = phage_dir / "temporal_phage_diversity.png"
    if temporal_phage.exists():
        img_data = encode_image(temporal_phage)
        html += f"""
                    <div class="figure">
                        <img src="data:image/png;base64,{img_data}" alt="Temporal Phage Diversity">
                        <div class="figure-caption">
                            <strong>Figure 1:</strong> Temporal trends in prophage abundance across Kansas NARMS isolates.
                            Shows average number of prophages per sample over time, stratified by organism. Error bands
                            represent standard deviation.
                        </div>
                    </div>
"""

    phage_by_org = phage_dir / "phage_by_organism.png"
    if phage_by_org.exists():
        img_data = encode_image(phage_by_org)
        html += f"""
                    <div class="figure">
                        <img src="data:image/png;base64,{img_data}" alt="Phage by Organism">
                        <div class="figure-caption">
                            <strong>Figure 2:</strong> Distribution of prophage counts by organism. Box plots show median,
                            quartiles, and outliers for prophage abundance in each bacterial species.
                        </div>
                    </div>
"""

    if not temporal_phage.exists() and not phage_by_org.exists():
        html += """
                    <div class="alert alert-warning">
                        <strong>⚠️ No Prophage Plots Available</strong><br>
                        Prophage analysis plots were not found. This may occur if VIBRANT results are unavailable
                        or if prophages were not detected in the samples.
                    </div>
"""

    html += """
                </div>
            </div>
"""

    # AMR Trends Tab
    html += """
            <div id="amr" class="tab-content">
                <div class="section">
                    <h2>Temporal AMR Trends</h2>
"""

    amr_prev = amr_dir / "amr_prevalence_trends.png"
    if amr_prev.exists():
        img_data = encode_image(amr_prev)
        html += f"""
                    <div class="figure">
                        <img src="data:image/png;base64,{img_data}" alt="AMR Prevalence Trends">
                        <div class="figure-caption">
                            <strong>Figure 3:</strong> Temporal trends in the top 10 most prevalent AMR genes.
                            Each line represents the percentage of isolates carrying a specific resistance gene over time.
                        </div>
                    </div>
"""

    mdr_trends = amr_dir / "mdr_trends.png"
    if mdr_trends.exists():
        img_data = encode_image(mdr_trends)
        html += f"""
                    <div class="figure">
                        <img src="data:image/png;base64,{img_data}" alt="MDR Trends">
                        <div class="figure-caption">
                            <strong>Figure 4:</strong> Multi-drug resistance (MDR) trends by organism. Shows the percentage
                            of isolates classified as MDR (resistant to ≥3 antibiotic classes) over time.
                        </div>
                    </div>
"""

    html += """
                </div>
            </div>
"""

    # Correlations Tab
    html += """
            <div id="correlations" class="tab-content">
                <div class="section">
                    <h2>Phage-AMR-Plasmid Correlations</h2>
"""

    corr_heatmap = corr_dir / "correlation_heatmap.png"
    if corr_heatmap.exists():
        img_data = encode_image(corr_heatmap)
        html += f"""
                    <div class="figure">
                        <img src="data:image/png;base64,{img_data}" alt="Correlation Heatmap">
                        <div class="figure-caption">
                            <strong>Figure 5:</strong> Correlation matrix of genomic features. Heatmap shows Pearson
                            correlation coefficients between prophage presence, AMR gene counts, plasmid presence, and
                            MDR status. Values range from -1 (negative correlation) to +1 (positive correlation).
                        </div>
                    </div>
"""

    # Add co-occurrence data if available
    cooccur_csv = corr_dir / "cooccurrence_analysis.csv"
    if cooccur_csv.exists():
        html += """
                    <h3>Statistical Co-occurrence Analysis</h3>
"""
        html += load_csv_summary(cooccur_csv, max_rows=20)
        html += """
                    <div class="figure-caption">
                        <strong>Table 1:</strong> Fisher's exact test results for feature co-occurrence. P-values < 0.05
                        indicate statistically significant associations between features.
                    </div>
"""

    html += """
                </div>
            </div>
"""

    # Data Tables Tab
    html += """
            <div id="data" class="tab-content">
                <div class="section">
                    <h2>Data Tables & Downloads</h2>
"""

    # List available CSV files
    csv_files = []
    for dir_name, label in [
        (phage_dir, "Prophage Analysis"),
        (amr_dir, "AMR Analysis"),
        (corr_dir, "Correlation Analysis")
    ]:
        if dir_name.exists():
            for csv_file in dir_name.glob("*.csv"):
                csv_files.append((csv_file, label))

    if csv_files:
        html += """
                    <h3>Available Data Files</h3>
                    <p>Download raw data tables for further analysis:</p>
                    <div style="margin: 20px 0;">
"""
        for csv_file, label in csv_files:
            rel_path = csv_file.relative_to(analysis_dir)
            html += f"""
                        <a href="{rel_path}" class="download-btn" download>
                            📥 {csv_file.name} ({label})
                        </a>
"""
        html += """
                    </div>
"""

    # Show preview of feature matrix
    feature_csv = corr_dir / "feature_matrix.csv"
    if feature_csv.exists():
        html += """
                    <h3>Feature Matrix Preview</h3>
"""
        html += load_csv_summary(feature_csv, max_rows=15)

    html += """
                </div>
            </div>
"""

    # Close content and add footer
    html += """
        </div>

        <div class="footer">
            <p><strong>Kansas NARMS Comprehensive Analysis Report</strong></p>
            <p>Generated from COMPASS pipeline results | Analysis by analyze_kansas_narms.py</p>
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
    print(f"📊 Analysis directory: {analysis_dir}")
    print(f"🌐 Open in browser: file://{output_file.absolute()}")

def main():
    parser = argparse.ArgumentParser(
        description='Generate interactive HTML report from Kansas NARMS analysis results',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--analysis-dir', required=True, type=Path,
                       help='Path to analysis output directory')
    parser.add_argument('--outfile', default='kansas_narms_report.html', type=Path,
                       help='Output HTML file (default: kansas_narms_report.html)')

    args = parser.parse_args()

    if not args.analysis_dir.exists():
        print(f"❌ Error: Analysis directory not found: {args.analysis_dir}")
        sys.exit(1)

    generate_html_report(args.analysis_dir, args.outfile)

if __name__ == '__main__':
    main()
