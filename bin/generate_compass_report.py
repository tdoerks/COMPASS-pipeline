#!/usr/bin/env python3
"""
Enhanced COMPASS Report Generator
Integrates AMR detection and phage analysis results into a comprehensive HTML report
"""

import pandas as pd
import sys
from pathlib import Path
import json
from collections import defaultdict

def parse_amr_data(amr_files):
    """Parse AMR gene detection files"""
    amr_data = []
    for f in amr_files:
        if Path(f).exists():
            df = pd.read_csv(f, sep='\t')
            if not df.empty:
                sample_id = Path(f).stem.replace('_amr', '')
                df['sample_id'] = sample_id
                amr_data.append(df)
    
    if amr_data:
        return pd.concat(amr_data, ignore_index=True)
    return pd.DataFrame()

def parse_mutation_data(mutation_files):
    """Parse AMR mutation files"""
    mut_data = []
    for f in mutation_files:
        if Path(f).exists():
            df = pd.read_csv(f, sep='\t')
            if not df.empty:
                sample_id = Path(f).stem.replace('_mutations', '')
                df['sample_id'] = sample_id
                mut_data.append(df)
    
    if mut_data:
        return pd.concat(mut_data, ignore_index=True)
    return pd.DataFrame()

def parse_phage_data(phage_files):
    """Parse phage analysis summary files"""
    phage_data = []
    for f in phage_files:
        if Path(f).exists():
            df = pd.read_csv(f, sep='\t')
            if not df.empty:
                phage_data.append(df)
    
    if phage_data:
        return pd.concat(phage_data, ignore_index=True)
    return pd.DataFrame()

def generate_summary_stats(amr_df, phage_df, mut_df):
    """Generate overview statistics"""
    stats = {
        'total_samples': 0,
        'samples_with_amr': 0,
        'samples_with_phages': 0,
        'samples_with_both': 0,
        'total_amr_genes': len(amr_df),
        'total_mutations': len(mut_df),
        'total_phages': 0,
        'unique_resistance_classes': 0
    }
    
    samples = set()
    samples_amr = set()
    samples_phage = set()
    
    if not amr_df.empty:
        samples_amr = set(amr_df['sample_id'].unique())
        samples.update(samples_amr)
        stats['unique_resistance_classes'] = amr_df['resistance_class'].nunique() if 'resistance_class' in amr_df else 0
    
    if not phage_df.empty:
        samples_phage = set(phage_df['sample_id'].unique())
        samples.update(samples_phage)
        stats['total_phages'] = int(phage_df['phage_count'].sum()) if 'phage_count' in phage_df else 0
    
    stats['total_samples'] = len(samples)
    stats['samples_with_amr'] = len(samples_amr)
    stats['samples_with_phages'] = len(samples_phage)
    stats['samples_with_both'] = len(samples_amr & samples_phage)
    
    return stats

def create_integrated_table(amr_df, phage_df, mut_df):
    """Create integrated sample summary table"""
    samples = set()
    if not amr_df.empty:
        samples.update(amr_df['sample_id'].unique())
    if not phage_df.empty:
        samples.update(phage_df['sample_id'].unique())
    
    table_data = []
    
    for sample in sorted(samples):
        row = {'sample_id': sample}
        
        # AMR data
        sample_amr = amr_df[amr_df['sample_id'] == sample] if not amr_df.empty else pd.DataFrame()
        row['amr_gene_count'] = len(sample_amr)
        
        if not sample_amr.empty and 'resistance_class' in sample_amr:
            classes = sample_amr['resistance_class'].unique()
            row['resistance_classes'] = ', '.join(sorted(classes)[:5])
            if len(classes) > 5:
                row['resistance_classes'] += f' (+{len(classes)-5} more)'
        else:
            row['resistance_classes'] = 'None'
        
        # Mutation data
        sample_mut = mut_df[mut_df['sample_id'] == sample] if not mut_df.empty else pd.DataFrame()
        row['mutation_count'] = len(sample_mut)
        
        # Phage data
        sample_phage = phage_df[phage_df['sample_id'] == sample] if not phage_df.empty else pd.DataFrame()
        if not sample_phage.empty:
            row['phage_count'] = int(sample_phage['phage_count'].iloc[0]) if 'phage_count' in sample_phage else 0
            row['lytic_count'] = int(sample_phage['lytic_count'].iloc[0]) if 'lytic_count' in sample_phage else 0
            row['lysogenic_count'] = int(sample_phage['lysogenic_count'].iloc[0]) if 'lysogenic_count' in sample_phage else 0
            row['quality'] = str(sample_phage['quality_summary'].iloc[0]) if 'quality_summary' in sample_phage else 'N/A'
        else:
            row['phage_count'] = 0
            row['lytic_count'] = 0
            row['lysogenic_count'] = 0
            row['quality'] = 'N/A'
        
        table_data.append(row)
    
    return pd.DataFrame(table_data)

