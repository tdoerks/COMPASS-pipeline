#!/usr/bin/env python3
"""
Generate a standalone HTML report with embedded data from COMPASS pipeline results
"""

import sys
import os
import csv
from pathlib import Path
import argparse
from datetime import datetime

def read_tsv(file_path, max_rows=None):
    """Read TSV file and return as list of dicts"""
    try:
        with open(file_path) as f:
            reader = csv.DictReader(f, delimiter='\t')
            rows = list(reader)
            if max_rows:
                rows = rows[:max_rows]
            return rows
    except Exception as e:
        return []

def read_metadata(results_dir):
    """Read metadata files"""
    metadata = {}
    metadata_dir = Path(results_dir) / 'metadata'

    if metadata_dir.exists():
        for meta_file in metadata_dir.glob('*_metadata.csv'):
            try:
                with open(meta_file) as f:
                    reader = csv.DictReader(f)
                    organism = meta_file.stem.replace('_metadata', '')
                    metadata[organism] = list(reader)
            except:
                pass

    # Also check for filtered samples
    filtered_dir = Path(results_dir) / 'filtered_samples'
    if filtered_dir.exists():
        filtered_csv = filtered_dir / 'filtered_samples.csv'
        if filtered_csv.exists():
            try:
                with open(filtered_csv) as f:
                    reader = csv.DictReader(f)
                    metadata['filtered_samples'] = list(reader)
            except:
                pass

    return metadata

def collect_all_results(results_dir):
    """Collect all results from the pipeline"""
    results_dir = Path(results_dir)
    data = {
        'amr': {},
        'phage_summaries': {},
        'mlst': {},
        'sistr': {},
        'mobsuite': {},
        'busco': {},
        'metadata': {}
    }

    # AMR results
    amr_dir = results_dir / 'amrfinder'
    if amr_dir.exists():
        for amr_file in amr_dir.glob('*_amr.tsv'):
            sample = amr_file.stem.replace('_amr', '')
            data['amr'][sample] = read_tsv(amr_file)

    # VIBRANT summaries
    vibrant_dir = results_dir / 'vibrant'
    if vibrant_dir.exists():
        for sample_dir in vibrant_dir.glob('*_vibrant'):
            sample = sample_dir.name.replace('_vibrant', '')
            summary_files = list(sample_dir.glob('**/VIBRANT_summary_results*.tsv'))
            if summary_files:
                data['phage_summaries'][sample] = read_tsv(summary_files[0])

    # MLST
    mlst_dir = results_dir / 'mlst'
    if mlst_dir.exists():
        for mlst_file in mlst_dir.glob('*_mlst.tsv'):
            sample = mlst_file.stem.replace('_mlst', '')
            data['mlst'][sample] = read_tsv(mlst_file)

    # SISTR
    sistr_dir = results_dir / 'sistr'
    if sistr_dir.exists():
        for sistr_file in sistr_dir.glob('*_sistr.tsv'):
            sample = sistr_file.stem.replace('_sistr', '')
            data['sistr'][sample] = read_tsv(sistr_file)

    # MOB-suite
    mobsuite_dir = results_dir / 'mobsuite'
    if mobsuite_dir.exists():
        for sample_dir in mobsuite_dir.glob('*_mobsuite'):
            sample = sample_dir.name.replace('_mobsuite', '')
            mobtyper = sample_dir / 'mobtyper_results.txt'
            if mobtyper.exists():
                data['mobsuite'][sample] = read_tsv(mobtyper)

    # BUSCO summaries
    busco_dir = results_dir / 'busco'
    if busco_dir.exists():
        for sample_dir in busco_dir.glob('*_busco'):
            sample = sample_dir.name.replace('_busco', '')
            summary_files = list(sample_dir.glob('short_summary*.txt'))
            if summary_files:
                data['busco'][sample] = parse_busco_summary(summary_files[0])

    # Metadata
    data['metadata'] = read_metadata(results_dir)

    return data

def parse_busco_summary(file_path):
    """Parse BUSCO summary text file"""
    try:
        with open(file_path) as f:
            lines = f.readlines()

        summary = {}
        for line in lines:
            line = line.strip()
            if line.startswith('C:'):
                # Parse the summary line: C:98.5%[S:98.0%,D:0.5%],F:0.8%,M:0.7%,n:124
                summary['summary'] = line
            elif 'Complete BUSCOs' in line and '(C)' in line:
                summary['complete'] = line.split('\t')[0].strip()
            elif 'Complete and single-copy' in line:
                summary['single_copy'] = line.split('\t')[0].strip()
            elif 'Complete and duplicated' in line:
                summary['duplicated'] = line.split('\t')[0].strip()
            elif 'Fragmented BUSCOs' in line:
                summary['fragmented'] = line.split('\t')[0].strip()
            elif 'Missing BUSCOs' in line:
                summary['missing'] = line.split('\t')[0].strip()

        return summary
    except:
        return {}

