#!/usr/bin/env python3
"""
COMPASS Pipeline Comprehensive Summary Report Generator (Enhanced Version)
Aggregates results from all pipeline modules into comprehensive summary with visualizations
"""

import argparse
import pandas as pd
import json
from pathlib import Path
import sys
from collections import Counter
import re

def parse_args():
    parser = argparse.ArgumentParser(description='Generate comprehensive COMPASS summary report with visualizations')
    parser.add_argument('--outdir', required=True, help='Pipeline output directory')
    parser.add_argument('--metadata', help='Optional metadata CSV with organism/source info')
    parser.add_argument('--output_tsv', default='compass_summary.tsv', help='Output TSV summary file')
    parser.add_argument('--output_html', default='compass_summary.html', help='Output HTML report')
    return parser.parse_args()

def parse_metadata(metadata_file):
    """Parse metadata CSV if provided"""
    metadata = {}
    if metadata_file and Path(metadata_file).exists():
        try:
            df = pd.read_csv(metadata_file)
            for _, row in df.iterrows():
                sample_id = row.get('Run', row.get('sample_id', row.get('sample', '')))
                metadata[sample_id] = {
                    'organism': row.get('Organism', row.get('organism', '-')),
                    'state': row.get('geo_loc_name_state_province', row.get('state', '-')),
                    'year': row.get('Collection_Date', row.get('year', '-')),
                    'source': row.get('Isolation_source', row.get('source', '-'))
                }
        except Exception as e:
            print(f"Warning: Could not parse metadata file: {e}", file=sys.stderr)
    return metadata

def parse_quast(quast_dir):
    """Parse QUAST assembly statistics"""
    quast_data = {}
    quast_path = Path(quast_dir)
    if quast_path.exists():
        for report_file in quast_path.glob('*/report.tsv'):
            try:
                df = pd.read_csv(report_file, sep='\t', index_col=0)
                sample_id = df.columns[0]

                # Extract key metrics
                total_length = df.loc['Total length', sample_id] if 'Total length' in df.index else 0
                n50 = df.loc['N50', sample_id] if 'N50' in df.index else 0
                num_contigs = df.loc['# contigs', sample_id] if '# contigs' in df.index else 0

                # Determine assembly quality status based on thresholds
                quality_pass = True
                quality_issues = []

                if isinstance(num_contigs, (int, float)) and num_contigs > 500:
                    quality_pass = False
                    quality_issues.append(f"high_contigs({num_contigs})")

                if isinstance(total_length, (int, float)) and total_length < 1000000:
                    quality_pass = False
                    quality_issues.append(f"small_assembly({total_length})")

                if isinstance(n50, (int, float)) and n50 < 10000:
                    quality_pass = False
                    quality_issues.append(f"low_N50({n50})")

                quast_data[sample_id] = {
                    'num_contigs': num_contigs,
                    'assembly_length': total_length,
                    'n50': n50,
                    'gc_percent': df.loc['GC (%)', sample_id] if 'GC (%)' in df.index else '-',
                    'assembly_quality': 'Pass' if quality_pass else f"Fail: {', '.join(quality_issues)}"
                }
            except Exception as e:
                print(f"Warning: Could not parse QUAST results for {report_file}: {e}", file=sys.stderr)
    return quast_data

