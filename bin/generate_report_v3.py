#!/usr/bin/env python3
"""
Enhanced COMPASS Pipeline Report with Cross-Reference Analysis
"""

import sys, os, csv, json
from pathlib import Path
from datetime import datetime
from collections import Counter

# Try to import pandas for metadata processing
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

def read_tsv(file_path, max_rows=None):
    try:
        with open(file_path) as f:
            reader = csv.DictReader(f, delimiter='\t')
            rows = list(reader)
            return rows[:max_rows] if max_rows else rows
    except:
        return []

def load_prophage_metadata(metadata_file):
    """Load prophage metadata from Excel file and create lookup dictionary."""
    if not PANDAS_AVAILABLE:
        print("Warning: pandas not available, metadata enrichment disabled")
        return None

    if not metadata_file or not Path(metadata_file).exists():
        print(f"Warning: Metadata file not found: {metadata_file}")
        return None

    try:
        print(f"Loading prophage metadata from {metadata_file}...")
        # Read Table 1 (prophage metadata)
        phage_df = pd.read_excel(metadata_file, sheet_name='Table 1', header=0)

        # Replace 'NA' strings with actual NaN
        phage_df = phage_df.replace('NA', pd.NA)

        # Create lookup dictionary keyed by contig_id and file_name
        metadata_dict = {}

        for _, row in phage_df.iterrows():
            contig_id = str(row.get('contig_id', '')).strip()
            file_name = str(row.get('file_name', '')).strip()

            # Create metadata entry
            entry = {
                'file_name': file_name,
                'contig_id': contig_id,
                'host_domain': row.get('host_domain', ''),
                'host_phylum': row.get('phylum', ''),
                'host_class': row.get('class', ''),
                'host_order': row.get('order', ''),
                'host_family': row.get('family', ''),
                'host_genus': row.get('genus', ''),
                'host_species': row.get('species', ''),
                'environment': row.get('environment', ''),
                'isolation_source': row.get('ncbi_isolation_source', ''),
                'checkv_quality': row.get('checkv_quality', ''),
                'completeness': row.get('completeness', ''),
                'viral_genes': row.get('viral_genes', ''),
                'host_genes': row.get('host_genes', ''),
                'lineage': row.get('lineage_genomad', ''),
                'latitude': row.get('latitude', ''),
                'longitude': row.get('longitude', ''),
                'country': row.get('ncbi_country', '')
            }

            # Index by both contig_id and file_name for flexible matching
            if contig_id:
                metadata_dict[contig_id] = entry
            if file_name:
                metadata_dict[file_name] = entry

        print(f"Loaded metadata for {len(metadata_dict)} prophage entries")
        return metadata_dict

    except Exception as e:
        print(f"Warning: Could not load metadata: {e}")
        return None

def enrich_diamond_with_metadata(diamond_data, metadata_dict):
    """Add metadata information to DIAMOND results."""
    if not metadata_dict:
        return diamond_data

    enriched = {}
    for sample, hits in diamond_data.items():
        enriched_hits = []
        for hit in hits:
            # Get the subject (matched prophage ID)
            subject = hit.get('subject', hit.get('sseqid', ''))

            # Look up metadata - try multiple variations of the subject ID
            meta = None
            if subject:
                # Try exact match
                meta = metadata_dict.get(subject)

                # Try extracting just the accession (e.g., "CP017873" from "195.SAMN05942178.CP017873")
                if not meta and '.' in subject:
                    parts = subject.split('.')
                    for part in parts:
                        meta = metadata_dict.get(part)
                        if meta:
                            break

            # Add metadata fields to the hit
            if meta:
                hit['meta_host_genus'] = meta.get('host_genus', '')
                hit['meta_host_species'] = meta.get('host_species', '')
                hit['meta_environment'] = meta.get('environment', '')
                hit['meta_quality'] = meta.get('checkv_quality', '')
                hit['meta_completeness'] = meta.get('completeness', '')
                hit['meta_lineage'] = meta.get('lineage', '')
                hit['meta_matched'] = 'Yes'
            else:
                hit['meta_matched'] = 'No'

            enriched_hits.append(hit)

        enriched[sample] = enriched_hits

    return enriched