def generate_html_report(stats, integrated_table, amr_df, phage_df, mut_df, output_file):
    """Generate comprehensive HTML report with visualizations"""
    
    # Prepare data for visualizations
    amr_class_counts = {}
    if not amr_df.empty and 'resistance_class' in amr_df:
        amr_class_counts = amr_df['resistance_class'].value_counts().to_dict()
    
    phage_quality_counts = {}
    if not phage_df.empty and 'quality_summary' in phage_df:
        for _, row in phage_df.iterrows():
            qualities = str(row['quality_summary']).split(', ')
            for q in qualities:
                if q and q != 'N/A':
                    phage_quality_counts[q] = phage_quality_counts.get(q, 0) + 1
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>COMPASS Pipeline Report</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
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
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.95;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .stat-value {{
            font-size: 2.5em;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 8px;
        }}
        
        .stat-label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .section {{
            padding: 40px;
        }}
        
        .section-title {{
            font-size: 1.8em;
            margin-bottom: 25px;
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }}
        
        .chart-container {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .chart-title {{
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 20px;
            color: #333;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 12px;
            overflow: hidden;
        }}
        
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e9ecef;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .badge-amr {{
            background: #e3f2fd;
            color: #1976d2;
        }}
        
        .badge-phage {{
            background: #f3e5f5;
            color: #7b1fa2;
        }}
        
        .expandable {{
            margin-top: 20px;
        }}
        
        .expandable-header {{
            background: #667eea;
            color: white;
            padding: 15px 20px;
            cursor: pointer;
            border-radius: 8px;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s;
        }}
        
        .expandable-header:hover {{
            background: #5568d3;
        }}
        
        .expandable-content {{
            display: none;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 0 0 8px 8px;
            margin-top: -8px;
        }}
        
        .expandable-content.active {{
            display: block;
        }}
        
        .arrow {{
            transition: transform 0.3s;
        }}
        
        .arrow.active {{
            transform: rotate(180deg);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧬 COMPASS Pipeline Report</h1>
            <p>COmprehensive Mobile element & Pathogen ASsessment Suite</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{stats['total_samples']}</div>
                <div class="stat-label">Total Samples</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['total_amr_genes']}</div>
                <div class="stat-label">AMR Genes Detected</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['total_phages']}</div>
                <div class="stat-label">Phages Detected</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['samples_with_both']}</div>
                <div class="stat-label">Samples with Both</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['unique_resistance_classes']}</div>
                <div class="stat-label">Resistance Classes</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{stats['total_mutations']}</div>
                <div class="stat-label">Mutations Detected</div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">📊 Visualizations</h2>
            <div class="chart-grid">
                <div class="chart-container">
                    <div class="chart-title">AMR Resistance Classes Distribution</div>
                    <canvas id="amrClassChart"></canvas>
                </div>
                <div class="chart-container">
                    <div class="chart-title">Phage Quality Distribution</div>
                    <canvas id="phageQualityChart"></canvas>
                </div>
                <div class="chart-container">
                    <div class="chart-title">Phage Counts per Sample</div>
                    <canvas id="phageCountChart"></canvas>
                </div>
                <div class="chart-container">
                    <div class="chart-title">AMR vs Phage Correlation</div>
                    <canvas id="correlationChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">📋 Integrated Sample Summary</h2>
            <table>
                <thead>
                    <tr>
                        <th>Sample ID</th>
                        <th>AMR Genes</th>
                        <th>Mutations</th>
                        <th>Resistance Classes</th>
                        <th>Phages</th>
                        <th>Lytic</th>
                        <th>Lysogenic</th>
                        <th>Quality</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for _, row in integrated_table.iterrows():
        html += f"""
                    <tr>
                        <td><strong>{row['sample_id']}</strong></td>
                        <td><span class="badge badge-amr">{row['amr_gene_count']}</span></td>
                        <td><span class="badge badge-amr">{row['mutation_count']}</span></td>
                        <td>{row['resistance_classes']}</td>
                        <td><span class="badge badge-phage">{row['phage_count']}</span></td>
                        <td>{row['lytic_count']}</td>
                        <td>{row['lysogenic_count']}</td>
                        <td>{row['quality']}</td>
                    </tr>
"""
    
    html += """
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2 class="section-title">🔍 Detailed Results</h2>
            
            <div class="expandable">
                <div class="expandable-header" onclick="toggleExpand('amr-details')">
                    <span>AMR Gene Details</span>
                    <span class="arrow" id="amr-details-arrow">▼</span>
                </div>
                <div class="expandable-content" id="amr-details">
"""
    
    if not amr_df.empty:
        html += """
                    <table>
                        <thead>
                            <tr>
                                <th>Sample</th>
                                <th>Gene</th>
                                <th>Resistance Class</th>
                                <th>Identity (%)</th>
                                <th>Coverage (%)</th>
                            </tr>
                        </thead>
                        <tbody>
"""
        for _, row in amr_df.iterrows():
            identity = f"{row['identity']:.1f}" if 'identity' in row and pd.notna(row['identity']) else 'N/A'
            coverage = f"{row['coverage']:.1f}" if 'coverage' in row and pd.notna(row['coverage']) else 'N/A'
            html += f"""
                            <tr>
                                <td>{row['sample_id']}</td>
                                <td><strong>{row.get('gene', 'Unknown')}</strong></td>
                                <td>{row.get('resistance_class', 'Unknown')}</td>
                                <td>{identity}</td>
                                <td>{coverage}</td>
                            </tr>
"""
        html += """
                        </tbody>
                    </table>
"""
    else:
        html += '<p>No AMR genes detected.</p>'
    
    html += """
                </div>
            </div>
            
            <div class="expandable">
                <div class="expandable-header" onclick="toggleExpand('mutation-details')">
                    <span>Point Mutation Details</span>
                    <span class="arrow" id="mutation-details-arrow">▼</span>
                </div>
                <div class="expandable-content" id="mutation-details">
"""
    
    if not mut_df.empty:
        html += """
                    <table>
                        <thead>
                            <tr>
                                <th>Sample</th>
                                <th>Gene</th>
                                <th>Mutation</th>
                                <th>Resistance Class</th>
                            </tr>
                        </thead>
                        <tbody>
"""
        for _, row in mut_df.iterrows():
            html += f"""
                            <tr>
                                <td>{row['sample_id']}</td>
                                <td><strong>{row.get('gene', 'Unknown')}</strong></td>
                                <td><code>{row.get('mutation', 'Unknown')}</code></td>
                                <td>{row.get('resistance_class', 'Unknown')}</td>
                            </tr>
"""
        html += """
                        </tbody>
                    </table>
"""
    else:
        html += '<p>No resistance mutations detected.</p>'
    
    html += """
                </div>
            </div>
            
            <div class="expandable">
                <div class="expandable-header" onclick="toggleExpand('phage-details')">
                    <span>Phage Analysis Details</span>
                    <span class="arrow" id="phage-details-arrow">▼</span>
                </div>
                <div class="expandable-content" id="phage-details">
"""
    
    if not phage_df.empty:
        html += """
                    <table>
                        <thead>
                            <tr>
                                <th>Sample</th>
                                <th>Total Phages</th>
                                <th>Lytic</th>
                                <th>Lysogenic</th>
                                <th>Quality Summary</th>
                                <th>Prophage Hits</th>
                                <th>Predicted Genes</th>
                            </tr>
                        </thead>
                        <tbody>
"""
        for _, row in phage_df.iterrows():
            html += f"""
                            <tr>
                                <td>{row['sample_id']}</td>
                                <td><span class="badge badge-phage">{row.get('phage_count', 0)}</span></td>
                                <td>{row.get('lytic_count', 0)}</td>
                                <td>{row.get('lysogenic_count', 0)}</td>
                                <td>{row.get('quality_summary', 'N/A')}</td>
                                <td>{row.get('prophage_hits', 0)}</td>
                                <td>{row.get('predicted_genes', 0)}</td>
                            </tr>
"""
        html += """
                        </tbody>
                    </table>
"""
    else:
        html += '<p>No phages detected.</p>'
    
    html += """
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function toggleExpand(id) {
            const content = document.getElementById(id);
            const arrow = document.getElementById(id + '-arrow');
            content.classList.toggle('active');
            arrow.classList.toggle('active');
        }
        
        const colors = [
            '#667eea', '#764ba2', '#f093fb', '#4facfe',
            '#43e97b', '#fa709a', '#fee140', '#30cfd0'
        ];
        
        const amrClassData = """ + json.dumps(amr_class_counts) + """;
        if (Object.keys(amrClassData).length > 0) {
            new Chart(document.getElementById('amrClassChart'), {
                type: 'bar',
                data: {
                    labels: Object.keys(amrClassData),
                    datasets: [{
                        label: 'Gene Count',
                        data: Object.values(amrClassData),
                        backgroundColor: colors[0],
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { stepSize: 1 }
                        }
                    }
                }
            });
        }
        
        const phageQualityData = """ + json.dumps(phage_quality_counts) + """;
        if (Object.keys(phageQualityData).length > 0) {
            new Chart(document.getElementById('phageQualityChart'), {
                type: 'doughnut',
                data: {
                    labels: Object.keys(phageQualityData),
                    datasets: [{
                        data: Object.values(phageQualityData),
                        backgroundColor: colors,
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
        
        const phageCounts = """ + integrated_table[['sample_id', 'phage_count']].to_json(orient='values') + """;
        if (phageCounts.length > 0) {
            new Chart(document.getElementById('phageCountChart'), {
                type: 'bar',
                data: {
                    labels: phageCounts.map(d => d[0]),
                    datasets: [{
                        label: 'Phages per Sample',
                        data: phageCounts.map(d => d[1]),
                        backgroundColor: colors[1],
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { stepSize: 1 }
                        }
                    }
                }
            });
        }
        
        const correlationData = """ + integrated_table[['amr_gene_count', 'phage_count', 'sample_id']].to_json(orient='values') + """;
        if (correlationData.length > 0) {
            new Chart(document.getElementById('correlationChart'), {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: 'Samples',
                        data: correlationData.map(d => ({x: d[0], y: d[1], label: d[2]})),
                        backgroundColor: colors[0],
                        pointRadius: 6,
                        pointHoverRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.raw.label + ': AMR=' + context.raw.x + ', Phages=' + context.raw.y;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'AMR Gene Count'
                            },
                            beginAtZero: true
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Phage Count'
                            },
                            beginAtZero: true
                        }
                    }
                }
            });
        }
    </script>
</body>
</html>
"""
    
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"Enhanced HTML report generated: {output_file}")