def parse_busco(busco_dir):
    """Parse BUSCO completeness and contamination metrics"""
    busco_data = {}
    busco_path = Path(busco_dir)
    if busco_path.exists():
        for summary_file in busco_path.glob('*/short_summary.*.txt'):
            sample_id = summary_file.parent.name.replace('_busco', '')
            try:
                with open(summary_file) as f:
                    content = f.read()

                    # Parse BUSCO percentages from summary line
                    # Format: C:98.5%[S:97.0%,D:1.5%],F:0.5%,M:1.0%,n:124
                    match = re.search(r'C:([0-9.]+)%\[S:([0-9.]+)%,D:([0-9.]+)%\],F:([0-9.]+)%,M:([0-9.]+)%', content)

                    if match:
                        complete_pct = float(match.group(1))
                        single_pct = float(match.group(2))
                        duplicated_pct = float(match.group(3))
                        fragmented_pct = float(match.group(4))
                        missing_pct = float(match.group(5))

                        busco_data[sample_id] = {
                            'busco_complete_pct': complete_pct,
                            'busco_duplicated_pct': duplicated_pct,
                            'busco_fragmented_pct': fragmented_pct,
                            'busco_missing_pct': missing_pct,
                            'busco_summary': f"C:{complete_pct}%[S:{single_pct}%,D:{duplicated_pct}%],F:{fragmented_pct}%,M:{missing_pct}%"
                        }
            except Exception as e:
                print(f"Warning: Could not parse BUSCO results for {summary_file}: {e}", file=sys.stderr)
    return busco_data

def parse_mlst(mlst_dir):
    """Parse MLST sequence typing results"""
    mlst_data = {}
    mlst_path = Path(mlst_dir)
    if mlst_path.exists():
        for mlst_file in mlst_path.glob('*_mlst.tsv'):
            sample_id = mlst_file.stem.replace('_mlst', '')
            try:
                df = pd.read_csv(mlst_file, sep='\t')
                if not df.empty:
                    # MLST format: FILE SCHEME ST gene1 gene2 ...
                    mlst_data[sample_id] = {
                        'mlst_scheme': str(df.iloc[0]['SCHEME']) if 'SCHEME' in df.columns else '-',
                        'mlst_st': str(df.iloc[0]['ST']) if 'ST' in df.columns else '-'
                    }
            except Exception as e:
                print(f"Warning: Could not parse MLST results for {mlst_file}: {e}", file=sys.stderr)
    return mlst_data

def parse_sistr(sistr_dir):
    """Parse SISTR Salmonella serovar predictions"""
    sistr_data = {}
    sistr_path = Path(sistr_dir)
    if sistr_path.exists():
        for sistr_file in sistr_path.glob('*_sistr.tsv'):
            sample_id = sistr_file.stem.replace('_sistr', '')
            try:
                df = pd.read_csv(sistr_file, sep='\t')
                if not df.empty:
                    sistr_data[sample_id] = {
                        'serovar': df.iloc[0].get('serovar', '-'),
                        'serogroup': df.iloc[0].get('serogroup', '-'),
                        'h1': df.iloc[0].get('h1', '-'),
                        'h2': df.iloc[0].get('h2', '-')
                    }
            except Exception as e:
                print(f"Warning: Could not parse SISTR results for {sistr_file}: {e}", file=sys.stderr)
    return sistr_data

def parse_amrfinder(amr_dir):
    """Parse AMRFinder+ AMR gene and point mutation results"""
    amr_data = {}
    amr_path = Path(amr_dir)
    if amr_path.exists():
        for amr_file in amr_path.glob('*_amr.tsv'):
            sample_id = amr_file.stem.replace('_amr', '')
            try:
                df = pd.read_csv(amr_file, sep='\t')

                if df.empty:
                    amr_data[sample_id] = {
                        'num_amr_genes': 0,
                        'num_point_mutations': 0,
                        'amr_classes': '-',
                        'mdr_status': 'No',
                        'top_amr_genes': '-'
                    }
                else:
                    # Count genes vs point mutations
                    genes = df[df['Element type'] == 'AMR'] if 'Element type' in df.columns else df
                    mutations = df[df['Element type'] == 'POINT'] if 'Element type' in df.columns else pd.DataFrame()

                    # Get AMR classes
                    classes = []
                    if 'Class' in df.columns:
                        classes = [c for c in df['Class'].dropna().unique() if str(c) != 'nan']

                    # Determine MDR status (≥3 classes)
                    mdr_status = 'Yes' if len(classes) >= 3 else 'No'

                    # Get top genes
                    top_genes = []
                    if 'Gene symbol' in df.columns:
                        gene_counts = Counter(df['Gene symbol'].dropna())
                        top_genes = [gene for gene, count in gene_counts.most_common(5)]

                    amr_data[sample_id] = {
                        'num_amr_genes': len(genes),
                        'num_point_mutations': len(mutations),
                        'amr_classes': ', '.join(sorted(classes)) if classes else '-',
                        'mdr_status': mdr_status,
                        'top_amr_genes': ', '.join(top_genes) if top_genes else '-'
                    }
            except Exception as e:
                print(f"Warning: Could not parse AMRFinder results for {amr_file}: {e}", file=sys.stderr)
    return amr_data