def dict_to_html_table(data_list, max_rows=50):
    """Convert list of dicts to HTML table"""
    if not data_list:
        return "<p><em>No data available</em></p>"

    if len(data_list) > max_rows:
        note = f"<p><em>Showing first {max_rows} of {len(data_list)} rows</em></p>"
        data_list = data_list[:max_rows]
    else:
        note = ""

    headers = list(data_list[0].keys())

    html = note + '<table class="data-table">\n<thead><tr>\n'
    for header in headers:
        html += f'<th>{header}</th>\n'
    html += '</tr></thead>\n<tbody>\n'

    for row in data_list:
        html += '<tr>\n'
        for header in headers:
            value = row.get(header, '')
            html += f'<td>{value}</td>\n'
        html += '</tr>\n'

    html += '</tbody>\n</table>\n'
    return html

def generate_standalone_html(data, results_dir, output_file):
    """Generate self-contained HTML report"""

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Count samples
    all_samples = set()
    all_samples.update(data['amr'].keys())
    all_samples.update(data['phage_summaries'].keys())
    all_samples.update(data['mlst'].keys())
    all_samples.update(data['sistr'].keys())
    all_samples.update(data['mobsuite'].keys())
    all_samples.update(data['busco'].keys())

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>COMPASS Pipeline - Standalone Report</title>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 4px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 30px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 40px;
            border-left: 5px solid #3498db;
            padding-left: 15px;
            background: #ecf0f1;
            padding: 10px 15px;
            border-radius: 5px;
        }}
        h3 {{
            color: #555;
            margin-top: 25px;
            padding-bottom: 5px;
            border-bottom: 2px solid #bdc3c7;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            font-size: 1.1em;
            border: none;
            color: white;
        }}
        .summary-card .number {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 0.9em;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .data-table thead tr {{
            background: #3498db;
            color: white;
            text-align: left;
        }}
        .data-table th,
        .data-table td {{
            padding: 12px 15px;
            border: 1px solid #ddd;
        }}
        .data-table tbody tr:nth-of-type(even) {{
            background: #f8f9fa;
        }}
        .data-table tbody tr:hover {{
            background: #e3f2fd;
        }}
        .section {{
            background: #f8f9fa;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-style: italic;
            margin-bottom: 20px;
        }}
        .sample-section {{
            background: white;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
            border: 1px solid #ddd;
        }}
        .badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: bold;
            margin: 2px;
        }}
        .badge-success {{
            background: #2ecc71;
            color: white;
        }}
        .badge-warning {{
            background: #f39c12;
            color: white;
        }}
        .badge-info {{
            background: #3498db;
            color: white;
        }}
        .metadata-box {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        nav {{
            background: #34495e;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        nav a {{
            color: white;
            text-decoration: none;
            padding: 8px 15px;
            margin: 0 5px;
            border-radius: 5px;
            display: inline-block;
        }}
        nav a:hover {{
            background: #3498db;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧬 COMPASS Pipeline - Standalone Report</h1>
        <div class="timestamp">
            <strong>Results Directory:</strong> {results_dir}<br>
            <strong>Generated:</strong> {timestamp}<br>
            <strong>Total Samples:</strong> {len(all_samples)}
        </div>

        <nav>
            <a href="#summary">Summary</a>
            <a href="#metadata">Metadata</a>
            <a href="#qc">Quality Control</a>
            <a href="#typing">Typing</a>
            <a href="#amr">AMR</a>
            <a href="#phage">Phage</a>
            <a href="#plasmids">Plasmids</a>
        </nav>

        <div id="summary" class="section">
            <h2>📊 Pipeline Summary</h2>
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>🔬 Samples Analyzed</h3>
                    <div class="number">{len(all_samples)}</div>
                </div>
                <div class="summary-card">
                    <h3>🦠 AMR Results</h3>
                    <div class="number">{len(data['amr'])}</div>
                </div>
                <div class="summary-card">
                    <h3>🧬 Phage Analyses</h3>
                    <div class="number">{len(data['phage_summaries'])}</div>
                </div>
                <div class="summary-card">
                    <h3>📊 Typed Samples</h3>
                    <div class="number">{len(data['mlst'])}</div>
                </div>
            </div>
        </div>
"""

    # Metadata section
    if data['metadata']:
        html += '<div id="metadata" class="section"><h2>📋 Sample Metadata</h2>\n'

        for organism, meta_list in data['metadata'].items():
            if meta_list:
                html += f'<h3>{organism.replace("_", " ").title()}</h3>\n'
                html += dict_to_html_table(meta_list, max_rows=100)

        html += '</div>\n'

    # Quality Control section
    if data['busco']:
        html += '<div id="qc" class="section"><h2>✅ Quality Control - Assembly Completeness (BUSCO)</h2>\n'

        for sample, busco_data in sorted(data['busco'].items()):
            html += f'<div class="sample-section"><h3>{sample}</h3>\n'
            if 'summary' in busco_data:
                html += f'<p><strong>{busco_data["summary"]}</strong></p>\n'

                if 'complete' in busco_data:
                    html += f'<p>Complete BUSCOs: {busco_data["complete"]}</p>\n'
                if 'single_copy' in busco_data:
                    html += f'<p>Single-copy: {busco_data["single_copy"]}</p>\n'
                if 'duplicated' in busco_data:
                    html += f'<p>Duplicated: {busco_data["duplicated"]}</p>\n'
                if 'fragmented' in busco_data:
                    html += f'<p>Fragmented: {busco_data["fragmented"]}</p>\n'
                if 'missing' in busco_data:
                    html += f'<p>Missing: {busco_data["missing"]}</p>\n'
            html += '</div>\n'

        html += '</div>\n'

    # Typing section
    if data['mlst'] or data['sistr']:
        html += '<div id="typing" class="section"><h2>🔬 Strain Typing</h2>\n'

        if data['mlst']:
            html += '<h3>MLST Results</h3>\n'
            for sample, mlst_data in sorted(data['mlst'].items()):
                html += f'<div class="sample-section"><h4>{sample}</h4>\n'
                html += dict_to_html_table(mlst_data)
                html += '</div>\n'

        if data['sistr']:
            html += '<h3>SISTR Serotyping (Salmonella)</h3>\n'
            for sample, sistr_data in sorted(data['sistr'].items()):
                html += f'<div class="sample-section"><h4>{sample}</h4>\n'
                html += dict_to_html_table(sistr_data)
                html += '</div>\n'

        html += '</div>\n'

    # AMR section
    if data['amr']:
        html += '<div id="amr" class="section"><h2>🦠 Antimicrobial Resistance (AMRFinder+)</h2>\n'

        for sample, amr_data in sorted(data['amr'].items()):
            gene_count = len(amr_data)
            html += f'<div class="sample-section">\n'
            html += f'<h3>{sample} <span class="badge badge-warning">{gene_count} genes</span></h3>\n'

            if gene_count > 0:
                html += dict_to_html_table(amr_data)
            else:
                html += '<p><em>No resistance genes detected</em></p>\n'

            html += '</div>\n'

        html += '</div>\n'

    # Phage section
    if data['phage_summaries']:
        html += '<div id="phage" class="section"><h2>🧬 Phage Analysis (VIBRANT)</h2>\n'

        for sample, phage_data in sorted(data['phage_summaries'].items()):
            phage_count = len(phage_data)
            html += f'<div class="sample-section">\n'
            html += f'<h3>{sample} <span class="badge badge-info">{phage_count} phages</span></h3>\n'

            if phage_count > 0:
                html += dict_to_html_table(phage_data)
            else:
                html += '<p><em>No phages detected</em></p>\n'

            html += '</div>\n'

        html += '</div>\n'

    # Plasmids section
    if data['mobsuite']:
        html += '<div id="plasmids" class="section"><h2>🧩 Plasmid Detection (MOB-suite)</h2>\n'

        for sample, mob_data in sorted(data['mobsuite'].items()):
            plasmid_count = len(mob_data)
            html += f'<div class="sample-section">\n'
            html += f'<h3>{sample} <span class="badge badge-success">{plasmid_count} plasmids</span></h3>\n'

            if plasmid_count > 0:
                html += dict_to_html_table(mob_data)
            else:
                html += '<p><em>No plasmids detected</em></p>\n'

            html += '</div>\n'

        html += '</div>\n'

    html += """
        <div class="section">
            <h2>ℹ️ About This Report</h2>
            <p>This is a self-contained, standalone HTML report generated from the COMPASS pipeline.</p>
            <p><strong>All data is embedded in this file</strong> - you can share it without needing access to the results directory.</p>
            <p>For the complete analysis files and raw data, refer to the original results directory.</p>
        </div>
    </div>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html)

    return output_file

def main():
    parser = argparse.ArgumentParser(description='Generate standalone COMPASS report with embedded data')
    parser.add_argument('results_dir', help='Path to results directory')
    parser.add_argument('-o', '--output', default='compass_standalone_report.html', help='Output HTML file')

    args = parser.parse_args()

    if not os.path.exists(args.results_dir):
        print(f"❌ Error: Results directory not found: {args.results_dir}")
        sys.exit(1)

    print(f"🔍 Collecting data from: {args.results_dir}")
    data = collect_all_results(args.results_dir)

    print(f"📊 Found:")
    print(f"  - {len(data['amr'])} AMR results")
    print(f"  - {len(data['phage_summaries'])} Phage analyses")
    print(f"  - {len(data['mlst'])} MLST results")
    print(f"  - {len(data['sistr'])} SISTR results")
    print(f"  - {len(data['mobsuite'])} Plasmid detections")
    print(f"  - {len(data['busco'])} BUSCO QC results")

    print(f"\n📝 Generating standalone report...")
    output_file = generate_standalone_html(data, args.results_dir, args.output)

    file_size = os.path.getsize(output_file) / 1024  # KB
    print(f"\n✅ Generated: {output_file} ({file_size:.1f} KB)")
    print(f"✨ This file contains all data and can be viewed offline!")

if __name__ == '__main__':
    main()
