#!/usr/bin/env python3
"""
Generate interactive HTML dashboard for AMR-prophage analysis.
Creates visualizations and summary tables from CSV exports.
"""
import sys
import csv
from pathlib import Path
from collections import defaultdict, Counter
import json

def load_csv_data(csv_dir):
    """Load all CSV files from directory"""
    csv_dir = Path(csv_dir)

    data = {
        'summary': [],
        'amr_detail': [],
        'prophage_functions': [],
        'colocation': []
    }

    # Load all years
    for summary_file in csv_dir.glob("sample_summary_*.csv"):
        year = summary_file.stem.split('_')[-1]

        with open(summary_file) as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['year'] = year
                data['summary'].append(row)

        # AMR detail
        amr_file = csv_dir / f"amr_gene_detail_{year}.csv"
        if amr_file.exists():
            with open(amr_file) as f:
                reader = csv.DictReader(f)
                data['amr_detail'].extend(list(reader))

        # Prophage functions
        func_file = csv_dir / f"prophage_functions_{year}.csv"
        if func_file.exists():
            with open(func_file) as f:
                reader = csv.DictReader(f)
                data['prophage_functions'].extend(list(reader))

        # Co-location
        coloc_file = csv_dir / f"amr_prophage_colocation_{year}.csv"
        if coloc_file.exists():
            with open(coloc_file) as f:
                reader = csv.DictReader(f)
                data['colocation'].extend(list(reader))

    return data