def parse_mobsuite(mobsuite_dir):
    """Parse MOB-suite plasmid detection and typing results"""
    mobsuite_data = {}
    mobsuite_path = Path(mobsuite_dir)
    if mobsuite_path.exists():
        for result_file in mobsuite_path.glob('*/mobtyper_results.txt'):
            sample_id = result_file.parent.name.replace('_mobsuite', '')
            try:
                df = pd.read_csv(result_file, sep='\t')

                if df.empty:
                    mobsuite_data[sample_id] = {
                        'num_plasmids': 0,
                        'inc_groups': '-',
                        'mob_types': '-'
                    }
                else:
                    # Count plasmids
                    num_plasmids = len(df)

                    # Get incompatibility groups
                    inc_groups = []
                    if 'rep_type(s)' in df.columns:
                        for reps in df['rep_type(s)'].dropna():
                            if str(reps) != 'nan' and str(reps) != '-':
                                inc_groups.extend(str(reps).split(','))

                    # Get MOB types
                    mob_types = []
                    if 'predicted_mobility' in df.columns:
                        mob_types = df['predicted_mobility'].dropna().unique().tolist()

                    mobsuite_data[sample_id] = {
                        'num_plasmids': num_plasmids,
                        'inc_groups': ', '.join(sorted(set(inc_groups))) if inc_groups else '-',
                        'mob_types': ', '.join(sorted(set(str(m) for m in mob_types))) if mob_types else '-'
                    }
            except Exception as e:
                print(f"Warning: Could not parse MOBsuite results for {result_file}: {e}", file=sys.stderr)
    return mobsuite_data

def parse_vibrant(vibrant_dir):
    """Parse VIBRANT prophage detection results"""
    vibrant_data = {}
    vibrant_path = Path(vibrant_dir)
    if vibrant_path.exists():
        # VIBRANT creates nested structure: sample_vibrant/VIBRANT_sample_contigs/VIBRANT_results_sample_contigs/VIBRANT_results_sample_contigs.tsv
        for results_file in vibrant_path.glob('*/VIBRANT_*/VIBRANT_results_*/VIBRANT_results_*.tsv'):
            # Extract sample_id from directory name (e.g., SRR001_vibrant -> SRR001)
            sample_id = results_file.parents[2].name.replace('_vibrant', '')
            try:
                df = pd.read_csv(results_file, sep='\t')

                if df.empty:
                    vibrant_data[sample_id] = {
                        'num_prophages': 0,
                        'num_lytic': 0,
                        'num_lysogenic': 0
                    }
                else:
                    # Count prophages
                    num_prophages = len(df)

                    # Count lytic vs lysogenic
                    num_lytic = 0
                    num_lysogenic = 0
                    if 'type' in df.columns:
                        num_lytic = len(df[df['type'] == 'lytic'])
                        num_lysogenic = len(df[df['type'] == 'lysogenic'])

                    vibrant_data[sample_id] = {
                        'num_prophages': num_prophages,
                        'num_lytic': num_lytic,
                        'num_lysogenic': num_lysogenic
                    }
            except Exception as e:
                print(f"Warning: Could not parse VIBRANT results for {results_file}: {e}", file=sys.stderr)
    return vibrant_data

