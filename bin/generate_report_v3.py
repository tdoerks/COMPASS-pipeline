#!/usr/bin/env python3
"""
Enhanced COMPASS Pipeline Report with Cross-Reference Analysis
"""

import sys, os, csv, json
from pathlib import Path
from datetime import datetime
from collections import Counter

def read_tsv(file_path, max_rows=None):
    try:
        with open(file_path) as f:
            reader = csv.DictReader(f, delimiter='\t')
            rows = list(reader)
            return rows[:max_rows] if max_rows else rows
    except:
        return []

def collect_all_results(results_dir):
    results_dir = Path(results_dir)
    data = {'amr': {}, 'phage': {}, 'mlst': {}, 'sistr': {}, 'mobsuite': {}, 'busco': {}, 'metadata': {}}
    
    # AMR
    amr_dir = results_dir / 'amrfinder'
    if amr_dir.exists():
        for f in amr_dir.glob('*_amr.tsv'):
            data['amr'][f.stem.replace('_amr', '')] = read_tsv(f)
    
    # Phage
    vibrant_dir = results_dir / 'vibrant'
    if vibrant_dir.exists():
        for d in vibrant_dir.glob('*_vibrant'):
            sample = d.name.replace('_vibrant', '')
            summaries = list(d.glob('**/VIBRANT_summary_results*.tsv'))
            if summaries:
                data['phage'][sample] = read_tsv(summaries[0])
    
    # MLST
    mlst_dir = results_dir / 'mlst'
    if mlst_dir.exists():
        for f in mlst_dir.glob('*_mlst.tsv'):
            data['mlst'][f.stem.replace('_mlst', '')] = read_tsv(f)
    
    # SISTR
    sistr_dir = results_dir / 'sistr'
    if sistr_dir.exists():
        for f in sistr_dir.glob('*_sistr.tsv'):
            data['sistr'][f.stem.replace('_sistr', '')] = read_tsv(f)
    
    # MOB-suite
    mob_dir = results_dir / 'mobsuite'
    if mob_dir.exists():
        for d in mob_dir.glob('*_mobsuite'):
            sample = d.name.replace('_mobsuite', '')
            mobfile = d / 'mobtyper_results.txt'
            if mobfile.exists():
                data['mobsuite'][sample] = read_tsv(mobfile)
    
    # Metadata
    meta_dir = results_dir / 'metadata'
    if meta_dir.exists():
        for f in meta_dir.glob('*_metadata.csv'):
            with open(f) as mf:
                data['metadata'][f.stem.replace('_metadata', '')] = list(csv.DictReader(mf))
    
    return data

def create_cross_reference_table(data):
    """Create a summary table linking AMR and phage results per isolate"""
    all_samples = set()
    all_samples.update(data['amr'].keys())
    all_samples.update(data['phage'].keys())
    all_samples.update(data['mlst'].keys())
    
    summary = []
    for sample in sorted(all_samples):
        # AMR info
        amr_genes = data['amr'].get(sample, [])
        amr_count = len(amr_genes)
        amr_classes = set(g.get('Class', '') for g in amr_genes if g.get('Class'))
        
        # Phage info
        phages = data['phage'].get(sample, [])
        phage_count = len(phages)
        
        # MLST info
        mlst = data['mlst'].get(sample, [])
        mlst_st = mlst[0].get('ST', '-') if mlst else '-'
        
        # Plasmid info
        plasmids = data['mobsuite'].get(sample, [])
        plasmid_count = len(plasmids)
        
        summary.append({
            'Sample': sample,
            'AMR_Genes': amr_count,
            'AMR_Classes': ', '.join(sorted(amr_classes)) if amr_classes else '-',
            'Phages': phage_count,
            'Plasmids': plasmid_count,
            'MLST_ST': mlst_st,
            'Status': '⚠️ Both' if (amr_count > 0 and phage_count > 0) else ('AMR only' if amr_count > 0 else ('Phage only' if phage_count > 0 else 'Clean'))
        })
    
    return summary

def analyze_phage_diversity(phage_data):
    """Analyze phage types across all samples"""
    all_phages = []
    for sample, phages in phage_data.items():
        for phage in phages:
            all_phages.append(phage)
    
    types = Counter()
    for phage in all_phages:
        phage_type = phage.get('type', phage.get('scaffold', phage.get('fragment', 'Unknown')))
        types[phage_type] += 1
    
    return types

def create_pie_chart_data(counter_data, title="Distribution"):
    """Convert Counter to format for pie chart"""
    labels = list(counter_data.keys())[:10]  # Top 10
    values = [counter_data[l] for l in labels]
    return json.dumps({'labels': labels, 'values': values, 'title': title})

def table_html(data_list, max_rows=50):
    if not data_list:
        return "<p><em>No data</em></p>"
    
    shown = data_list[:max_rows]
    note = f"<p><em>Showing {len(shown)} of {len(data_list)} rows</em></p>" if len(data_list) > max_rows else ""
    
    headers = list(shown[0].keys())
    html = note + '<table class="data-table"><thead><tr>'
    html += ''.join(f'<th>{h}</th>' for h in headers)
    html += '</tr></thead><tbody>'
    
    for row in shown:
        html += '<tr>' + ''.join(f'<td>{row.get(h, "")}</td>' for h in headers) + '</tr>'
    
    html += '</tbody></table>'
    return html