def main():
    if len(sys.argv) < 4:
        print("Usage: python generate_compass_report.py <output_dir> <amr_genes.tsv> <amr_mutations.tsv> <phage_summary.tsv>")
        sys.exit(1)
    
    output_dir = Path(sys.argv[1])
    amr_file = sys.argv[2]
    mut_file = sys.argv[3]
    phage_file = sys.argv[4]
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading data files...")
    print(f"  AMR genes: {amr_file}")
    print(f"  Mutations: {mut_file}")
    print(f"  Phage data: {phage_file}")
    
    # Parse all data
    amr_df = parse_amr_data([amr_file])
    mut_df = parse_mutation_data([mut_file])
    phage_df = parse_phage_data([phage_file])
    
    print(f"Loaded {len(amr_df)} AMR genes, {len(mut_df)} mutations, {len(phage_df)} phage samples")
    
    # Generate summary statistics
    stats = generate_summary_stats(amr_df, phage_df, mut_df)
    
    # Create integrated table
    integrated_table = create_integrated_table(amr_df, phage_df, mut_df)
    
    # Save integrated summary as TSV
    summary_file = output_dir / 'compass_integrated_summary.tsv'
    integrated_table.to_csv(summary_file, sep='\t', index=False)
    print(f"Integrated summary saved: {summary_file}")
    
    # Generate HTML report
    html_file = output_dir / 'compass_report.html'
    generate_html_report(stats, integrated_table, amr_df, phage_df, mut_df, html_file)
    
    print("Report generation complete!")

if __name__ == '__main__':
    main()