def parse_vibrant_annotations(vibrant_dir):
    """Parse VIBRANT annotation files to extract prophage functional categories"""
    functional_data = Counter()
    hypothetical_count = 0
    vibrant_path = Path(vibrant_dir)

    if vibrant_path.exists():
        # Look for annotation files - VIBRANT creates nested structure
        for annot_file in vibrant_path.glob('*_vibrant/VIBRANT_*/VIBRANT_annotations_*.tsv'):
            try:
                df = pd.read_csv(annot_file, sep='\t')

                # VIBRANT uses multi-column format: columns 4 (KO), 9 (Pfam), 14 (VOG)
                # Based on working v1.2-stable code
                for idx, row in df.iterrows():
                    # Extract annotation from multiple columns
                    ko_name = str(row.iloc[4]) if len(row) > 4 else ""
                    pfam_name = str(row.iloc[9]) if len(row) > 9 else ""
                    vog_name = str(row.iloc[14]) if len(row) > 14 else ""

                    combined = f"{ko_name} {pfam_name} {vog_name}".lower()

                    # Skip hypothetical/unknown proteins
                    if any(kw in combined for kw in ['hypothetical', 'duf', 'unknown function', 'uncharacterized', 'nan']):
                        hypothetical_count += 1
                        continue

                    # Categorize using combined annotation (from v1.2-stable logic)
                    categorized = False

                    # DNA Packaging
                    if any(term in combined for term in ['terminase', 'portal', 'packaging protein', 'dna-packaging']):
                        functional_data['DNA Packaging'] += 1
                        categorized = True
                    # Structural
                    elif any(term in combined for term in ['capsid', 'head', 'coat protein', 'tail', 'baseplate', 'fiber']):
                        functional_data['Structural'] += 1
                        categorized = True
                    # Lysis
                    elif any(term in combined for term in ['lyso', 'lysis', 'holin', 'spanin', 'endopeptidase', 'lysin', 'endolysin']):
                        functional_data['Lysis'] += 1
                        categorized = True
                    # DNA Modification
                    elif any(term in combined for term in ['integrase', 'recombinase', 'transposase', 'excisionase', 'replication', 'primase', 'helicase', 'polymerase', 'ligase', 'endonuclease', 'exonuclease', 'nuclease', 'methylase', 'methyltransferase']):
                        functional_data['DNA Modification'] += 1
                        categorized = True
                    # Regulation
                    elif any(term in combined for term in ['repressor', 'regulator', 'antitermination', 'antirepressor', 'anti-repressor']):
                        functional_data['Regulation'] += 1
                        categorized = True

                    # If not categorized and not hypothetical, mark as "Other"
                    if not categorized:
                        functional_data['Other'] += 1

            except Exception as e:
                print(f"Warning: Could not parse VIBRANT annotations for {annot_file}: {e}", file=sys.stderr)

    return dict(functional_data)

def parse_diamond_prophage(diamond_dir):
    """Parse DIAMOND prophage database matches"""
    diamond_data = {}
    diamond_path = Path(diamond_dir)
    if diamond_path.exists():
        for diamond_file in diamond_path.glob('*_diamond_results.tsv'):
            sample_id = diamond_file.stem.replace('_diamond_results', '')
            try:
                # DIAMOND format: qseqid sseqid pident length mismatch gapopen qstart qend sstart send evalue bitscore
                df = pd.read_csv(diamond_file, sep='\t', header=None,
                                names=['qseqid', 'sseqid', 'pident', 'length', 'mismatch',
                                       'gapopen', 'qstart', 'qend', 'sstart', 'send', 'evalue', 'bitscore'])

                if df.empty:
                    diamond_data[sample_id] = {
                        'num_prophage_hits': 0,
                        'top_prophage_matches': '-'
                    }
                else:
                    # Count unique prophage hits
                    num_hits = df['qseqid'].nunique()

                    # Get top 3 matches by identity
                    top_matches = []
                    if not df.empty:
                        df_sorted = df.sort_values('pident', ascending=False).head(3)
                        for _, row in df_sorted.iterrows():
                            match_str = f"{row['sseqid']}({row['pident']:.1f}%)"
                            top_matches.append(match_str)

                    diamond_data[sample_id] = {
                        'num_prophage_hits': num_hits,
                        'top_prophage_matches': ', '.join(top_matches) if top_matches else '-'
                    }
            except Exception as e:
                print(f"Warning: Could not parse DIAMOND results for {diamond_file}: {e}", file=sys.stderr)
    return diamond_data