def generate_html(data, results_dir, output_file):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    all_samples = set()
    for key in ['amr', 'phage', 'mlst', 'sistr', 'mobsuite']:
        all_samples.update(data[key].keys())
    
    # Create cross-reference summary
    cross_ref = create_cross_reference_table(data)
    
    # Analyze phage diversity
    phage_diversity = analyze_phage_diversity(data['phage'])
    phage_chart_data = create_pie_chart_data(phage_diversity, "Phage Type Distribution")
    
    # Count AMR classes
    amr_classes = Counter()
    for sample, amr_list in data['amr'].items():
        for gene in amr_list:
            amr_class = gene.get('Class', gene.get('class', 'Unknown'))
            if amr_class:
                amr_classes[amr_class] += 1
    amr_chart_data = create_pie_chart_data(amr_classes, "AMR Gene Classes")
    
    # Count samples with both AMR and phage
    both_count = sum(1 for s in cross_ref if s['AMR_Genes'] > 0 and s['Phages'] > 0)
    
    html = f'''<!DOCTYPE html>
<html><head>
<title>COMPASS Pipeline Report</title>
<meta charset="UTF-8">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
body {{font-family: Arial, sans-serif; max-width: 1400px; margin: 0 auto; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);}}
.container {{background: white; border-radius: 10px; padding: 30px; box-shadow: 0 10px 40px rgba(0,0,0,0.2);}}
h1 {{color: #2c3e50; border-bottom: 4px solid #3498db; padding-bottom: 15px;}}
h2 {{color: #34495e; margin-top: 40px; border-left: 5px solid #3498db; padding: 10px 15px; background: #ecf0f1; border-radius: 5px;}}
.summary-grid {{display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0;}}
.summary-card {{background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}}
.summary-card h3 {{margin: 0 0 10px 0; font-size: 1.1em; border: none; color: white;}}
.summary-card .number {{font-size: 2.5em; font-weight: bold; margin: 10px 0;}}
.data-table {{width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 0.9em; box-shadow: 0 2px 8px rgba(0,0,0,0.1);}}
.data-table thead tr {{background: #3498db; color: white; text-align: left;}}
.data-table th, .data-table td {{padding: 12px 15px; border: 1px solid #ddd;}}
.data-table tbody tr:nth-of-type(even) {{background: #f8f9fa;}}
.data-table tbody tr:hover {{background: #e3f2fd;}}
.section {{background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #3498db;}}
.chart-container {{max-width: 500px; margin: 20px auto;}}
.chart-grid {{display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 30px; margin: 20px 0;}}
nav {{background: #34495e; padding: 15px; border-radius: 8px; margin-bottom: 30px;}}
nav a {{color: white; text-decoration: none; padding: 8px 15px; margin: 0 5px; border-radius: 5px; display: inline-block;}}
nav a:hover {{background: #3498db;}}
.badge {{display: inline-block; padding: 5px 10px; border-radius: 15px; font-size: 0.85em; font-weight: bold; margin: 2px;}}
.badge-warning {{background: #f39c12; color: white;}}
.badge-info {{background: #3498db; color: white;}}
.badge-success {{background: #2ecc71; color: white;}}
.badge-danger {{background: #e74c3c; color: white;}}
.highlight-both {{background: #fff3cd !important; border-left: 4px solid #f39c12;}}
</style>
</head>
<body>
<div class="container">
<h1>🧬 COMPASS Pipeline Report</h1>
<p><strong>Generated:</strong> {timestamp} | <strong>Samples:</strong> {len(all_samples)}</p>

<nav>
<a href="#overview">Overview</a>
<a href="#cross-ref">Sample Summary</a>
<a href="#amr">AMR</a>
<a href="#phage">Phage</a>
<a href="#typing">Typing</a>
<a href="#plasmids">Plasmids</a>
<a href="#about">About</a>
</nav>

<div id="overview" class="section">
<h2>📊 Overview</h2>
<div class="summary-grid">
<div class="summary-card"><h3>🔬 Samples</h3><div class="number">{len(all_samples)}</div></div>
<div class="summary-card"><h3>🦠 AMR Results</h3><div class="number">{len(data["amr"])}</div></div>
<div class="summary-card"><h3>🧬 Phages</h3><div class="number">{len(data["phage"])}</div></div>
<div class="summary-card"><h3>⚠️ Both AMR+Phage</h3><div class="number">{both_count}</div></div>
<div class="summary-card"><h3>📊 Typed</h3><div class="number">{len(data["mlst"])}</div></div>
</div>

<div class="chart-grid">
<div class="chart-container">
<h3>Phage Type Distribution</h3>
<canvas id="phageChart"></canvas>
</div>

<div class="chart-container">
<h3>AMR Gene Classes</h3>
<canvas id="amrChart"></canvas>
</div>
</div>
</div>

<div id="cross-ref" class="section">
<h2>📋 Sample Summary - AMR & Phage Cross-Reference</h2>
<p><strong>Samples with both AMR genes and phages are highlighted</strong> to identify potential correlations.</p>
{table_html(cross_ref, max_rows=1000)}
</div>

<div id="amr" class="section">
<h2>🦠 Antimicrobial Resistance Details</h2>
'''
    
    for sample, amr_list in sorted(data['amr'].items()):
        count = len(amr_list)
        has_phage = len(data['phage'].get(sample, [])) > 0
        highlight = ' class="highlight-both"' if (count > 0 and has_phage) else ''
        
        html += f'<div{highlight}><h3>{sample} <span class="badge badge-warning">{count} genes</span>'
        if has_phage:
            html += ' <span class="badge badge-info">Has Phages</span>'
        html += '</h3>'
        html += table_html(amr_list) if count > 0 else '<p><em>No resistance genes</em></p>'
        html += '</div>'
    
    html += '</div><div id="phage" class="section"><h2>🧬 Phage Analysis Details</h2>'
    
    for sample, phage_list in sorted(data['phage'].items()):
        count = len(phage_list)
        has_amr = len(data['amr'].get(sample, [])) > 0
        highlight = ' class="highlight-both"' if (count > 0 and has_amr) else ''
        
        html += f'<div{highlight}><h3>{sample} <span class="badge badge-info">{count} phages</span>'
        if has_amr:
            html += ' <span class="badge badge-warning">Has AMR</span>'
        html += '</h3>'
        html += table_html(phage_list) if count > 0 else '<p><em>No phages detected</em></p>'
        html += '</div>'
    
    html += '</div><div id="typing" class="section"><h2>🔬 Strain Typing</h2>'
    
    if data['mlst']:
        html += '<h3>MLST Results</h3>'
        for sample, mlst_list in sorted(data['mlst'].items()):
            html += f'<h4>{sample}</h4>{table_html(mlst_list)}'
    
    if data['sistr']:
        html += '<h3>SISTR Serotyping</h3>'
        for sample, sistr_list in sorted(data['sistr'].items()):
            html += f'<h4>{sample}</h4>{table_html(sistr_list)}'
    
    html += '</div><div id="plasmids" class="section"><h2>🧩 Plasmid Detection</h2>'
    
    for sample, mob_list in sorted(data['mobsuite'].items()):
        count = len(mob_list)
        html += f'<h3>{sample} <span class="badge badge-success">{count} plasmids</span></h3>'
        html += table_html(mob_list) if count > 0 else '<p><em>No plasmids</em></p>'
    
    html += f'''</div>

<div id="about" class="section">
<h2>ℹ️ About This Report</h2>
<p>Self-contained COMPASS pipeline report with cross-reference analysis.</p>
<p><strong>Key Features:</strong></p>
<ul>
<li>Sample summary table showing AMR genes, phages, and plasmids per isolate</li>
<li>Highlighted samples with both AMR and phage content</li>
<li>Interactive pie charts for distribution analysis</li>
<li>All data embedded - no external files needed</li>
</ul>
<p><strong>Results Directory:</strong> {results_dir}</p>
</div>

<script>
const phageData = {phage_chart_data};
const amrData = {amr_chart_data};

new Chart(document.getElementById('phageChart'), {{
    type: 'pie',
    data: {{
        labels: phageData.labels,
        datasets: [{{
            data: phageData.values,
            backgroundColor: ['#3498db','#e74c3c','#2ecc71','#f39c12','#9b59b6','#1abc9c','#34495e','#e67e22','#95a5a6','#d35400']
        }}]
    }},
    options: {{responsive: true, plugins: {{legend: {{position: 'bottom'}}}}}}
}});

new Chart(document.getElementById('amrChart'), {{
    type: 'pie',
    data: {{
        labels: amrData.labels,
        datasets: [{{
            data: amrData.values,
            backgroundColor: ['#e74c3c','#f39c12','#e67e22','#c0392b','#d35400','#f1c40f','#e85d75','#ff6b81','#fd9644','#fa8231']
        }}]
    }},
    options: {{responsive: true, plugins: {{legend: {{position: 'bottom'}}}}}}
}});
</script>
</div>
</body>
</html>'''
    
    with open(output_file, 'w') as f:
        f.write(html)
    return output_file

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate COMPASS report with cross-reference')
    parser.add_argument('results_dir', help='Results directory')
    parser.add_argument('-o', '--output', default='compass_report.html')
    args = parser.parse_args()
    
    print(f"🔍 Scanning: {args.results_dir}")
    data = collect_all_results(args.results_dir)
    
    print(f"📊 Found: {len(data['amr'])} AMR, {len(data['phage'])} Phage, {len(data['mlst'])} MLST")
    
    output = generate_html(data, args.results_dir, args.output)
    size = os.path.getsize(output) / 1024
    print(f"✅ Generated: {output} ({size:.1f} KB)")

if __name__ == '__main__':
    main()