def collect_all_results(results_dir, prophage_metadata=None):
    results_dir = Path(results_dir)
    data = {'amr': {}, 'phage': {}, 'diamond': {}, 'mlst': {}, 'sistr': {}, 'mobsuite': {}, 'busco': {}, 'metadata': {}, 'quast': {}, 'abricate': {}, 'abricate_summary': None, 'prophage_metadata': None}

    # Load prophage metadata if provided
    metadata_dict = None
    if prophage_metadata:
        metadata_dict = load_prophage_metadata(prophage_metadata)
        data['prophage_metadata'] = metadata_dict

    # AMR
    amr_dir = results_dir / 'amrfinder'
    if amr_dir.exists():
        for f in amr_dir.glob('*_amr.tsv'):
            data['amr'][f.stem.replace('_amr', '')] = read_tsv(f)

    # ABRicate (multi-database AMR screening)
    abricate_dir = results_dir / 'abricate'
    if abricate_dir.exists():
        # Collect per-sample, per-database results
        for f in abricate_dir.glob('*_*.tsv'):
            if f.name != 'abricate_summary.tsv':
                # Parse filename: {sample}_{database}.tsv
                parts = f.stem.rsplit('_', 1)
                if len(parts) == 2:
                    sample, database = parts
                    if sample not in data['abricate']:
                        data['abricate'][sample] = {}
                    data['abricate'][sample][database] = read_tsv(f)

        # Collect summary matrix
        summary_file = abricate_dir / 'abricate_summary.tsv'
        if summary_file.exists():
            data['abricate_summary'] = read_tsv(summary_file)

    # Phage
    vibrant_dir = results_dir / 'vibrant'
    if vibrant_dir.exists():
        for d in vibrant_dir.glob('*_vibrant'):
            sample = d.name.replace('_vibrant', '')
            summaries = list(d.glob('**/VIBRANT_summary_results*.tsv'))
            if summaries:
                data['phage'][sample] = read_tsv(summaries[0])

    # DIAMOND prophage identification
    diamond_dir = results_dir / 'diamond_prophage'
    if diamond_dir.exists():
        for f in diamond_dir.glob('*_diamond_results.tsv'):
            sample = f.stem.replace('_diamond_results', '')
            # DIAMOND BLAST tabular format (outfmt 6)
            # Columns: qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore
            diamond_hits = read_tsv(f)
            if diamond_hits and diamond_hits[0]:
                # Add column names for DIAMOND output if they don't exist
                if 'qseqid' not in diamond_hits[0]:
                    for hit in diamond_hits:
                        if len(hit) >= 12:
                            keys = list(hit.keys())[:12]
                            hit_dict = dict(zip(
                                ['query', 'subject', 'pident', 'length', 'mismatch', 'gapopen',
                                 'qstart', 'qend', 'sstart', 'send', 'evalue', 'bitscore'],
                                [hit[k] for k in keys]
                            ))
                            diamond_hits[diamond_hits.index(hit)] = hit_dict
            data['diamond'][sample] = diamond_hits

    # Enrich DIAMOND results with metadata if available
    if metadata_dict and data['diamond']:
        print(f"Enriching DIAMOND results with prophage metadata...")
        data['diamond'] = enrich_diamond_with_metadata(data['diamond'], metadata_dict)

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

    # QUAST assembly quality
    quast_dir = results_dir / 'quast'
    if quast_dir.exists():
        for d in quast_dir.glob('*_quast'):
            sample = d.name.replace('_quast', '')
            report_file = d / 'report.tsv'
            if report_file.exists():
                quast_data = read_tsv(report_file)
                if quast_data:
                    data['quast'][sample] = quast_data[0]  # QUAST has single row per assembly

    return data

def create_assembly_quality_table(quast_data):
    """Create assembly quality summary table from QUAST results"""
    if not quast_data:
        return []

    summary = []
    for sample in sorted(quast_data.keys()):
        q = quast_data[sample]
        summary.append({
            'Sample': sample,
            'Total Length (bp)': q.get('Total length', q.get('Total length (>= 0 bp)', '-')),
            '# Contigs': q.get('# contigs', q.get('# contigs (>= 0 bp)', '-')),
            'Largest Contig (bp)': q.get('Largest contig', '-'),
            'N50 (bp)': q.get('N50', '-'),
            'L50': q.get('L50', '-'),
            'GC (%)': q.get('GC (%)', '-'),
        })

    return summary

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