def generate_html_dashboard(data, output_file):
    """Generate interactive HTML dashboard"""

    # Calculate summary statistics
    years = sorted(set(row['year'] for row in data['summary']))

    # Year-by-year summary
    yearly_stats = {}
    for year in years:
        year_data = [row for row in data['summary'] if row['year'] == year]
        total_samples = len(year_data)
        samples_with_prophage_amr = sum(1 for row in year_data if float(row['amr_on_prophage']) > 0)
        total_amr = sum(int(row['total_amr_genes']) for row in year_data)
        amr_on_prophage = sum(int(row['amr_on_prophage']) for row in year_data)

        yearly_stats[year] = {
            'total_samples': total_samples,
            'samples_with_prophage_amr': samples_with_prophage_amr,
            'pct_samples_with_prophage_amr': (samples_with_prophage_amr / total_samples * 100) if total_samples > 0 else 0,
            'total_amr': total_amr,
            'amr_on_prophage': amr_on_prophage,
            'pct_amr_on_prophage': (amr_on_prophage / total_amr * 100) if total_amr > 0 else 0
        }

    # Top AMR genes on prophages (all years)
    amr_on_prophages = [row for row in data['colocation'] if row['location'] == 'prophage']
    top_prophage_amr = Counter(row['amr_gene'] for row in amr_on_prophages).most_common(15)

    # Top sequence types
    st_counts = Counter(row['st'] for row in data['summary'] if row['st'] != 'Unknown')
    top_sts = st_counts.most_common(10)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AMR-Prophage Analysis Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}

        .header h1 {{
            color: #2d3748;
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}

        .header p {{
            color: #718096;
            font-size: 1.1rem;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .stat-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
        }}

        .stat-value {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}

        .stat-label {{
            color: #718096;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .chart-container {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}

        .chart-container h2 {{
            color: #2d3748;
            margin-bottom: 20px;
            font-size: 1.5rem;
        }}

        .chart-wrapper {{
            position: relative;
            height: 400px;
        }}

        .two-col {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}

        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}

        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e2e8f0;
        }}

        tr:hover {{
            background: #f7fafc;
        }}

        .highlight {{
            background: #fef3c7;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
        }}

        @media (max-width: 768px) {{
            .two-col {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧬 AMR-Prophage Analysis Dashboard</h1>
            <p>Comprehensive analysis of antimicrobial resistance genes and prophage associations in E. coli ({min(years)}-{max(years)})</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{sum(s['total_samples'] for s in yearly_stats.values())}</div>
                <div class="stat-label">Total Samples Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(s['samples_with_prophage_amr'] for s in yearly_stats.values())}</div>
                <div class="stat-label">Samples with Prophage-AMR</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(s['total_amr'] for s in yearly_stats.values())}</div>
                <div class="stat-label">Total AMR Genes Detected</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{sum(s['amr_on_prophage'] for s in yearly_stats.values())}</div>
                <div class="stat-label">AMR Genes on Prophages</div>
            </div>
        </div>

        <div class="two-col">
            <div class="chart-container">
                <h2>📊 AMR-Prophage Co-location by Year</h2>
                <div class="chart-wrapper">
                    <canvas id="yearlyTrendChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h2>🧬 Top AMR Genes on Prophages</h2>
                <div class="chart-wrapper">
                    <canvas id="topAmrGenesChart"></canvas>
                </div>
            </div>
        </div>

        <div class="chart-container">
            <h2>📋 Yearly Statistics</h2>
            <table>
                <thead>
                    <tr>
                        <th>Year</th>
                        <th>Samples</th>
                        <th>Samples w/ Prophage-AMR</th>
                        <th>% Samples</th>
                        <th>Total AMR Genes</th>
                        <th>AMR on Prophages</th>
                        <th>% on Prophages</th>
                    </tr>
                </thead>
                <tbody>
"""

    for year in sorted(yearly_stats.keys()):
        stats = yearly_stats[year]
        html_content += f"""
                    <tr>
                        <td><strong>{year}</strong></td>
                        <td>{stats['total_samples']}</td>
                        <td>{stats['samples_with_prophage_amr']}</td>
                        <td><span class="highlight">{stats['pct_samples_with_prophage_amr']:.1f}%</span></td>
                        <td>{stats['total_amr']}</td>
                        <td>{stats['amr_on_prophage']}</td>
                        <td><span class="highlight">{stats['pct_amr_on_prophage']:.1f}%</span></td>
                    </tr>
"""

    html_content += f"""
                </tbody>
            </table>
        </div>

        <div class="two-col">
            <div class="chart-container">
                <h2>🔬 Top 10 Sequence Types</h2>
                <table>
                    <thead>
                        <tr>
                            <th>ST</th>
                            <th>Count</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for st, count in top_sts:
        html_content += f"""
                        <tr>
                            <td>ST-{st}</td>
                            <td>{count}</td>
                        </tr>
"""

    html_content += f"""
                    </tbody>
                </table>
            </div>

            <div class="chart-container">
                <h2>💊 Top AMR Genes on Prophages</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Gene</th>
                            <th>Count</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    for gene, count in top_prophage_amr:
        html_content += f"""
                        <tr>
                            <td>{gene}</td>
                            <td>{count}</td>
                        </tr>
"""

    # Prepare chart data
    years_list = sorted(yearly_stats.keys())
    pct_samples_data = [yearly_stats[y]['pct_samples_with_prophage_amr'] for y in years_list]
    pct_amr_data = [yearly_stats[y]['pct_amr_on_prophage'] for y in years_list]

    top_genes = [gene for gene, _ in top_prophage_amr]
    top_counts = [count for _, count in top_prophage_amr]

    html_content += f"""
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // Yearly trend chart
        const yearlyCtx = document.getElementById('yearlyTrendChart').getContext('2d');
        new Chart(yearlyCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(years_list)},
                datasets: [
                    {{
                        label: '% Samples with Prophage-AMR',
                        data: {json.dumps(pct_samples_data)},
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    }},
                    {{
                        label: '% AMR Genes on Prophages',
                        data: {json.dumps(pct_amr_data)},
                        borderColor: '#f56565',
                        backgroundColor: 'rgba(245, 101, 101, 0.1)',
                        tension: 0.4,
                        fill: true
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'top',
                    }},
                    title: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{
                            callback: function(value) {{
                                return value + '%';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Top AMR genes chart
        const amrCtx = document.getElementById('topAmrGenesChart').getContext('2d');
        new Chart(amrCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(top_genes)},
                datasets: [{{
                    label: 'Count',
                    data: {json.dumps(top_counts)},
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: '#667eea',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    x: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html_content)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_amr_prophage_dashboard.py <csv_directory> [output_file]")
        print("\nExample:")
        print("  python3 generate_amr_prophage_dashboard.py ~/amr_prophage_analysis_2021-2025/csv_exports ~/dashboard.html")
        sys.exit(1)

    csv_dir = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.home() / "amr_prophage_dashboard.html"

    if not csv_dir.exists():
        print(f"❌ Error: CSV directory not found: {csv_dir}")
        sys.exit(1)

    print("📊 Loading data from CSV files...")
    data = load_csv_data(csv_dir)

    if not data['summary']:
        print("❌ Error: No data found in CSV files")
        sys.exit(1)

    print(f"✅ Loaded {len(data['summary'])} samples")
    print(f"📈 Generating HTML dashboard...")

    generate_html_dashboard(data, output_file)

    print(f"\n✅ Dashboard created successfully!")
    print(f"   Output file: {output_file}")
    print(f"\n🌐 Open in browser: file://{output_file.absolute()}")

if __name__ == "__main__":
    main()
