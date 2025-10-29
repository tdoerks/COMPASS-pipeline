#!/usr/bin/env python3
"""
Quick Preview Report Generator for COMPASS Pipeline
Generates a simplified HTML report from partial results
"""

import os
import sys
import glob
from collections import defaultdict, Counter
from pathlib import Path

def count_lines(file_path):
    """Count non-header lines in a file"""
    try:
        with open(file_path) as f:
            lines = f.readlines()
            # Skip header and empty lines
            return len([l for l in lines[1:] if l.strip()])
    except:
        return 0

def parse_amrfinder(results_dir):
    """Parse AMRFinder results"""
    amr_dir = os.path.join(results_dir, "amrfinder")
    if not os.path.exists(amr_dir):
        return {}

    amr_data = {}
    gene_counts = Counter()
    class_counts = Counter()

    for file in glob.glob(f"{amr_dir}/*_amrfinder.tsv"):
        sample = os.path.basename(file).replace("_amrfinder.tsv", "")
        gene_count = count_lines(file)
        amr_data[sample] = gene_count

        # Parse gene details
        try:
            with open(file) as f:
                lines = f.readlines()[1:]  # Skip header
                for line in lines:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) > 5:
                            gene = parts[5]  # Gene symbol
                            gene_counts[gene] += 1
                            if len(parts) > 10:
                                gene_class = parts[10]  # Class
                                if gene_class:
                                    class_counts[gene_class] += 1
        except:
            pass

    return {
        'samples': amr_data,
        'top_genes': gene_counts.most_common(15),
        'top_classes': class_counts.most_common(10),
        'total_samples': len(amr_data),
        'total_genes': sum(amr_data.values())
    }

def parse_abricate(results_dir):
    """Parse ABRicate results"""
    abr_dir = os.path.join(results_dir, "abricate")
    if not os.path.exists(abr_dir):
        return {}

    db_data = {}

    for db in ['ncbi', 'card', 'resfinder', 'argannot']:
        db_path = os.path.join(abr_dir, db)
        if os.path.exists(db_path):
            files = glob.glob(f"{db_path}/*.tsv")
            gene_counts = Counter()
            total_hits = 0

            for file in files:
                hits = count_lines(file)
                total_hits += hits

                # Parse genes
                try:
                    with open(file) as f:
                        lines = f.readlines()[1:]
                        for line in lines:
                            if line.strip():
                                parts = line.split('\t')
                                if len(parts) > 4:
                                    gene = parts[4]  # GENE column
                                    gene_counts[gene] += 1
                except:
                    pass

            db_data[db] = {
                'samples': len(files),
                'total_hits': total_hits,
                'top_genes': gene_counts.most_common(10)
            }

    return db_data

def parse_vibrant(results_dir):
    """Parse VIBRANT phage results"""
    vibrant_dir = os.path.join(results_dir, "vibrant")
    if not os.path.exists(vibrant_dir):
        return {}

    phage_data = {}
    total_phages = 0

    for sample_dir in glob.glob(f"{vibrant_dir}/SRR*"):
        sample = os.path.basename(sample_dir)

        # Count phage sequences
        phage_files = glob.glob(f"{sample_dir}/VIBRANT_phages_*/*.fasta")
        phage_count = 0
        for pf in phage_files:
            phage_count += count_lines(pf) // 2  # FASTA has 2 lines per sequence

        if phage_count > 0:
            phage_data[sample] = phage_count
            total_phages += phage_count

    return {
        'samples_with_phages': len(phage_data),
        'total_phages': total_phages,
        'samples': phage_data
    }