def analyze_phage_diversity(diamond_data):
    """Analyze phage diversity using DIAMOND identifications with metadata enrichment"""
    phage_ids = Counter()

    for sample, diamond_hits in diamond_data.items():
        for hit in diamond_hits:
            # Priority 1: Use phage lineage from metadata (best identification)
            lineage = hit.get('meta_lineage', '')
            if lineage and lineage != 'NA' and str(lineage).strip():
                # Extract phage family from lineage (e.g., "Caudoviricetes;Siphoviridae" -> "Siphoviridae")
                lineage_parts = str(lineage).split(';')
                phage_name = lineage_parts[-1] if lineage_parts else lineage
                phage_ids[phage_name.strip()] += 1
                continue

            # Priority 2: Use host genus (e.g., "Salmonella prophage")
            host_genus = hit.get('meta_host_genus', '')
            if host_genus and host_genus != 'NA' and str(host_genus).strip():
                phage_ids[f"{host_genus} prophage"] += 1
                continue

            # Priority 3: Fall back to subject ID
            subject = hit.get('subject', hit.get('sseqid', 'Unknown'))
            if subject and subject != 'Unknown':
                # Clean up the subject ID to make it more readable
                if '.' in subject and subject.count('.') >= 2:
                    # Format like "195.SAMN05942178.CP017873" -> "CP017873"
                    parts = subject.split('.')
                    subject = parts[-1] if parts[-1] else subject

                phage_ids[subject] += 1

    return phage_ids if phage_ids else Counter({'No DIAMOND matches': 1})

def analyze_mlst_distribution(mlst_data):
    """Analyze MLST sequence type distribution across samples"""
    st_counts = Counter()

    for sample, mlst_results in mlst_data.items():
        if mlst_results:
            # Get ST from first result
            st = mlst_results[0].get('ST', mlst_results[0].get('st', 'Unknown'))
            if st and st != '-' and st != 'Unknown':
                st_counts[f"ST-{st}"] += 1
            else:
                st_counts['Unknown ST'] += 1

    return st_counts if st_counts else Counter({'No MLST data': 1})

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

    # Create assembly quality summary
    assembly_qc = create_assembly_quality_table(data['quast'])

    # Analyze phage diversity using DIAMOND identifications
    phage_diversity = analyze_phage_diversity(data['diamond'])
    phage_chart_data = create_pie_chart_data(phage_diversity, "Phage Identification Distribution")
    
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
<a href="#assembly-qc">Assembly QC</a>
<a href="#cross-ref">Sample Summary</a>
<a href="#amr">AMR (AMRFinder)</a>
<a href="#abricate">AMR (ABRicate)</a>
<a href="#phage">Phage Detection</a>
<a href="#phage-id">Phage ID</a>
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
<h3>Phage Identification Distribution</h3>
<p style="font-size: 0.9em; color: #7f8c8d;"><em>Based on DIAMOND prophage database matches</em></p>
<canvas id="phageChart"></canvas>
</div>

<div class="chart-container">
<h3>AMR Gene Classes</h3>
<canvas id="amrChart"></canvas>
</div>
</div>
</div>

