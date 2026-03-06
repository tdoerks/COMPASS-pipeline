#!/usr/bin/env python3
"""
Quick Results Viewer for COMPASS Pipeline
Generates a simple HTML summary of available results
"""

import sys
import os
from pathlib import Path
import argparse

def find_results(results_dir):
    """Scan results directory and categorize available files"""
    results_dir = Path(results_dir)

    results = {
        'amr': [],
        'phage': [],
        'typing': [],
        'qc': [],
        'plasmids': [],
        'reports': []
    }

    # AMR results
    amr_dir = results_dir / 'amrfinder'
    if amr_dir.exists():
        results['amr'] = sorted(amr_dir.glob('*_amr.tsv'))

    # Phage results
    vibrant_dir = results_dir / 'vibrant'
    if vibrant_dir.exists():
        results['phage'] = sorted(vibrant_dir.glob('*_vibrant'))

    # Typing results
    mlst_dir = results_dir / 'mlst'
    if mlst_dir.exists():
        results['typing'].extend(sorted(mlst_dir.glob('*_mlst.tsv')))

    sistr_dir = results_dir / 'sistr'
    if sistr_dir.exists():
        results['typing'].extend(sorted(sistr_dir.glob('*_sistr.tsv')))

    # QC results
    fastqc_dir = results_dir / 'fastqc'
    if fastqc_dir.exists():
        results['qc'].extend(sorted(fastqc_dir.glob('*.html')))

    busco_dir = results_dir / 'busco'
    if busco_dir.exists():
        results['qc'].extend(sorted(busco_dir.glob('*/short_summary*.txt')))

    # Plasmid results
    mobsuite_dir = results_dir / 'mobsuite'
    if mobsuite_dir.exists():
        results['plasmids'] = sorted(mobsuite_dir.glob('*/mobtyper_results.txt'))

    # Reports
    if (results_dir / 'multiqc').exists():
        multiqc = results_dir / 'multiqc' / 'multiqc_report.html'
        if multiqc.exists():
            results['reports'].append(multiqc)

    if (results_dir / 'summary').exists():
        summary = results_dir / 'summary' / 'phage_analysis_report.html'
        if summary.exists():
            results['reports'].append(summary)

    return results

def read_tsv_preview(file_path, max_rows=10):
    """Read first few lines of a TSV file"""
    try:
        with open(file_path) as f:
            lines = [line.strip() for line in f.readlines()[:max_rows+1]]
        return lines
    except:
        return []