def generate_html_report(results_dir, output_file):
    """Generate HTML preview report"""

    print(f"Parsing results from: {results_dir}")

    # Parse data
    amr_data = parse_amrfinder(results_dir)
    abr_data = parse_abricate(results_dir)
    phage_data = parse_vibrant(results_dir)

    # Get assembly count
    assembly_dir = os.path.join(results_dir, "assemblies")
    assembly_count = len(glob.glob(f"{assembly_dir}/*.fasta")) if os.path.exists(assembly_dir) else 0

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>COMPASS Pipeline - Quick Preview Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 8px;
        }}
        h3 {{
            color: #7f8c8d;
            margin-top: 20px;
        }}
        .summary-box {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }}
        .stat {{
            display: inline-block;
            margin: 10px 20px 10px 0;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
        }}
        .stat-label {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th {{
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ecf0f1;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .note {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
        }}
        .db-section {{
            margin: 20px 0;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧬 COMPASS Pipeline - Quick Preview Report</h1>

        <div class="note">
            <strong>⚠️ Preview Report:</strong> This is a preliminary report generated from partial results.
            The final report will be more comprehensive once the pipeline completes.
        </div>

        <div class="summary-box">
            <h2>📊 Overview</h2>
            <div class="stat">
                <div class="stat-value">{assembly_count}</div>
                <div class="stat-label">Assemblies</div>
            </div>
            <div class="stat">
                <div class="stat-value">{amr_data.get('total_samples', 0)}</div>
                <div class="stat-label">AMR Analyzed</div>
            </div>
            <div class="stat">
                <div class="stat-value">{amr_data.get('total_genes', 0)}</div>
                <div class="stat-label">AMR Genes Found</div>
            </div>
            <div class="stat">
                <div class="stat-value">{phage_data.get('total_phages', 0)}</div>
                <div class="stat-label">Phages Detected</div>
            </div>
        </div>
"""

    # AMRFinder section
    if amr_data:
        html += f"""
        <h2>💊 AMR Analysis (AMRFinder+)</h2>

        <h3>Top Resistance Genes</h3>
        <table>
            <tr>
                <th>Gene</th>
                <th>Sample Count</th>
            </tr>
"""
        for gene, count in amr_data.get('top_genes', []):
            html += f"            <tr><td>{gene}</td><td>{count}</td></tr>\n"

        html += """        </table>

        <h3>Resistance Classes</h3>
        <table>
            <tr>
                <th>Class</th>
                <th>Occurrences</th>
            </tr>
"""
        for cls, count in amr_data.get('top_classes', []):
            html += f"            <tr><td>{cls}</td><td>{count}</td></tr>\n"

        html += "        </table>\n"

    # ABRicate section
    if abr_data:
        html += """
        <h2>🔬 ABRicate Multi-Database Screening</h2>
"""
        for db, data in abr_data.items():
            html += f"""
        <div class="db-section">
            <h3>{db.upper()} Database</h3>
            <p><strong>Samples:</strong> {data['samples']} | <strong>Total Hits:</strong> {data['total_hits']}</p>
            <table>
                <tr>
                    <th>Gene</th>
                    <th>Occurrences</th>
                </tr>
"""
            for gene, count in data.get('top_genes', []):
                html += f"                <tr><td>{gene}</td><td>{count}</td></tr>\n"

            html += "            </table>\n        </div>\n"

    # Phage section
    if phage_data:
        html += f"""
        <h2>🦠 Phage/Prophage Detection (VIBRANT)</h2>

        <div class="summary-box">
            <div class="stat">
                <div class="stat-value">{phage_data['samples_with_phages']}</div>
                <div class="stat-label">Samples with Phages</div>
            </div>
            <div class="stat">
                <div class="stat-value">{phage_data['total_phages']}</div>
                <div class="stat-label">Total Phage Sequences</div>
            </div>
        </div>

        <h3>Top Samples by Phage Count</h3>
        <table>
            <tr>
                <th>Sample</th>
                <th>Phage Count</th>
            </tr>
"""
        sorted_phages = sorted(phage_data['samples'].items(), key=lambda x: x[1], reverse=True)[:20]
        for sample, count in sorted_phages:
            html += f"            <tr><td>{sample}</td><td>{count}</td></tr>\n"

        html += "        </table>\n"

    # Footer
    html += """
        <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #ecf0f1; color: #7f8c8d; font-size: 0.9em;">
            <p><strong>Generated:</strong> """ + f"{results_dir}" + """</p>
            <p>This preview report shows currently available results. Final report will include additional analyses.</p>
        </div>
    </div>
</body>
</html>
"""

    # Write file
    with open(output_file, 'w') as f:
        f.write(html)

    print(f"✅ Preview report generated: {output_file}")
    print(f"\nSummary:")
    print(f"  - Assemblies: {assembly_count}")
    print(f"  - AMR genes: {amr_data.get('total_genes', 0)}")
    print(f"  - Phages detected: {phage_data.get('total_phages', 0)}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: ./generate_preview_report.py <results_dir> <output.html>")
        print("Example: ./generate_preview_report.py results_kansas_2025 preview_report.html")
        sys.exit(1)

    results_dir = sys.argv[1]
    output_file = sys.argv[2]

    if not os.path.exists(results_dir):
        print(f"Error: Results directory not found: {results_dir}")
        sys.exit(1)

    generate_html_report(results_dir, output_file)