<div id="assembly-qc" class="section">
<h2>🔬 Assembly Quality Metrics</h2>
<p>Summary of assembly statistics from QUAST. Key metrics to assess assembly quality:</p>
<ul>
<li><strong>N50:</strong> 50% of the assembly is in contigs this size or larger (higher is better)</li>
<li><strong>L50:</strong> Number of contigs comprising 50% of the assembly (lower is better)</li>
<li><strong># Contigs:</strong> Fewer contigs indicates a more contiguous assembly</li>
</ul>
{table_html(assembly_qc, max_rows=1000)}
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

    html += '</div><div id="abricate" class="section"><h2>🦠 AMR Multi-Database Screening (ABRicate)</h2>'
    html += '<p><em>Compares assemblies against multiple resistance databases: NCBI, CARD, ResFinder, ARG-ANNOT</em></p>'

    if data['abricate']:
        for sample in sorted(data['abricate'].keys()):
            databases = data['abricate'][sample]
            total_hits = sum(len(hits) for hits in databases.values())
            has_phage = len(data['phage'].get(sample, [])) > 0
            highlight = ' class="highlight-both"' if (total_hits > 0 and has_phage) else ''

            html += f'<div{highlight}><h3>{sample} <span class="badge badge-warning">{total_hits} total hits</span>'
            if has_phage:
                html += ' <span class="badge badge-info">Has Phages</span>'
            html += '</h3>'

            for db_name in sorted(databases.keys()):
                db_hits = databases[db_name]
                if db_hits:
                    html += f'<h4>{db_name.upper()} Database <span class="badge badge-success">{len(db_hits)} hits</span></h4>'
                    html += table_html(db_hits, max_rows=100)
                else:
                    html += f'<h4>{db_name.upper()} Database</h4><p><em>No hits</em></p>'

            html += '</div>'
    else:
        html += '<p><em>No ABRicate results available</em></p>'

    html += '</div><div id="phage" class="section"><h2>🧬 Phage Detection (VIBRANT)</h2>'
    html += '<p><em>Shows which contigs contain phage sequences and their characteristics.</em></p>'

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

    html += '</div><div id="phage-id" class="section"><h2>🔍 Phage Identification (DIAMOND)</h2>'
    html += '<p><em>Identifies which known phages your sequences match to (like AMRFinder for AMR genes).</em></p>'
    html += '<p><strong>Key columns:</strong> <code>query</code> = your phage contig, <code>subject</code> = known phage match, <code>pident</code> = % identity, <code>evalue</code> = significance</p>'

    # Check if metadata was loaded
    if data.get('prophage_metadata'):
        html += '<p><span class="badge badge-success">✓ Enhanced with Prophage Metadata</span> Shows host organism, environment, and quality metrics for matched prophages.</p>'
    else:
        html += '<p><span class="badge badge-info">ℹ️ Basic View</span> Metadata enrichment available with --prophage-metadata parameter.</p>'

    if data['diamond']:
        for sample, diamond_list in sorted(data['diamond'].items()):
            count = len(diamond_list)
            has_amr = len(data['amr'].get(sample, [])) > 0
            highlight = ' class="highlight-both"' if (count > 0 and has_amr) else ''

            # Count how many have metadata
            with_metadata = sum(1 for hit in diamond_list if hit.get('meta_matched') == 'Yes')

            html += f'<div{highlight}><h3>{sample} <span class="badge badge-success">{count} matches</span>'
            if has_amr:
                html += ' <span class="badge badge-warning">Has AMR</span>'
            if with_metadata > 0:
                html += f' <span class="badge badge-info">{with_metadata} with metadata</span>'
            html += '</h3>'
            html += table_html(diamond_list, max_rows=100) if count > 0 else '<p><em>No phage matches found</em></p>'
            html += '</div>'
    else:
        html += '<p><em>No DIAMOND results available. DIAMOND compares detected phages against a prophage database to identify which known phages they match.</em></p>'

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
<li><strong>Phage Detection (VIBRANT):</strong> Identifies which contigs contain phage sequences</li>
<li><strong>Phage Identification (DIAMOND):</strong> Matches detected phages to known phage databases</li>
<li><strong>Metadata Enrichment:</strong> Shows host taxonomy, environment, and quality metrics for matched prophages (when metadata file provided)</li>
<li>All data embedded - no external files needed</li>
</ul>
<p><strong>Understanding Phage Results:</strong></p>
<ul>
<li><code>scaffold</code> in VIBRANT = the contig/region containing the phage</li>
<li><code>subject</code> in DIAMOND = the name of the known phage it matches (like a phage species)</li>
<li>Compare scaffold names between AMR and phage sections to see if AMR genes are on phage contigs</li>
<li>When metadata is available, DIAMOND results include:
  <ul>
    <li><code>meta_host_genus</code> and <code>meta_host_species</code>: The bacterial host this prophage came from</li>
    <li><code>meta_environment</code>: Where the original prophage was isolated (e.g., "human gut", "marine", "soil")</li>
    <li><code>meta_quality</code>: CheckV quality assessment (High-quality, Medium-quality, Low-quality)</li>
    <li><code>meta_completeness</code>: Estimated genome completeness percentage</li>
  </ul>
</li>
</ul>
<p><strong>Metadata Source:</strong></p>
<p>Prophage metadata from <a href="https://datadryad.org/dataset/doi:10.5061/dryad.3n5tb2rs5" target="_blank">Prophage-DB</a>
   (356,776 prophage sequences from bacterial and archaeal genomes).</p>
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
    parser.add_argument('--prophage-metadata', help='Path to prophage metadata.xlsx file (optional)')
    args = parser.parse_args()

    print(f"🔍 Scanning: {args.results_dir}")
    data = collect_all_results(args.results_dir, prophage_metadata=args.prophage_metadata)

    metadata_status = "with metadata" if data.get('prophage_metadata') else "without metadata"
    print(f"📊 Found: {len(data['amr'])} AMR, {len(data['phage'])} Phage, {len(data['diamond'])} Phage IDs, {len(data['mlst'])} MLST ({metadata_status})")

    output = generate_html(data, args.results_dir, args.output)
    size = os.path.getsize(output) / 1024
    print(f"✅ Generated: {output} ({size:.1f} KB)")

if __name__ == '__main__':
    main()