def generate_html_report(df, output_file, functional_diversity=None):
    """Generate interactive multi-tab HTML report with visualizations"""

    # Calculate summary statistics
    total_samples = len(df)
    passed_qc = len(df[df['assembly_quality'] == 'Pass'])
    failed_qc = total_samples - passed_qc

    avg_contigs = df['num_contigs'].replace('-', 0).astype(float).mean()
    avg_n50 = df['n50'].replace('-', 0).astype(float).mean()

    mdr_samples = len(df[df['mdr_status'] == 'Yes'])
    mdr_pct = (mdr_samples / total_samples * 100) if total_samples > 0 else 0

    total_prophages = df['num_prophages'].sum()
    avg_prophages = total_prophages / total_samples if total_samples > 0 else 0

    # AMR statistics
    total_amr_genes = df['num_amr_genes'].sum()
    samples_with_amr = len(df[df['num_amr_genes'] > 0])

    # Plasmid statistics
    total_plasmids = df['num_plasmids'].sum()
    samples_with_plasmids = len(df[df['num_plasmids'] > 0])

    # Prepare functional diversity data for chart
    functional_labels = []
    functional_values = []
    if functional_diversity:
        for category, count in functional_diversity.items():
            functional_labels.append(category)
            functional_values.append(count)

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>COMPASS Pipeline Summary Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        }}

        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}

        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}

        .tabs {{
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }}

        .tab-buttons {{
            display: flex;
            overflow-x: auto;
            border-bottom: 2px solid #e0e0e0;
        }}

        .tab-button {{
            padding: 15px 25px;
            border: none;
            background: none;
            cursor: pointer;
            font-size: 1em;
            font-weight: 500;
            color: #666;
            white-space: nowrap;
            transition: all 0.3s ease;
            border-bottom: 3px solid transparent;
        }}

        .tab-button:hover {{
            color: #667eea;
            background: #f8f9ff;
        }}

        .tab-button.active {{
            color: #667eea;
            border-bottom-color: #667eea;
            background: #f8f9ff;
        }}

        .tab-content {{
            display: none;
            padding: 30px;
            animation: fadeIn 0.3s ease-in;
        }}

        .tab-content.active {{
            display: block;
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .summary-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }}

        .summary-card .subtext {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}

        .chart-container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}

        .chart-container h2 {{
            margin: 0 0 20px 0;
            color: #333;
        }}

        .chart-wrapper {{
            position: relative;
            height: 400px;
        }}

        .table-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow-x: auto;
        }}

        .search-box {{
            margin-bottom: 20px;
            padding: 12px;
            width: 100%;
            max-width: 400px;
            border: 2px solid #667eea;
            border-radius: 6px;
            font-size: 1em;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }}

        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            cursor: pointer;
            user-select: none;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        th:hover {{
            background: #5568d3;
        }}

        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
        }}

        tr:hover {{
            background-color: #f8f9ff;
        }}

        .status-pass {{
            color: #22c55e;
            font-weight: 600;
        }}

        .status-fail {{
            color: #ef4444;
            font-weight: 600;
        }}

        .mdr-yes {{
            background: #fee2e2;
            color: #991b1b;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧬 COMPASS Pipeline Summary Report</h1>
        <p>Comprehensive Overview of AMR, Phage, and Assembly Quality Metrics</p>
    </div>

    <div class="tabs">
        <div class="tab-buttons">
            <button class="tab-button active" onclick="switchTab(event, 'overview')">Overview</button>
            <button class="tab-button" onclick="switchTab(event, 'data-table')">Data Table</button>
            <button class="tab-button" onclick="switchTab(event, 'prophage-functional')">Prophage Functional Diversity</button>
        </div>
    </div>

    <!-- Overview Tab -->
    <div id="overview" class="tab-content active">
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Total Samples</h3>
                <div class="value">{total_samples}</div>
            </div>
            <div class="summary-card">
                <h3>Assembly QC</h3>
                <div class="value">{passed_qc}</div>
                <div class="subtext">Passed ({failed_qc} failed)</div>
            </div>
            <div class="summary-card">
                <h3>Average Assembly</h3>
                <div class="value">{avg_contigs:.0f}</div>
                <div class="subtext">Contigs (N50: {avg_n50:.0f})</div>
            </div>
            <div class="summary-card">
                <h3>MDR Samples</h3>
                <div class="value">{mdr_samples}</div>
                <div class="subtext">{mdr_pct:.1f}% of samples</div>
            </div>
            <div class="summary-card">
                <h3>Total Prophages</h3>
                <div class="value">{total_prophages}</div>
                <div class="subtext">Avg: {avg_prophages:.1f} per sample</div>
            </div>
            <div class="summary-card">
                <h3>AMR Genes</h3>
                <div class="value">{total_amr_genes}</div>
                <div class="subtext">{samples_with_amr} samples with AMR</div>
            </div>
            <div class="summary-card">
                <h3>Plasmids</h3>
                <div class="value">{total_plasmids}</div>
                <div class="subtext">{samples_with_plasmids} samples with plasmids</div>
            </div>
        </div>
    </div>

    <!-- Data Table Tab -->
    <div id="data-table" class="tab-content">
        <div class="table-container">
            <h2>Sample Details</h2>
            <input type="text" class="search-box" id="searchBox" placeholder="Search samples..." onkeyup="filterTable()">

            <table id="dataTable">
                <thead>
                    <tr>
"""

    # Add table headers
    for col in df.columns:
        html += f"                        <th onclick=\"sortTable('{col}')\">{col}</th>\n"

    html += """                    </tr>
                </thead>
                <tbody>
"""

    # Add table rows
    for _, row in df.iterrows():
        html += "                    <tr>\n"
        for col in df.columns:
            value = row[col]

            # Apply special formatting
            if col == 'assembly_quality':
                css_class = 'status-pass' if value == 'Pass' else 'status-fail'
                html += f"                        <td class='{css_class}'>{value}</td>\n"
            elif col == 'mdr_status' and value == 'Yes':
                html += f"                        <td><span class='mdr-yes'>{value}</span></td>\n"
            else:
                html += f"                        <td>{value}</td>\n"

        html += "                    </tr>\n"

    html += """                </tbody>
            </table>
        </div>
    </div>

    <!-- Prophage Functional Diversity Tab -->
    <div id="prophage-functional" class="tab-content">
        <div class="chart-container">
            <h2>Prophage Functional Diversity</h2>
            <p style="color: #666; margin-bottom: 20px;">Distribution of prophage gene functions across all samples</p>
            <div class="chart-wrapper">
                <canvas id="functionalPieChart"></canvas>
            </div>
        </div>
    </div>

    <script>
        // Tab switching
        function switchTab(evt, tabName) {
            const tabContents = document.getElementsByClassName('tab-content');
            for (let i = 0; i < tabContents.length; i++) {
                tabContents[i].classList.remove('active');
            }

            const tabButtons = document.getElementsByClassName('tab-button');
            for (let i = 0; i < tabButtons.length; i++) {
                tabButtons[i].classList.remove('active');
            }

            document.getElementById(tabName).classList.add('active');
            evt.currentTarget.classList.add('active');
        }

        // Table sorting
        function sortTable(column) {
            const table = document.getElementById('dataTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const headerRow = table.querySelector('thead tr');
            const headers = Array.from(headerRow.querySelectorAll('th'));
            const colIndex = headers.findIndex(h => h.textContent === column);

            const currentSort = table.dataset.sortColumn;
            const currentDir = table.dataset.sortDir || 'asc';
            const newDir = (currentSort === column && currentDir === 'asc') ? 'desc' : 'asc';

            rows.sort((a, b) => {
                const aVal = a.cells[colIndex].textContent.trim();
                const bVal = b.cells[colIndex].textContent.trim();

                const aNum = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
                const bNum = parseFloat(bVal.replace(/[^0-9.-]/g, ''));

                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return newDir === 'asc' ? aNum - bNum : bNum - aNum;
                }

                return newDir === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            });

            rows.forEach(row => tbody.appendChild(row));

            table.dataset.sortColumn = column;
            table.dataset.sortDir = newDir;
        }

        // Table filtering
        function filterTable() {
            const input = document.getElementById('searchBox');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('dataTable');
            const rows = table.querySelectorAll('tbody tr');

            rows.forEach(row => {
                const text = row.textContent.toUpperCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            });
        }

        // Prophage Functional Diversity Pie Chart
        const functionalLabels = {json.dumps(functional_labels)};
        const functionalData = {json.dumps(functional_values)};

        const functionalCtx = document.getElementById('functionalPieChart').getContext('2d');
        const functionalPieChart = new Chart(functionalCtx, {{
            type: 'pie',
            data: {{
                labels: functionalLabels,
                datasets: [{{
                    data: functionalData,
                    backgroundColor: [
                        '#FF6384',  // DNA Packaging
                        '#36A2EB',  // Structural
                        '#FFCE56',  // Lysis
                        '#4BC0C0',  // Regulation
                        '#9966FF',  // DNA Modification
                        '#C9CBCF'   // Other
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{
                            font: {{
                                size: 14
                            }},
                            padding: 15
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return label + ': ' + value + ' (' + percentage + '%)';
                            }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    # Write HTML file
    with open(output_file, 'w') as f:
        f.write(html)

def main():
    args = parse_args()
    outdir = Path(args.outdir)

    print(f"Generating comprehensive COMPASS summary from {outdir}")

    # Parse optional metadata
    metadata = parse_metadata(args.metadata)

    # Parse all result files
    print("Parsing QUAST assembly statistics...")
    quast_data = parse_quast(outdir / 'quast')

    print("Parsing BUSCO completeness metrics...")
    busco_data = parse_busco(outdir / 'busco')

    print("Parsing MLST typing results...")
    mlst_data = parse_mlst(outdir / 'mlst')

    print("Parsing SISTR serovar predictions...")
    sistr_data = parse_sistr(outdir / 'sistr')

    print("Parsing AMRFinder results...")
    amr_data = parse_amrfinder(outdir / 'amrfinder')

    print("Parsing MOB-suite plasmid results...")
    mobsuite_data = parse_mobsuite(outdir / 'mobsuite')

    print("Parsing VIBRANT prophage results...")
    vibrant_data = parse_vibrant(outdir / 'vibrant')

    print("Parsing VIBRANT functional annotations...")
    functional_diversity = parse_vibrant_annotations(outdir / 'vibrant')
    if functional_diversity:
        print(f"  Found {sum(functional_diversity.values())} categorized prophage genes")
        for category, count in functional_diversity.items():
            print(f"    {category}: {count}")

    print("Parsing DIAMOND prophage matches...")
    diamond_data = parse_diamond_prophage(outdir / 'diamond_prophage')

    # Combine all data
    all_samples = set()
    for data_dict in [quast_data, busco_data, mlst_data, sistr_data, amr_data,
                     mobsuite_data, vibrant_data, diamond_data, metadata]:
        all_samples.update(data_dict.keys())

    print(f"Found {len(all_samples)} total samples")

    # Build comprehensive summary table
    summary_data = []
    for sample in sorted(all_samples):
        row = {'sample_id': sample}

        # Sample metadata (if available)
        if sample in metadata:
            row['organism'] = metadata[sample].get('organism', '-')
            row['state'] = metadata[sample].get('state', '-')
            row['year'] = metadata[sample].get('year', '-')
            row['source'] = metadata[sample].get('source', '-')

        # Assembly quality metrics
        if sample in quast_data:
            row.update(quast_data[sample])
        else:
            row.update({
                'num_contigs': '-',
                'assembly_length': '-',
                'n50': '-',
                'gc_percent': '-',
                'assembly_quality': 'No data'
            })

        # BUSCO completeness/contamination
        if sample in busco_data:
            row.update(busco_data[sample])
        else:
            row.update({
                'busco_complete_pct': '-',
                'busco_duplicated_pct': '-',
                'busco_summary': '-'
            })

        # Strain typing
        if sample in mlst_data:
            row.update(mlst_data[sample])
        else:
            row.update({'mlst_scheme': '-', 'mlst_st': '-'})

        if sample in sistr_data:
            row['serovar'] = sistr_data[sample]['serovar']
        else:
            row['serovar'] = '-'

        # AMR summary
        if sample in amr_data:
            row.update(amr_data[sample])
        else:
            row.update({
                'num_amr_genes': 0,
                'num_point_mutations': 0,
                'amr_classes': '-',
                'mdr_status': 'No',
                'top_amr_genes': '-'
            })

        # Mobile elements
        if sample in mobsuite_data:
            row.update(mobsuite_data[sample])
        else:
            row.update({
                'num_plasmids': 0,
                'inc_groups': '-',
                'mob_types': '-'
            })

        # Phage summary
        if sample in vibrant_data:
            row.update(vibrant_data[sample])
        else:
            row.update({
                'num_prophages': 0,
                'num_lytic': 0,
                'num_lysogenic': 0
            })

        if sample in diamond_data:
            row.update(diamond_data[sample])
        else:
            row.update({
                'num_prophage_hits': 0,
                'top_prophage_matches': '-'
            })

        summary_data.append(row)

    # Create DataFrame
    df = pd.DataFrame(summary_data)

    # Reorder columns for better readability
    column_order = ['sample_id']
    if 'organism' in df.columns:
        column_order.extend(['organism', 'state', 'year', 'source'])

    column_order.extend([
        # Assembly metrics
        'num_contigs', 'assembly_length', 'n50', 'assembly_quality',
        # BUSCO
        'busco_complete_pct', 'busco_duplicated_pct', 'busco_summary',
        # Typing
        'mlst_st', 'mlst_scheme', 'serovar',
        # AMR
        'num_amr_genes', 'num_point_mutations', 'amr_classes', 'mdr_status', 'top_amr_genes',
        # Plasmids
        'num_plasmids', 'inc_groups', 'mob_types',
        # Phages
        'num_prophages', 'num_lytic', 'num_lysogenic', 'num_prophage_hits', 'top_prophage_matches'
    ])

    # Only include columns that exist
    column_order = [col for col in column_order if col in df.columns]
    df = df[column_order]

    # Save TSV
    df.to_csv(args.output_tsv, sep='\t', index=False)
    print(f"✓ TSV summary written to {args.output_tsv}")

    # Generate HTML report with functional diversity data
    generate_html_report(df, args.output_html, functional_diversity=functional_diversity)
    print(f"✓ HTML report written to {args.output_html}")

    print(f"\n=== Summary Statistics ===")
    print(f"Total samples: {len(summary_data)}")
    print(f"Samples with assembly data: {len(quast_data)}")
    print(f"Samples with AMR genes: {len([s for s in summary_data if s.get('num_amr_genes', 0) > 0])}")
    print(f"Samples with prophages: {len([s for s in summary_data if s.get('num_prophages', 0) > 0])}")
    print(f"MDR samples: {len([s for s in summary_data if s.get('mdr_status') == 'Yes'])}")

if __name__ == '__main__':
    main()