def generate_html(results, results_dir, output_file):
    """Generate HTML summary page"""

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>COMPASS Pipeline Results - Quick View</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 20px auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}
        .section {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .file-list {{
            list-style: none;
            padding: 0;
        }}
        .file-list li {{
            padding: 8px;
            margin: 5px 0;
            background: #ecf0f1;
            border-radius: 3px;
        }}
        .file-list a {{
            color: #2980b9;
            text-decoration: none;
            font-weight: bold;
        }}
        .file-list a:hover {{
            color: #3498db;
            text-decoration: underline;
        }}
        .count {{
            background: #3498db;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.9em;
            margin-left: 10px;
        }}
        .summary-box {{
            background: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 10px 0;
        }}
        .preview {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            padding: 10px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 0.9em;
            overflow-x: auto;
            max-height: 300px;
            overflow-y: auto;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 0.9em;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <h1>🧬 COMPASS Pipeline Results - Quick View</h1>
    <div class="timestamp">Results directory: {results_dir}<br>Generated: {Path(output_file).name}</div>

    <div class="section">
        <h2>📊 Summary</h2>
        <div class="summary-box">
            <strong>AMR Results:</strong> {len(results['amr'])} samples<br>
            <strong>Phage Analysis:</strong> {len(results['phage'])} samples<br>
            <strong>Typing Results:</strong> {len(results['typing'])} files<br>
            <strong>QC Reports:</strong> {len(results['qc'])} files<br>
            <strong>Plasmid Detection:</strong> {len(results['plasmids'])} samples<br>
            <strong>Integrated Reports:</strong> {len(results['reports'])} files
        </div>
    </div>
"""

    # Reports section
    if results['reports']:
        html += """
    <div class="section">
        <h2>📑 Integrated Reports <span class="count">{}</span></h2>
        <ul class="file-list">
""".format(len(results['reports']))
        for report in results['reports']:
            rel_path = report.relative_to(results_dir)
            html += f'            <li><a href="{rel_path}" target="_blank">📄 {report.name}</a> - {report.parent.name}</li>\n'
        html += "        </ul>\n    </div>\n"

    # AMR section
    if results['amr']:
        html += """
    <div class="section">
        <h2>🦠 Antimicrobial Resistance (AMRFinder+) <span class="count">{}</span></h2>
        <ul class="file-list">
""".format(len(results['amr']))
        for amr_file in results['amr']:
            rel_path = amr_file.relative_to(results_dir)
            sample_name = amr_file.stem.replace('_amr', '')
            html += f'            <li><a href="{rel_path}" target="_blank">🔬 {sample_name}</a></li>\n'
        html += "        </ul>\n    </div>\n"

    # Phage section
    if results['phage']:
        html += """
    <div class="section">
        <h2>🦠 Phage Analysis (VIBRANT) <span class="count">{}</span></h2>
        <ul class="file-list">
""".format(len(results['phage']))
        for phage_dir in results['phage']:
            rel_path = phage_dir.relative_to(results_dir)
            sample_name = phage_dir.name.replace('_vibrant', '')

            # Look for summary files
            summary_files = list(phage_dir.glob('**/VIBRANT_summary*.tsv'))
            if summary_files:
                for sf in summary_files:
                    sf_rel = sf.relative_to(results_dir)
                    html += f'            <li><a href="{sf_rel}" target="_blank">🧬 {sample_name} - Summary</a></li>\n'
            else:
                html += f'            <li>🧬 {sample_name} (directory)</li>\n'
        html += "        </ul>\n    </div>\n"

    # Typing section
    if results['typing']:
        html += """
    <div class="section">
        <h2>🔬 Strain Typing (MLST/SISTR) <span class="count">{}</span></h2>
        <ul class="file-list">
""".format(len(results['typing']))
        for typing_file in results['typing']:
            rel_path = typing_file.relative_to(results_dir)
            tool = 'MLST' if 'mlst' in typing_file.name else 'SISTR'
            sample_name = typing_file.stem.replace('_mlst', '').replace('_sistr', '')
            html += f'            <li><a href="{rel_path}" target="_blank">📊 {sample_name} ({tool})</a></li>\n'
        html += "        </ul>\n    </div>\n"

    # QC section
    if results['qc']:
        html += """
    <div class="section">
        <h2>✅ Quality Control <span class="count">{}</span></h2>
        <ul class="file-list">
""".format(len(results['qc']))
        for qc_file in results['qc']:
            rel_path = qc_file.relative_to(results_dir)
            if qc_file.suffix == '.html':
                html += f'            <li><a href="{rel_path}" target="_blank">📈 {qc_file.name}</a></li>\n'
            else:
                html += f'            <li><a href="{rel_path}" target="_blank">📝 {qc_file.name}</a></li>\n'
        html += "        </ul>\n    </div>\n"

    # Plasmids section
    if results['plasmids']:
        html += """
    <div class="section">
        <h2>🧩 Plasmid Detection (MOB-suite) <span class="count">{}</span></h2>
        <ul class="file-list">
""".format(len(results['plasmids']))
        for plasmid_file in results['plasmids']:
            rel_path = plasmid_file.relative_to(results_dir)
            sample_name = plasmid_file.parent.name.replace('_mobsuite', '')
            html += f'            <li><a href="{rel_path}" target="_blank">🧬 {sample_name}</a></li>\n'
        html += "        </ul>\n    </div>\n"

    html += """
    <div class="section">
        <h2>ℹ️ About This Report</h2>
        <p>This is a quick results viewer generated from the COMPASS pipeline output directory.</p>
        <p>Click on any file link to view the raw data. For integrated analysis, check the Reports section above.</p>
        <p><em>Note: Some processes may still be running. Refresh this page to see updated results.</em></p>
    </div>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"✅ Generated: {output_file}")
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Generate quick HTML viewer for COMPASS results')
    parser.add_argument('results_dir', help='Path to results directory')
    parser.add_argument('-o', '--output', default='results_quick_view.html', help='Output HTML file')

    args = parser.parse_args()

    if not os.path.exists(args.results_dir):
        print(f"❌ Error: Results directory not found: {args.results_dir}")
        sys.exit(1)

    print(f"🔍 Scanning results directory: {args.results_dir}")
    results = find_results(args.results_dir)

    print(f"📊 Found:")
    print(f"  - {len(results['amr'])} AMR results")
    print(f"  - {len(results['phage'])} Phage analyses")
    print(f"  - {len(results['typing'])} Typing results")
    print(f"  - {len(results['qc'])} QC files")
    print(f"  - {len(results['plasmids'])} Plasmid detections")
    print(f"  - {len(results['reports'])} Integrated reports")

    output_file = generate_html(results, args.results_dir, args.output)
    print(f"\n✨ Open in browser: file://{os.path.abspath(output_file)}")

if __name__ == '__main__':
    main()
